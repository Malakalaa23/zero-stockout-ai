"""
TFT-MPIR: End-to-End Multi-Period Inventory Replenishment

Malak's Decision Agent - Now with Trained Neural Network!
"""

from typing import List, Dict, Tuple, Optional
import numpy as np
import torch
import pickle
import os
import logging

logger = logging.getLogger(__name__)


class TFTMPIR_DecisionAgent:
    """
    Decision Agent implementing TFT-MPIR for optimal inventory replenishment.
    """
    
    def __init__(self, cost_params: Optional[Dict[str, float]] = None):
        self.holding_cost = cost_params.get('holding', 2.0) if cost_params else 2.0
        self.stockout_cost = cost_params.get('stockout', 100.0) if cost_params else 100.0
        self.shipping_base = cost_params.get('shipping_base', 50.0) if cost_params else 50.0
        self.shipping_per_unit = cost_params.get('shipping_per_unit', 5.0) if cost_params else 5.0
        
        self.model = None
        self.scaler = None
        self.features = None
        self._load_model()
    
    def _load_model(self):
        """Load the trained model from disk."""
        try:
            model_path = 'models/decision_model.pth'
            scaler_path = 'models/decision_scaler.pkl'
            features_path = 'models/decision_features.pkl'
            
            if not all(os.path.exists(p) for p in [model_path, scaler_path, features_path]):
                logger.warning("Trained model not found. Using rule-based fallback.")
                return
            
            with open(features_path, 'rb') as f:
                self.features = pickle.load(f)
            
            with open(scaler_path, 'rb') as f:
                self.scaler = pickle.load(f)
            
            # CORRECT IMPORT: tft_mpir_model
            from backend.agents.tft_mpir_model import TFT_MPIR_Model
            self.model = TFT_MPIR_Model(input_dim=len(self.features))
            self.model.load_state_dict(torch.load(model_path, map_location='cpu'))
            self.model.eval()
            
            logger.info(f"✅ Trained model loaded with {len(self.features)} features")
            
        except Exception as e:
            logger.warning(f"Failed to load trained model: {e}")
            self.model = None
    
    def _predict_with_model(self, features: List[float]) -> Optional[int]:
        """Use trained model to predict optimal order quantity."""
        if self.model is None or self.scaler is None:
            return None
        
        try:
            features_array = np.array(features).reshape(1, -1)
            features_scaled = self.scaler.transform(features_array)
            features_tensor = torch.FloatTensor(features_scaled)
            
            with torch.no_grad():
                prediction = self.model(features_tensor).item()
            
            return max(0, int(round(prediction)))
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            return None
    
    def compute_total_cost(self, order_qty: int, demand_forecast: List[float], 
                          current_stock: int, days: int) -> float:
        """Compute total cost for a given order quantity."""
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
    
    def optimal_quantity(self, demand_forecast: List[float], 
                         current_stock: int, days: int) -> Tuple[int, float]:
        """Find optimal order quantity using trained model or fallback."""
        if not demand_forecast:
            raise ValueError("Demand forecast cannot be empty")
        if days <= 0:
            raise ValueError("Days must be positive")
        if current_stock < 0:
            raise ValueError("Current stock cannot be negative")
        
        expected_demand = sum(demand_forecast[:days])
        
        if current_stock >= expected_demand:
            return 0, self.compute_total_cost(0, demand_forecast, current_stock, days)
        
        # Try trained model
        if self.model is not None and self.features is not None:
            try:
                feature_dict = {
                    'price': 10.0,
                    'cost': 5.0,
                    'stock': current_stock,
                    'sales_7d': sum(demand_forecast[:7]) / 7 if len(demand_forecast) >= 7 else sum(demand_forecast) / len(demand_forecast),
                    'sales_30d': sum(demand_forecast[:30]) / 30 if len(demand_forecast) >= 30 else sum(demand_forecast) / len(demand_forecast),
                    'demand_7d': sum(demand_forecast[:7]) / 7 if len(demand_forecast) >= 7 else sum(demand_forecast) / len(demand_forecast),
                    'stock_ratio': current_stock / (sum(demand_forecast[:7]) / 7 + 1) if len(demand_forecast) >= 7 else current_stock / (sum(demand_forecast) / len(demand_forecast) + 1),
                    'day_of_week': 0,
                    'month': 1,
                    'quarter': 1,
                    'price_change': 0.0
                }
                
                features = [feature_dict.get(f, 0) for f in self.features]
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
    
    def optimal_quantity_vectorized(self, demand_forecast: List[float], 
                                    current_stock: int, days: int) -> Tuple[int, float]:
        """Vectorized version using Newsvendor model (O(1) approximation)."""
        if not demand_forecast:
            raise ValueError("Demand forecast cannot be empty")
        if days <= 0:
            raise ValueError("Days must be positive")
        if current_stock < 0:
            raise ValueError("Current stock cannot be negative")
        
        expected_demand = sum(demand_forecast[:days])
        
        if current_stock >= expected_demand:
            return 0, self.compute_total_cost(0, demand_forecast, current_stock, days)
        
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
    
    def recommend(self, demand_forecast: List[float], current_stock: int, 
                  days: int, method: str = "auto") -> Dict[str, any]:
        """Get a complete recommendation with rationale."""
        if method == "auto":
            if self.model is not None:
                method = "trained_model"
            else:
                method = "vectorized"
        
        if method == "trained_model":
            qty, cost = self.optimal_quantity(demand_forecast, current_stock, days)
        elif method == "brute_force":
            qty, cost = self.optimal_quantity(demand_forecast, current_stock, days)
        else:
            qty, cost = self.optimal_quantity_vectorized(demand_forecast, current_stock, days)
        
        expected_demand = sum(demand_forecast[:days])
        
        if qty == 0:
            rationale = f"Current stock ({current_stock}) is sufficient for demand ({expected_demand:.0f})"
        else:
            deficit = expected_demand - current_stock
            if self.model is not None:
                rationale = f"TFT-MPIR predicts order {qty} units to cover {deficit:.0f} unit deficit"
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
            "trained": self.model is not None
        }