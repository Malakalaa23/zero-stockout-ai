"""
TFT-MPIR: End-to-End Multi-Period Inventory Replenishment
Decision Agent for Zero-Stockout system.

Loads the trained decision_model.pth neural network and uses it to
predict the optimal order quantity. Falls back to exhaustive cost
minimization if the model is unavailable.
"""

from typing import List, Dict, Tuple, Optional
import os
import pickle
import logging
import math
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)


class TFTMPIR_DecisionAgent:
    """
    Decision Agent implementing TFT-MPIR for optimal inventory replenishment.
    Loads the trained neural network from disk; falls back to brute-force
    cost minimization if unavailable.
    """

    def __init__(self, cost_params: Optional[Dict[str, float]] = None):
        self.holding_cost = cost_params.get('holding', 2.0) if cost_params else 2.0
        self.stockout_cost = cost_params.get('stockout', 100.0) if cost_params else 100.0
        self.shipping_base = cost_params.get('shipping_base', 50.0) if cost_params else 50.0
        self.shipping_per_unit = cost_params.get('shipping_per_unit', 5.0) if cost_params else 5.0

        # Model artifacts
        self.model = None
        self.scaler = None
        self.features = None

        self._load_model()

    # ============================================================
    # MODEL LOADING
    # ============================================================

    def _find_model_dir(self) -> Optional[str]:
        """Locate the folder containing decision_model.pth."""
        here = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(here, "..", "..", "models"),           # repo_root/models
            os.path.join(here, "..", "..", "..", "models"),
            os.path.join(here, "..", "models"),                 # backend/models
            "models",                                            # cwd/models
        ]
        for c in candidates:
            if os.path.exists(os.path.join(c, "decision_model.pth")):
                return os.path.abspath(c)
        return None

    def _load_model(self):
        try:
            model_dir = self._find_model_dir()
            if not model_dir:
                logger.info("No trained model directory found. Using cost-minimization fallback.")
                return

            model_path = os.path.join(model_dir, "decision_model.pth")
            scaler_path = os.path.join(model_dir, "decision_scaler.pkl")
            features_path = os.path.join(model_dir, "decision_features.pkl")

            if not all(os.path.exists(p) for p in [model_path, scaler_path, features_path]):
                logger.info("Some model artifacts missing. Using fallback.")
                return

            # Load feature list and scaler
            with open(features_path, "rb") as f:
                self.features = pickle.load(f)
            with open(scaler_path, "rb") as f:
                self.scaler = pickle.load(f)

            # Import and instantiate the model
            import torch
            from .tft_mpir_model import TFT_MPIR_Model

            self.model = TFT_MPIR_Model(input_dim=len(self.features))
            state = torch.load(model_path, map_location="cpu", weights_only=True)
            self.model.load_state_dict(state)
            self.model.eval()

            logger.info(f"✅ Loaded trained decision model ({len(self.features)} features, 61K params)")

        except Exception as e:
            logger.warning(f"Model loading failed: {e}. Using fallback.")
            self.model = None
            self.scaler = None
            self.features = None

    # ============================================================
    # FEATURE ENGINEERING
    # ============================================================

    def _build_features(
        self,
        demand_forecast: List[float],
        current_stock: int,
        days: int,
        unit_cost: float,
    ) -> Optional[List[float]]:
        """
        Build the 19-feature vector the model expects, in exact order:
        price, cost, stock, lead_time_days, sales_mean_7d, sales_mean_14d,
        sales_mean_30d, sales_std_7d, stock_ratio, day_sin, day_cos,
        month_sin, month_cos, is_weekend, price_change, demand_lag_1,
        demand_lag_3, demand_lag_7, lead_time_demand
        """
        if not self.features:
            return None

        # Safely extract forecast windows
        def _mean(window):
            vals = demand_forecast[:window]
            return float(np.mean(vals)) if vals else 0.0

        def _std(window):
            vals = demand_forecast[:window]
            return float(np.std(vals)) if vals else 0.0

        def _lag(n):
            return float(demand_forecast[n - 1]) if len(demand_forecast) >= n else 0.0

        today = datetime.now()
        day_of_year = today.timetuple().tm_yday
        month = today.month

        mean_7d = _mean(7)
        mean_14d = _mean(14)
        mean_30d = _mean(30) if len(demand_forecast) >= 30 else _mean(len(demand_forecast))
        std_7d = _std(7)
        stock_ratio = current_stock / (mean_7d + 1.0) if mean_7d > 0 else 0.0

        lead_time_days = 5.0  # default supplier lead time
        lead_time_demand = mean_7d * lead_time_days / 7.0

        feature_dict = {
            "price": float(unit_cost),
            "cost": float(unit_cost),
            "stock": float(current_stock),
            "lead_time_days": lead_time_days,
            "sales_mean_7d": mean_7d,
            "sales_mean_14d": mean_14d,
            "sales_mean_30d": mean_30d,
            "sales_std_7d": std_7d,
            "stock_ratio": stock_ratio,
            "day_sin": math.sin(2 * math.pi * day_of_year / 365.0),
            "day_cos": math.cos(2 * math.pi * day_of_year / 365.0),
            "month_sin": math.sin(2 * math.pi * month / 12.0),
            "month_cos": math.cos(2 * math.pi * month / 12.0),
            "is_weekend": 1.0 if today.weekday() >= 5 else 0.0,
            "price_change": 0.0,
            "demand_lag_1": _lag(1),
            "demand_lag_3": _lag(3),
            "demand_lag_7": _lag(7),
            "lead_time_demand": lead_time_demand,
        }

        # Build vector in the exact order the scaler/model expects
        return [feature_dict.get(f, 0.0) for f in self.features]

    # ============================================================
    # INFERENCE
    # ============================================================

    def _predict_with_model(
        self,
        demand_forecast: List[float],
        current_stock: int,
        days: int,
        unit_cost: float,
    ) -> Optional[int]:
        if self.model is None or self.scaler is None or self.features is None:
            return None

        try:
            import torch

            features = self._build_features(demand_forecast, current_stock, days, unit_cost)
            if features is None:
                return None

            # Scale features (fit during training)
            arr = np.array(features, dtype=np.float32).reshape(1, -1)
            arr_scaled = self.scaler.transform(arr)

            tensor = torch.FloatTensor(arr_scaled)

            with torch.no_grad():
                _, q50, _ = self.model(tensor)
                qty = float(q50.item())

            return max(0, int(round(qty)))

        except Exception as e:
            logger.error(f"Model prediction failed: {e}")
            return None

    # ============================================================
    # COST FUNCTION (FALLBACK)
    # ============================================================

    def compute_total_cost(
        self,
        order_qty: int,
        demand_forecast: List[float],
        current_stock: int,
        days: int,
    ) -> float:
        if not demand_forecast:
            raise ValueError("Demand forecast cannot be empty")
        if days <= 0:
            raise ValueError("Days must be positive")
        if order_qty < 0:
            raise ValueError("Order quantity cannot be negative")
        if current_stock < 0:
            raise ValueError("Current stock cannot be negative")

        expected_demand = sum(demand_forecast[:days])

        stockout_units = max(0, expected_demand - current_stock - order_qty)
        stockout_cost = stockout_units * self.stockout_cost

        avg_inventory = current_stock - expected_demand + (order_qty / 2)
        holding_cost = max(0, avg_inventory) * self.holding_cost * days

        shipping_cost = self.shipping_base + (order_qty * self.shipping_per_unit)

        return float(stockout_cost + holding_cost + shipping_cost)

    # ============================================================
    # OPTIMIZER
    # ============================================================

    def optimal_quantity(
        self,
        demand_forecast: List[float],
        current_stock: int,
        days: int,
        unit_cost: float = 10.0,
    ) -> Tuple[int, float, str]:
        """
        Returns (order_qty, total_cost, method_used).
        Tries the trained model first; falls back to exhaustive cost minimization.
        """
        if not demand_forecast:
            raise ValueError("Demand forecast cannot be empty")
        if days <= 0:
            raise ValueError("Days must be positive")
        if current_stock < 0:
            raise ValueError("Current stock cannot be negative")

        expected_demand = sum(demand_forecast[:days])

        # Early exit
        if current_stock >= expected_demand:
            return 0, self.compute_total_cost(0, demand_forecast, current_stock, days), "stock_sufficient"

        # Try the trained model
        if self.model is not None:
            qty = self._predict_with_model(demand_forecast, current_stock, days, unit_cost)
            if qty is not None:
                cost = self.compute_total_cost(qty, demand_forecast, current_stock, days)
                return qty, cost, "trained_model"

        # Fallback: exhaustive search
        best_q = 0
        best_cost = float('inf')
        max_q = int(expected_demand * 1.5)

        for q in range(max_q + 1):
            cost = self.compute_total_cost(q, demand_forecast, current_stock, days)
            if cost < best_cost:
                best_cost = cost
                best_q = q

        return best_q, best_cost, "cost_minimization"

    # ============================================================
    # RECOMMENDATION WRAPPER
    # ============================================================

    def recommend(
        self,
        demand_forecast: List[float],
        current_stock: int,
        days: int,
        unit_cost: float = 10.0,
    ) -> Dict[str, any]:
        qty, cost, method = self.optimal_quantity(demand_forecast, current_stock, days, unit_cost)

        expected_demand = sum(demand_forecast[:days])

        if qty == 0:
            rationale = f"Current stock ({current_stock}) is sufficient for demand ({expected_demand:.0f})"
        else:
            deficit = expected_demand - current_stock
            if method == "trained_model":
                rationale = f"TFT-MPIR model predicts order {qty} units to cover {deficit:.0f} unit deficit"
            else:
                rationale = f"Order {qty} units to cover {deficit:.0f} unit deficit"

        return {
            "order_quantity": qty,
            "total_cost": cost,
            "expected_demand": expected_demand,
            "current_stock": current_stock,
            "holding_cost": self.holding_cost,
            "stockout_cost": self.stockout_cost,
            "shipping_cost": self.shipping_base + (qty * self.shipping_per_unit),
            "rationale": rationale,
            "confidence": 0.95 if method == "trained_model" else 0.85,
            "method": method,
            "trained": method == "trained_model",
        }