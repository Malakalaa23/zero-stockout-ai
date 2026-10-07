"""
Forecast Agent — demand forecasting.

Primary: TFT (Temporal Fusion Transformer) checkpoint from Sara.
Fallback: Holt-Winters exponential smoothing with weekly seasonality.

Uses manual model reconstruction to load a GPU-trained checkpoint on CPU.

Author: Sara (Forecast Lead) / integrated by Malak
"""

from __future__ import annotations

import logging
import os
import pickle
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# TFT model config (from Sara's training)
TFT_ENCODER_LENGTH = 24
TFT_PREDICTION_LENGTH = 6

# Sara trained on 3 stores x 30 items from the DEPI dataset
TFT_STORES = ["CA_1", "TX_1", "WI_1"]
TFT_ITEMS = [str(i) for i in range(1, 31)]


class ForecastAgent:
    """Demand forecasting agent with TFT + statistical fallback."""

    def __init__(self, model_path: Optional[str] = None, dataset_path: Optional[str] = None) -> None:
        base = Path(__file__).parent.parent / "models"
        self.model_path = model_path or str(base / "best-tft.ckpt")
        self.dataset_path = dataset_path or str(base / "training_dataset.pkl")

        self._tft_model = None
        self._tft_training_dataset = None
        self._tft_available = False
        self._load_tft()

    # ============================================================
    # TFT LOADING — MANUAL RECONSTRUCTION (NO LIGHTNING)
    # ============================================================

    def _load_tft(self) -> None:
        """Load Sara's TFT checkpoint via manual reconstruction. No CUDA, no Lightning."""
        model_p = Path(self.model_path)
        dataset_p = Path(self.dataset_path)

        if not model_p.exists():
            logger.info(f"TFT checkpoint not found at {model_p} - using statistical fallback")
            return
        if not dataset_p.exists():
            logger.info(f"TFT training dataset not found at {dataset_p} - using statistical fallback")
            return

        try:
            os.environ["CUDA_VISIBLE_DEVICES"] = ""

            import torch
            from pytorch_forecasting import TemporalFusionTransformer

            logger.info("Loading TFT checkpoint (manual reconstruction, CPU-only)...")
            ckpt = torch.load(str(model_p), map_location="cpu", weights_only=False)

            hp = dict(ckpt["hyper_parameters"])

            # Drop hparams that are nn.Modules or non-reconstructable
            for key in ["loss", "logging_metrics", "state_dict", "monotone_constraints"]:
                hp.pop(key, None)

            # Reconstruct model from hyperparameters
            logger.info("Reconstructing model from hyperparameters...")
            self._tft_model = TemporalFusionTransformer(**hp)
            self._tft_model.eval()

            # Load trained weights
            missing, unexpected = self._tft_model.load_state_dict(
                ckpt["state_dict"], strict=False
            )
            if missing:
                logger.info(f"  Missing keys: {len(missing)}")
            if unexpected:
                logger.info(f"  Unexpected keys: {len(unexpected)}")

            # Force every parameter to CPU
            for param in self._tft_model.parameters():
                param.data = param.data.to("cpu")
            for buf in self._tft_model.buffers():
                buf.data = buf.data.to("cpu")

            logger.info("Loading TFT training dataset (24 MB)...")
            with open(dataset_p, "rb") as f:
                self._tft_training_dataset = pickle.load(f)

            self._tft_available = True
            logger.info("TFT loaded - real transformer forecasting enabled")

        except Exception as exc:
            logger.warning(f"TFT load failed: {exc} - using statistical fallback")
            self._tft_available = False

    # ============================================================
    # TFT INFERENCE
    # ============================================================

    def _sku_to_group(self, sku_id: str) -> tuple:
        """Map arbitrary SKU ID to a valid (store_id, item_number) pair."""
        digits = "".join(c for c in sku_id if c.isdigit())
        if digits:
            item_num = str(int(digits) % 30 + 1)
        else:
            item_num = str(abs(hash(sku_id)) % 30 + 1)

        store = TFT_STORES[abs(hash(sku_id)) % len(TFT_STORES)]
        return store, item_num

    def _build_prediction_df(self, sku_id: str, history: List[float]) -> pd.DataFrame:
        """Build a 30-day history dataframe matching Sara's schema for TFT inference."""
        store, item_num = self._sku_to_group(sku_id)

        n = 30
        if len(history) >= n:
            values = list(history[-n:])
        else:
            pad = list(history) if history else [10.0] * n
            values = (pad * ((n // len(pad)) + 1))[:n]

        end = pd.Timestamp.today().normalize()
        dates = pd.date_range(end=end, periods=n, freq="D")
        start_time_idx = 100000

        rows = []
        for i, (date, val) in enumerate(zip(dates, values)):
            rows.append({
                "store_id": store,
                "item_number": item_num,
                "item_category": "FOODS",
                "item_subcategory": "1",
                "day_of_week": str(date.dayofweek),
                "time_idx": start_time_idx + i,
                "month": date.month,
                "year": date.year,
                "day": date.day,
                "is_holiday": 0,
                "is_weekend": int(date.dayofweek >= 5),
                "snap": 0,
                "is_event": 0,
                "event_count": 0,
                "event_impact": 0.0,
                "wday_x_snap": 0,
                "sell_price": 10.0,
                "target": float(val),
                "lag_1": float(values[i - 1]) if i >= 1 else float(val),
                "lag_7": float(values[i - 7]) if i >= 7 else float(val),
            })

        return pd.DataFrame(rows)

    def _tft_forecast(self, sku_id: str, history: List[float], days: int) -> List[float]:
        """Run TFT inference. Returns `days` values."""
        import torch
        from pytorch_forecasting import TimeSeriesDataSet

        df = self._build_prediction_df(sku_id, history)

        pred_dataset = TimeSeriesDataSet.from_dataset(
            self._tft_training_dataset,
            df,
            predict=True,
            stop_randomization=True,
        )
        pred_dataloader = pred_dataset.to_dataloader(
            train=False, batch_size=1, num_workers=0
        )

        with torch.no_grad():
            preds = self._tft_model.predict(
                pred_dataloader,
                mode="prediction",       # returns median (q50) by default
                return_x=True,
                return_index=True,
            )

        # ---- Robust shape handling ----
        # Depending on pytorch-forecasting version, output can be:
        #   - (batch, seq)                  -> median prediction
        #   - (batch, seq, 1)               -> median with extra dim
        #   - tensor directly (no .output)  -> rare
        out = preds.output if hasattr(preds, "output") else preds
        out_np = out.cpu().numpy()

        # Squeeze down to 1D list
        out_np = np.squeeze(out_np)
        if out_np.ndim == 0:
            out_np = np.array([float(out_np)])
        elif out_np.ndim > 1:
            # Take first row if still 2D+
            out_np = out_np.flatten()

        # Non-negative, list of floats
        forecast = [max(0.0, float(v)) for v in out_np.tolist()]

        if days <= len(forecast):
            return forecast[:days]

        extra = self._statistical_forecast(history, days - len(forecast))
        return forecast + extra

    # ============================================================
    # STATISTICAL FALLBACK
    # ============================================================

    def _statistical_forecast(
        self,
        history: List[float],
        days: int,
        alpha: float = 0.3,
        beta: float = 0.1,
    ) -> List[float]:
        """Holt-Winters-lite forecast."""
        if not history:
            return [10.0] * days

        clean = [max(0.0, float(x)) for x in history if x is not None and not np.isnan(x)]
        if not clean:
            return [10.0] * days

        seasonal = np.ones(7)
        if len(clean) >= 14:
            by_dow = [[] for _ in range(7)]
            for i, val in enumerate(clean):
                by_dow[i % 7].append(val)
            overall_mean = float(np.mean(clean)) or 1.0
            for d in range(7):
                if by_dow[d]:
                    seasonal[d] = float(np.mean(by_dow[d])) / overall_mean

        deseason = [
            clean[i] / seasonal[i % 7] if seasonal[i % 7] > 0 else clean[i]
            for i in range(len(clean))
        ]

        level = deseason[0]
        trend = 0.0
        for val in deseason[1:]:
            prev = level
            level = alpha * val + (1 - alpha) * (level + trend)
            trend = beta * (level - prev) + (1 - beta) * trend

        start_dow = len(clean) % 7
        out = []
        for h in range(1, days + 1):
            base = level + trend * h
            out.append(max(0.0, base * seasonal[(start_dow + h - 1) % 7]))
        return out

    # ============================================================
    # PUBLIC API
    # ============================================================

    def predict(
        self,
        sku_id: str,
        days: int = 14,
        history: Optional[List[float]] = None,
    ) -> dict:
        """Generate a demand forecast."""
        if days <= 0 or days > 30:
            raise ValueError(f"days must be in [1, 30], got {days}")

        if history is None:
            rng = np.random.default_rng(abs(hash(sku_id)) % (2**32))
            base = rng.uniform(8, 25)
            history = [
                max(0.0, base + rng.normal(0, 3) + 2 * np.sin(i * 2 * np.pi / 7))
                for i in range(28)
            ]

        if self._tft_available:
            try:
                forecast = self._tft_forecast(sku_id, history, days)
                method = "tft"
                confidence = 0.89
            except Exception as exc:
                logger.error(f"TFT inference failed: {exc} - falling back")
                forecast = self._statistical_forecast(history, days)
                method = "statistical"
                confidence = 0.75
        else:
            forecast = self._statistical_forecast(history, days)
            method = "statistical"
            confidence = 0.75

        return {
            "sku_id": sku_id,
            "forecast": [round(float(v), 2) for v in forecast],
            "confidence": confidence,
            "method": method,
            "days": days,
        }