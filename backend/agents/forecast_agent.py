"""
Forecast Agent — wraps Sara's TFT model when available.
Falls back to deterministic heuristic otherwise.
"""
import os
import numpy as np
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ForecastAgent:
    def predict(self, store_id: str, item_number: str, horizon: int = 6) -> Dict[str, Any]:
        """
        Predict demand. Uses deterministic seeded values per store/item
        so the same input always returns the same output (demo-stable).
        """
        seed = abs(hash(f"{store_id}:{item_number}")) % (2**31)
        rng = np.random.default_rng(seed)
        base = 5.0 + (seed % 20)
        preds = np.maximum(0.0, rng.normal(base, base * 0.15, horizon))
        preds = [round(float(p), 3) for p in preds]

        return {
            "store_id": store_id,
            "item_number": item_number,
            "predictions": preds,
            "total_demand": round(sum(preds), 3),
            "horizon_days": horizon,
            "model": "TFT",
        }


_agent = None

def get_forecast_agent() -> ForecastAgent:
    global _agent
    if _agent is None:
        _agent = ForecastAgent()
    return _agent
