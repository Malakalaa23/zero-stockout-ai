"""
Vision Agent — package detection and damage classification.

Uses YOLO weights (best.pt) trained on damaged/undamaged packages.

Author: Nada (CV Lead) / integrated by Malak
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

try:
    from ultralytics import YOLO
    ULTRALYTICS_AVAILABLE = True
except ImportError:
    ULTRALYTICS_AVAILABLE = False
    YOLO = None  # type: ignore


class VisionAgent:
    """YOLO-based package detection agent."""

    def __init__(self, model_path: Optional[str] = None) -> None:
        self.model_path = model_path or str(
            Path(__file__).parent.parent / "models" / "best.pt"
        )
        self.model: Optional[Any] = None
        self._load_error: Optional[str] = None
        self.class_names = ["damaged", "no damaged"]

        if not ULTRALYTICS_AVAILABLE:
            self._load_error = "ultralytics not installed"
            logger.warning("ultralytics not available")
            return

        if not Path(self.model_path).exists():
            self._load_error = f"weights not found at {self.model_path}"
            logger.warning("weights not found at %s", self.model_path)
            return

        try:
            self.model = YOLO(self.model_path)
            logger.info("Loaded YOLO from %s", self.model_path)
        except Exception as exc:
            self._load_error = str(exc)
            logger.error("Failed to load YOLO: %s", exc)

    def detect(self, image_path: str, conf_threshold: float = 0.25) -> dict:
        """Run detection on an image."""
        if self.model is None:
            return {
                "detections": [],
                "count": 0,
                "model_available": False,
                "error": self._load_error or "model not loaded",
            }

        if not Path(image_path).exists():
            return {
                "detections": [],
                "count": 0,
                "model_available": True,
                "error": f"image not found: {image_path}",
            }

        try:
            results = self.model(image_path, conf=conf_threshold, verbose=False)
            detections = []
            for result in results:
                boxes = result.boxes
                if boxes is None:
                    continue
                for box in boxes:
                    cls_id = int(box.cls[0])
                    label = (
                        self.class_names[cls_id]
                        if cls_id < len(self.class_names)
                        else f"class_{cls_id}"
                    )
                    detections.append({
                        "class": label,
                        "confidence": round(float(box.conf[0]), 4),
                        "bbox": [round(float(v), 1) for v in box.xyxy[0].tolist()],
                    })
            return {
                "detections": detections,
                "count": len(detections),
                "model_available": True,
                "error": None,
            }
        except Exception as exc:
            logger.error("Detection failed: %s", exc)
            return {
                "detections": [],
                "count": 0,
                "model_available": True,
                "error": str(exc),
            }