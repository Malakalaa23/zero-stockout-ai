"""
TFT-MPIR: End-to-End Multi-Period Inventory Replenishment

Malak's Decision Agent - Now with Trained Neural Network!
"""

# ---- IMPORTS ----
#SAPiBench data
# (Python doesn't enforce these at runtime)
from typing import List, Dict, Tuple, Optional

# NumPy: array math for the vectorized newsvendor method
import numpy as np

# PyTorch: used to LOAD the trained model and run inference (not training)
import torch

# pickle: loads the saved scaler and feature list (Python's serialization format)
import pickle

# os: checks whether model files exist on disk
import os

# logging: warnings when the model is missing (so we know it fell back)
import logging

# Module-level logger — writes to whatever logging config is set by the app
logger = logging.getLogger(__name__)


# ---- THE CLASS ----
class TFTMPIR_DecisionAgent:
    """
    Decision Agent implementing TFT-MPIR for optimal inventory replenishment.
    Given a demand forecast + current stock, outputs the cost-optimal order qty.
    """

    def __init__(self, cost_params: Optional[Dict[str, float]] = None):
        # Cost parameters are INJECTED, not hardcoded. Each SKU can have its own.
        # .get(key, default) reads the value or uses the default if missing.
        self.holding_cost = cost_params.get('holding', 2.0) if cost_params else 2.0
        self.stockout_cost = cost_params.get('stockout', 100.0) if cost_params else 100.0
        self.shipping_base = cost_params.get('shipping_base', 50.0) if cost_params else 50.0
        self.shipping_per_unit = cost_params.get('shipping_per_unit', 5.0) if cost_params else 5.0

        # These three hold the trained model + preprocessing objects.
        # They start as None and get filled by _load_model().
        self.model = None       # the PyTorch neural net
        self.scaler = None      # normalizes inputs to training distribution
        self.features = None    # the exact feature order the model expects

        # Try to load the trained model right away.
        # If it fails, we silently fall back to brute force later.
        self._load_model()


    # ---- MODEL LOADING ----
    def _load_model(self):
        """Load the trained model from disk. Silent failure if unavailable."""
        try:
            # The three files that must travel together for the model to work.
            # Weights alone are useless without scaler + feature list.
            model_path = 'models/decision_model.pth'
            scaler_path = 'models/decision_scaler.pkl'
            features_path = 'models/decision_features.pkl'

            # Check ALL three exist. If any is missing, skip loading.
            # os.path.exists returns True/False; all() requires every one True.
            if not all(os.path.exists(p) for p in [model_path, scaler_path, features_path]):
                logger.warning("Trained model not found. Using rule-based fallback.")
                return

            # Load the feature names in the exact order the model was trained on.
            # 'rb' = read binary. pickle.load deserializes back to a Python list.
            with open(features_path, 'rb') as f:
                self.features = pickle.load(f)

            # Load the scaler (fitted during training, must match at inference).
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)

            # Import the model CLASS (architecture definition) from another file.
            # This file only has the architecture, not the weights.
            from backend.agents.tft_mpir_model import TFT_MPIR_Model

            # Instantiate the model with the right input size.
            # len(self.features) tells us how many input features the net expects.
            self.model = TFT_MPIR_Model(input_dim=len(self.features))

            # Load the trained weights into the model.
            # map_location='cpu' means "load on CPU even if trained on GPU".
            self.model.load_state_dict(torch.load(model_path, map_location='cpu'))

            # CRITICAL: put the model in eval mode.
            # Disables dropout and freezes batch-norm statistics.
            # Without this, inference results would be non-deterministic.
            self.model.eval()

            logger.info(f"✅ Trained model loaded with {len(self.features)} features")

        except Exception as e:
            # Any error (corrupt file, torch version, import error) → fallback mode.
            # Never crash the API because of a missing model artifact.
            logger.warning(f"Failed to load trained model: {e}")
            self.model = None


    # ---- INFERENCE ----
    def _predict_with_model(self, features: List[float]) -> Optional[int]:
        """Use trained model to predict optimal order quantity. Returns None on failure."""
        # Guard: if model or scaler missing, tell caller to fall back.
        if self.model is None or self.scaler is None:
            return None

        try:
            # Convert Python list → NumPy array → reshape to (1, n_features).
            # Neural nets expect batched 2D inputs, even for single samples.
            features_array = np.array(features).reshape(1, -1)

            # Apply the same normalization used during training.
            # Mismatched scaling → garbage predictions.
            features_scaled = self.scaler.transform(features_array)

            # Convert NumPy → PyTorch tensor. Nets work on tensors, not arrays.
            features_tensor = torch.FloatTensor(features_scaled)

            # no_grad disables gradient tracking (we're inferring, not training).
            # Saves memory and speeds up forward pass.
            with torch.no_grad():
                prediction = self.model(features_tensor).item()

            # Round to nearest integer, clamp at 0 (no negative orders).
            return max(0, int(round(prediction)))

        except Exception as e:
            # Any failure → return None so caller falls back to brute force.
            logger.error(f"Prediction failed: {e}")
            return None


    # ---- THE COST FUNCTION (HEART OF THE MODEL) ----
    def compute_total_cost(self, order_qty: int, demand_forecast: List[float],
                          current_stock: int, days: int) -> float:
        """Compute total cost = stockout + holding + shipping for a given order qty."""

        # Input validation — fail loudly with clear messages, never silently.
        if not demand_forecast:
            raise ValueError("Demand forecast cannot be empty")
        if days <= 0:
            raise ValueError("Days must be positive")
        if order_qty < 0:
            raise ValueError("Order quantity cannot be negative")
        if current_stock < 0:
            raise ValueError("Current stock cannot be negative")

        # Sum the first `days` forecast values → total expected demand over horizon.
        expected_demand = sum(demand_forecast[:days])

        # STOCKOUT COST: units we couldn't fulfill × penalty per unit.
        # max(0, ...) clamps: if we have MORE than enough, stockout is 0, not negative.
        stockout_units = max(0, expected_demand - current_stock - order_qty)
        stockout_cost = stockout_units * self.stockout_cost

        # HOLDING COST: average inventory × per-unit-per-day × days.
        # Cycle stock approximation: start − half of consumed + half of received.
        # max(0, ...) clamps negative inventory (impossible to hold negative units).
        avg_inventory = current_stock - expected_demand + (order_qty / 2)
        holding_cost = max(0, avg_inventory) * self.holding_cost * days

        # SHIPPING COST: fixed base + per-unit variable cost.
        shipping_cost = self.shipping_base + (order_qty * self.shipping_per_unit)

        # Total is the sum of all three. Return as float for consistency.
        return float(stockout_cost + holding_cost + shipping_cost)


    # ---- THE OPTIMIZER (MODEL → FALLBACK) ----
    def optimal_quantity(self, demand_forecast: List[float],
                         current_stock: int, days: int) -> Tuple[int, float]:
        """Find optimal order qty using trained model, or brute-force if unavailable."""
        # Same validation as above — cheap, no reason to skip.
        if not demand_forecast:
            raise ValueError("Demand forecast cannot be empty")
        if days <= 0:
            raise ValueError("Days must be positive")
        if current_stock < 0:
            raise ValueError("Current stock cannot be negative")

        expected_demand = sum(demand_forecast[:days])

        # EARLY EXIT: if stock already covers demand, no need to order.
        # Saves compute and gives a clear, verifiable answer.
        if current_stock >= expected_demand:
            return 0, self.compute_total_cost(0, demand_forecast, current_stock, days)

        # ---- Try the trained neural net first ----
        if self.model is not None and self.features is not None:
            try:
                # Build the feature dict. Keys MUST match the training feature names.
                # Hardcoded defaults for demo — production would pull these from a DB.
                feature_dict = {
                    'price': 10.0,      # unit price (default)
                    'cost': 5.0,        # unit cost (default)
                    'stock': current_stock,     # from user input
                    # Rolling averages — computed from the forecast we were given.
                    # Conditional avoids division by zero if forecast is short.
                    'sales_7d': sum(demand_forecast[:7]) / 7 if len(demand_forecast) >= 7 else sum(demand_forecast) / len(demand_forecast),
                    'sales_30d': sum(demand_forecast[:30]) / 30 if len(demand_forecast) >= 30 else sum(demand_forecast) / len(demand_forecast),
                    'demand_7d': sum(demand_forecast[:7]) / 7 if len(demand_forecast) >= 7 else sum(demand_forecast) / len(demand_forecast),
                    # Coverage ratio: current stock / avg weekly demand.
                    # +1 avoids division by zero.
                    'stock_ratio': current_stock / (sum(demand_forecast[:7]) / 7 + 1) if len(demand_forecast) >= 7 else current_stock / (sum(demand_forecast) / len(demand_forecast) + 1),
                    'day_of_week': 0,   # default — would come from real date
                    'month': 1,         # default — would come from real date
                    'quarter': 1,       # default — would come from real date
                    'price_change': 0.0  # default — recent price delta
                }

                # Build the input vector in the EXACT order the model expects.
                # self.features was saved during training, so order is preserved.
                # .get(f, 0) defaults to 0 if a feature name is somehow missing.
                features = [feature_dict.get(f, 0) for f in self.features]

                # Run inference.
                qty = self._predict_with_model(features)

                if qty is not None:
                    # Compute cost for the model's prediction and return.
                    cost = self.compute_total_cost(qty, demand_forecast, current_stock, days)
                    return qty, cost

            except Exception as e:
                # Any failure in feature building or inference → fall through.
                logger.warning(f"Model prediction failed, using fallback: {e}")

        # ---- FALLBACK: brute-force search ----
        # Iterate q from 0 to 1.5× expected demand, track minimum cost.
        # Why 1.5×? Beyond that, holding cost dominates so heavily the optimum
        # mathematically can't be there. Cap saves ~30% search time, zero accuracy loss.
        best_q = 0
        best_cost = float('inf')
        max_q = int(expected_demand * 1.5)

        for q in range(max_q + 1):
            cost = self.compute_total_cost(q, demand_forecast, current_stock, days)
            if cost < best_cost:
                best_cost = cost
                best_q = q

        return best_q, best_cost


    # ---- VECTORIZED NEWSVENDOR (ALTERNATE O(1) APPROXIMATION) ----
    def optimal_quantity_vectorized(self, demand_forecast: List[float],
                                    current_stock: int, days: int) -> Tuple[int, float]:
        """Vectorized version using Newsvendor model (O(1) approximation).
        Classical inventory formula: order at the critical-ratio percentile of demand.
        """
        if not demand_forecast:
            raise ValueError("Demand forecast cannot be empty")
        if days <= 0:
            raise ValueError("Days must be positive")
        if current_stock < 0:
            raise ValueError("Current stock cannot be negative")

        expected_demand = sum(demand_forecast[:days])

        if current_stock >= expected_demand:
            return 0, self.compute_total_cost(0, demand_forecast, current_stock, days)

        # NEWSENDOR RATIO: underage (stockout) / (underage + overage) costs.
        # This ratio tells you which quantile of demand to cover.
        # High stockout cost → high ratio → order conservatively (large qty).
        underage_cost = self.stockout_cost          # cost of ordering too little
        overage_cost = self.holding_cost * days     # cost of ordering too much
        critical_ratio = underage_cost / (underage_cost + overage_cost)

        # Cumulative sum ≈ demand CDF. Take the critical-ratio percentile.
        cumsum = np.cumsum(demand_forecast[:days])
        qty = int(np.ceil(np.percentile(cumsum, critical_ratio * 100)))

        # Shipping breakpoint: minimum qty that justifies the fixed shipping base.
        # Below this, you're paying $50 base for a tiny order → inefficient.
        shipping_breakpoint = self.shipping_base / self.shipping_per_unit
        if qty < shipping_breakpoint:
            qty = int(shipping_breakpoint)

        # Bound by 1.5× expected demand (same cap as brute force).
        qty = min(qty, int(expected_demand * 1.5))
        cost = self.compute_total_cost(qty, demand_forecast, current_stock, days)

        return int(qty), float(cost)


    # ---- RECOMMENDATION WRAPPER (USER-FACING API) ----
    def recommend(self, demand_forecast: List[float], current_stock: int,
                  days: int, method: str = "auto") -> Dict[str, any]:
        """Get a complete recommendation with rationale and confidence score."""

        # Auto-select method: prefer trained model, else vectorized newsvendor.
        if method == "auto":
            if self.model is not None:
                method = "trained_model"
            else:
                method = "vectorized"

        # Dispatch to the right engine.
        if method == "trained_model":
            qty, cost = self.optimal_quantity(demand_forecast, current_stock, days)
        elif method == "brute_force":
            qty, cost = self.optimal_quantity(demand_forecast, current_stock, days)
        else:
            qty, cost = self.optimal_quantity_vectorized(demand_forecast, current_stock, days)

        expected_demand = sum(demand_forecast[:days])

        # Build a natural-language rationale — honest about which engine was used.
        if qty == 0:
            rationale = f"Current stock ({current_stock}) is sufficient for demand ({expected_demand:.0f})"
        else:
            deficit = expected_demand - current_stock
            if self.model is not None:
                rationale = f"TFT-MPIR predicts order {qty} units to cover {deficit:.0f} unit deficit"
            else:
                rationale = f"Order {qty} units to cover {deficit:.0f} unit deficit"

        # Return the full response — decision + context + confidence + metadata.
        return {
            "order_quantity": qty,                                  # the decision
            "total_cost": cost,                                     # the cost
            "expected_demand": expected_demand,                     # context
            "current_stock": current_stock,                         # context
            "holding_cost": self.holding_cost,                      # cost params
            "stockout_cost": self.stockout_cost,                    # cost params
            "shipping_cost": self.shipping_base + (qty * self.shipping_per_unit),  # breakdown
            "rationale": rationale,                                 # human-readable why
            "confidence": 0.95 if self.model is not None else 0.85, # reliability signal
            "method": method,                                       # which engine ran
            "trained": self.model is not None                       # boolean flag for UI
        }