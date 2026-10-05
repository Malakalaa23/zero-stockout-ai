"""
TFT-MPIR: End-to-End Multi-Period Inventory Replenishment
Decision Agent for Malak's Zero-Stockout system.

Two modes:
  1. Trained neural network (if model artifacts exist)
  2. Brute-force cost minimization (fallback)

Both compute the same thing: the order quantity that minimizes
total cost = stockout + holding + shipping.
"""

from typing import List, Dict, Tuple, Optional
import os
import logging
import numpy as np

logger = logging.getLogger(__name__)


class TFTMPIR_DecisionAgent:
    """
    Decision Agent implementing TFT-MPIR for optimal inventory replenishment.

    Given a demand forecast + current stock, outputs the cost-optimal order qty.
    """

    def __init__(self, cost_params: Optional[Dict[str, float]] = None):
        # Cost parameters are injected — each SKU can have its own
        self.holding_cost = cost_params.get('holding', 2.0) if cost_params else 2.0
        self.stockout_cost = cost_params.get('stockout', 100.0) if cost_params else 100.0
        self.shipping_base = cost_params.get('shipping_base', 50.0) if cost_params else 50.0
        self.shipping_per_unit = cost_params.get('shipping_per_unit', 5.0) if cost_params else 5.0

        # Model artifacts (populated by _load_model if files exist)
        self.model = None
        self.scaler = None
        self.features = None

        self._load_model()

    # ============================================================
    # MODEL LOADING
    # ============================================================

    def _load_model(self):
        """
        Try to load the trained neural network from disk.
        Silent fallback if any artifact is missing — never crash the API.
        """
        try:
            # Find the models directory — support multiple layouts
            here = os.path.dirname(os.path.abspath(__file__))
            candidates = [
                os.path.join(here, "..", "models", "router_model.pkl"),
                os.path.join(here, "..", "models", "decision_model.pth"),
                os.path.join(here, "..", "..", "backend", "models", "router_model.pkl"),
            ]

            model_path = None
            for c in candidates:
                if os.path.exists(c):
                    model_path = os.path.abspath(c)
                    break

            if not model_path:
                logger.info("No trained decision model found. Using cost-minimization fallback.")
                return

            # Try loading if it's the router_model.pkl (state_dict format)
            if model_path.endswith(".pkl"):
                try:
                    import torch
                    from .tft_mpir_model import TFT_MPIR_Model

                    # router_model.pkl is our 7-feature decision NN
                    self.model = TFT_MPIR_Model(input_dim=7)
                    state = torch.load(model_path, map_location="cpu")

                    # Support both raw state_dict and wrapped checkpoint
                    if isinstance(state, dict) and "state_dict" in state:
                        state = state["state_dict"]
                    self.model.load_state_dict(state)
                    self.model.eval()
                    logger.info(f"✅ Loaded trained decision model from {model_path}")
                except Exception as e:
                    logger.warning(f"Failed to load neural model: {e}. Using fallback.")
                    self.model = None

        except Exception as e:
            logger.warning(f"Model loading error: {e}. Using fallback.")
            self.model = None

    # ============================================================
    # INFERENCE
    # ============================================================

    def _predict_with_model(self, features: List[float]) -> Optional[int]:
        """Use the trained model to predict optimal order quantity."""
        if self.model is None:
            return None

        try:
            import torch
            features_array = np.array(features, dtype=np.float32).reshape(1, -1)
            features_tensor = torch.FloatTensor(features_array)

            with torch.no_grad():
                prediction = self.model(features_tensor).item()

            return max(0, int(round(prediction)))

        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return None

    # ============================================================
    # COST FUNCTION (HEART OF THE MODEL)
    # ============================================================

    def compute_total_cost(
        self,
        order_qty: int,
        demand_forecast: List[float],
        current_stock: int,
        days: int,
    ) -> float:
        """
        Total cost = stockout + holding + shipping for a given order quantity.
        """
        if not demand_forecast:
            raise ValueError("Demand forecast cannot be empty")
        if days <= 0:
            raise ValueError("Days must be positive")
        if order_qty < 0:
            raise ValueError("Order quantity cannot be negative")
        if current_stock < 0:
            raise ValueError("Current stock cannot be negative")

        expected_demand = sum(demand_forecast[:days])

        # Stockout: units we couldn't fulfill × penalty
        stockout_units = max(0, expected_demand - current_stock - order_qty)
        stockout_cost = stockout_units * self.stockout_cost

        # Holding: average inventory × per-unit-per-day × days
        avg_inventory = current_stock - expected_demand + (order_qty / 2)
        holding_cost = max(0, avg_inventory) * self.holding_cost * days

        # Shipping: fixed base + per-unit variable
        shipping_cost = self.shipping_base + (order_qty * self.shipping_per_unit)

        return float(stockout_cost + holding_cost + shipping_cost)

    # ============================================================
    # OPTIMIZER (MODEL → FALLBACK)
    # ============================================================

    def optimal_quantity(
        self,
        demand_forecast: List[float],
        current_stock: int,
        days: int,
    ) -> Tuple[int, float]:
        """
        Find optimal order qty using trained model, or brute-force if unavailable.
        """
        if not demand_forecast:
            raise ValueError("Demand forecast cannot be empty")
        if days <= 0:
            raise ValueError("Days must be positive")
        if current_stock < 0:
            raise ValueError("Current stock cannot be negative")

        expected_demand = sum(demand_forecast[:days])

        # Early exit: stock covers demand, no order needed
        if current_stock >= expected_demand:
            return 0, self.compute_total_cost(0, demand_forecast, current_stock, days)

        # Try the trained model first
        if self.model is not None:
            try:
                # Build the 7-feature vector in the order the model expects
                avg_daily = sum(demand_forecast) / len(demand_forecast)
                features = [
                    float(current_stock),
                    float(expected_demand),
                    float(days),
                    float(self.holding_cost),
                    float(self.stockout_cost),
                    float(10.0),  # unit cost default
                    float(0.85),  # confidence default
                ]
                qty = self._predict_with_model(features)
                if qty is not None:
                    cost = self.compute_total_cost(qty, demand_forecast, current_stock, days)
                    return qty, cost
            except Exception as e:
                logger.warning(f"Model prediction failed, using fallback: {e}")

        # Fallback: brute-force search
        best_q = 0
        best_cost = float('inf')
        max_q = int(expected_demand * 1.5)

        for q in range(max_q + 1):
            cost = self.compute_total_cost(q, demand_forecast, current_stock, days)
            if cost < best_cost:
                best_cost = cost
                best_q = q

        return best_q, best_cost

    # ============================================================
    # VECTORIZED NEWSVENDOR (O(1) ALTERNATIVE)
    # ============================================================

    def optimal_quantity_vectorized(
        self,
        demand_forecast: List[float],
        current_stock: int,
        days: int,
    ) -> Tuple[int, float]:
        """Fast approximation using the classical Newsvendor formula."""
        if not demand_forecast:
            raise ValueError("Demand forecast cannot be empty")
        if days <= 0:
            raise ValueError("Days must be positive")
        if current_stock < 0:
            raise ValueError("Current stock cannot be negative")

        expected_demand = sum(demand_forecast[:days])

        if current_stock >= expected_demand:
            return 0, self.compute_total_cost(0, demand_forecast, current_stock, days)

        # Newsvendor critical ratio
        underage_cost = self.stockout_cost
        overage_cost = self.holding_cost * days
        critical_ratio = underage_cost / (underage_cost + overage_cost)

        cumsum = np.cumsum(demand_forecast[:days])
        qty = int(np.ceil(np.percentile(cumsum, critical_ratio * 100)))

        shipping_breakpoint = self.shipping_base / self.shipping_per_unit
        if qty < shipping_breakpoint:
            qty = int(shipping_breakpoint)

        qty = min(qty, int(expected_demand * 1.5))
        cost = self.compute_total_cost(qty, demand_forecast, current_stock, days)

        return int(qty), float(cost)

    # ============================================================
    # RECOMMENDATION WRAPPER (USER-FACING)
    # ============================================================

    def recommend(
        self,
        demand_forecast: List[float],
        current_stock: int,
        days: int,
        method: str = "auto",
    ) -> Dict[str, any]:
        """Complete recommendation with rationale and confidence."""
        if method == "auto":
            method = "trained_model" if self.model is not None else "brute_force"

        if method == "vectorized":
            qty, cost = self.optimal_quantity_vectorized(demand_forecast, current_stock, days)
        else:
            qty, cost = self.optimal_quantity(demand_forecast, current_stock, days)

        expected_demand = sum(demand_forecast[:days])

        if qty == 0:
            rationale = f"Current stock ({current_stock}) is sufficient for demand ({expected_demand:.0f})"
        else:
            deficit = expected_demand - current_stock
            if self.model is not None and method == "trained_model":
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
            "confidence": 0.95 if self.model is not None else 0.85,
            "method": method,
            "trained": self.model is not None,
        }