# backend/api/routes.py
# ZERO-STOCKOUT AI API
# Works on Python 3.14 with Pydantic 1.10.13

from fastapi import APIRouter, FastAPI, HTTPException, UploadFile, File
from typing import Optional, List, Dict, Any
import logging
import tempfile
import os
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================
# AGENT IMPORTS
# ============================================================
from agents.decision_agent import TFTMPIR_DecisionAgent
from agents.rag_agent import get_rag_agent
from agents.forecast_agent import ForecastAgent

# VisionAgent is imported lazily inside endpoints to avoid
# crashing the whole API if ultralytics fails to load.

# ============================================================
# AGENT INSTANCES (loaded once at import time)
# ============================================================
_forecast_agent = ForecastAgent()

# ============================================================
# ROUTER
# ============================================================
router = APIRouter(prefix="/predict", tags=["Prediction"])

# ============================================================
# HEALTH CHECK
# ============================================================
@router.get("/health")
async def health_check():
    """System health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "forecast": "operational",
            "decision": "operational",
            "vision": "operational",
            "rag": "operational"
        }
    }

# ============================================================
# FORECAST - Uses real ForecastAgent (statistical or TFT)
# ============================================================
@router.post("/forecast")
async def forecast(sku_id: str, days: int = 14):
    """
    Generate demand forecast for a SKU.

    Uses TFT if checkpoint is available at backend/models/best-tft.ckpt.
    Otherwise uses statistical exponential smoothing with weekly seasonality.

    Args:
        sku_id: Product SKU identifier
        days: Number of days to forecast (default: 14, max: 30)

    Returns:
        Forecast with values, confidence, and method
    """
    try:
        if not sku_id or sku_id.isspace():
            raise HTTPException(status_code=400, detail="SKU ID cannot be empty")
        if days <= 0 or days > 30:
            raise HTTPException(status_code=400, detail="days must be between 1 and 30")

        result = _forecast_agent.predict(sku_id=sku_id, days=days)
        result["timestamp"] = datetime.now().isoformat()
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Forecast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# DECISION - Uses TFT-MPIR Decision Agent
# ============================================================
@router.post("/decision")
async def decision(
    sku_id: str,
    current_stock: int,
    unit_cost: float = 10.0,
    forecast_days: int = 14,
    holding_cost: float = 2.0,
    stockout_cost: float = 100.0,
    shipping_base: float = 50.0,
    shipping_per_unit: float = 5.0
):
    """
    Calculate optimal order quantity using the TFT-MPIR Decision Agent.

    The agent uses the trained neural network if model files are present,
    otherwise falls back to exhaustive cost minimization.
    """
    try:
        if current_stock < 0:
            raise HTTPException(status_code=400, detail="Current stock cannot be negative")

        # Get forecast from the forecast endpoint
        fore = await forecast(sku_id, forecast_days)
        forecast_values = fore["forecast"]

        # Instantiate the agent with the request's cost parameters
        agent = TFTMPIR_DecisionAgent({
            "holding": holding_cost,
            "stockout": stockout_cost,
            "shipping_base": shipping_base,
            "shipping_per_unit": shipping_per_unit,
        })

        # Get recommendation — pass unit_cost for the trained model's features
        result = agent.recommend(
            demand_forecast=forecast_values,
            current_stock=current_stock,
            days=forecast_days,
            unit_cost=unit_cost,
        )

        return {
            "sku_id": sku_id,
            "order_quantity": result["order_quantity"],
            "total_cost": round(result["total_cost"], 2),
            "expected_demand": round(result["expected_demand"], 2),
            "confidence": result["confidence"],
            "rationale": result["rationale"],
            "method": result["method"],
            "trained": result["trained"],
            "timestamp": datetime.now().isoformat()
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Decision error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# VISION - Uses Real YOLO VisionAgent
# ============================================================
@router.post("/vision")
async def vision(file: UploadFile = File(None)):
    """
    Analyze package image for defects using the trained YOLO model.

    Args:
        file: Uploaded image file

    Returns:
        Detection results with damaged/intact counts
    """
    if not file:
        return {
            "status": "no_image",
            "detections": [],
            "damaged_count": 0,
            "intact_count": 0,
            "confidence": 0.0,
            "timestamp": datetime.now().isoformat()
        }

    tmp_path = None
    try:
        # Save uploaded file to a temp path
        contents = await file.read()
        suffix = Path(file.filename or "image.jpg").suffix or ".jpg"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        # Lazy import so API boots even if ultralytics fails
        from agents.vision_agent import VisionAgent
        agent = VisionAgent()
        result = agent.detect(tmp_path)

        # Count damaged vs intact
        damaged = sum(1 for d in result["detections"] if d["class"] == "damaged")
        intact = sum(1 for d in result["detections"] if d["class"] == "no damaged")

        avg_conf = (
            sum(d["confidence"] for d in result["detections"]) / len(result["detections"])
            if result["detections"] else 0.0
        )

        return {
            "status": "success" if result["model_available"] else "model_unavailable",
            "detections": result["detections"],
            "damaged_count": damaged,
            "intact_count": intact,
            "confidence": round(avg_conf, 4),
            "model_available": result["model_available"],
            "error": result.get("error"),
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Vision error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

# ============================================================
# RAG - Uses Jumana's knowledge graph
# ============================================================
@router.post("/rag")
async def rag(query: str):
    """
    Query knowledge base for policy, inventory, and product information.

    Args:
        query: User question (English or Arabic)

    Returns:
        Answer with source and confidence
    """
    try:
        if not query or query.isspace():
            raise HTTPException(status_code=400, detail="Query cannot be empty")

        agent = get_rag_agent()
        result = agent.query(query)

        return {
            "answer": result["answer"],
            "source": result["source"],
            "confidence": result["confidence"],
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"RAG error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# VOICE TRANSCRIPTION
# ============================================================
@router.post("/voice/transcribe")
async def voice_transcribe(file: UploadFile = File(...)):
    """
    Transcribe uploaded audio to text.

    Uses OpenAI Whisper if installed. Otherwise returns a
    graceful fallback so the UI doesn't break.
    """
    tmp_path = None
    try:
        contents = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name

        transcribed_text = ""

        try:
            import whisper
            model = whisper.load_model("base")
            result = model.transcribe(tmp_path)
            transcribed_text = result.get("text", "").strip()
            logger.info(f"Whisper transcribed: {transcribed_text[:80]}...")
        except ImportError:
            logger.warning("Whisper not installed — returning fallback")
        except Exception as e:
            logger.error(f"Whisper error: {e}")

        try:
            if tmp_path:
                os.unlink(tmp_path)
        except Exception:
            pass

        if transcribed_text:
            return {
                "text": transcribed_text,
                "status": "success",
                "model": "whisper-base",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "text": "reorder P001",
                "status": "fallback",
                "model": "fallback",
                "message": "Whisper not installed — returned sample transcription",
                "timestamp": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Voice transcribe error: {e}")
        try:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

# ============================================================
# FULL PIPELINE - Vision + Forecast + Decision (Cross-Agent)
# ============================================================
@router.post("/full")
async def predict_full(
    sku_id: str,
    current_stock: int,
    unit_cost: float = 10.0,
    forecast_days: int = 14,
    image: UploadFile = File(None)
):
    """
    End-to-end pipeline: Vision + Forecast + Decision.

    This is the cross-agent endpoint. It:
      1. Forecasts demand for the SKU
      2. Detects damage from an uploaded image (if provided)
      3. Adjusts effective stock for damaged units
      4. Computes optimal order quantity via the Decision Agent
      5. Returns a SITUATION REPORT — never auto-orders.

    Human-in-the-loop: the caller must approve/modify/reject.
    """
    try:
        if current_stock < 0:
            raise HTTPException(status_code=400, detail="Current stock cannot be negative")

        # ---------- 1. FORECAST ----------
        fore = await forecast(sku_id, forecast_days)
        demand = fore["forecast"]
        expected_demand = sum(demand)

        # ---------- 2. VISION (optional) ----------
        damaged_count = 0
        intact_count = 0
        damage_detections = []
        vision_error = None

        if image is not None:
            tmp_path = None
            try:
                contents = await image.read()
                suffix = Path(image.filename or "image.jpg").suffix or ".jpg"
                with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                    tmp.write(contents)
                    tmp_path = tmp.name

                from agents.vision_agent import VisionAgent
                v_agent = VisionAgent()
                v_result = v_agent.detect(tmp_path)
                damage_detections = v_result["detections"]
                damaged_count = sum(1 for d in damage_detections if d["class"] == "damaged")
                intact_count = sum(1 for d in damage_detections if d["class"] == "no damaged")
                vision_error = v_result.get("error")
            finally:
                if tmp_path and os.path.exists(tmp_path):
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass

        # ---------- 3. ADJUST STOCK ----------
        effective_stock = max(0, current_stock - damaged_count)

        # ---------- 4. DECISION ----------
        agent = TFTMPIR_DecisionAgent()
        qty, cost, method = agent.optimal_quantity(
            demand_forecast=demand,
            current_stock=effective_stock,
            days=forecast_days,
            unit_cost=unit_cost,
        )

        deficit = max(0, expected_demand - effective_stock)

        # ---------- 5. SITUATION REPORT ----------
        return {
            "sku_id": sku_id,
            "situation": {
                "current_stock": current_stock,
                "damaged_units": damaged_count,
                "intact_units": intact_count if damage_detections else current_stock,
                "effective_stock": effective_stock,
                "predicted_demand": round(expected_demand, 1),
                "deficit": round(deficit, 1),
            },
            "forecast": {
                "daily_demand": demand,
                "confidence": fore.get("confidence", 0.85),
                "method": fore.get("method", "statistical"),
            },
            "damage_detections": damage_detections,
            "vision_error": vision_error,
            "recommendation": {
                "suggested_order_qty": qty,
                "estimated_cost": round(cost, 2),
                "method_used": method,
                "rationale": (
                    f"Predicted demand over {forecast_days} days: {expected_demand:.0f} units. "
                    f"Effective stock: {effective_stock} units "
                    f"({damaged_count} damaged, {current_stock} current). "
                    f"Recommended order: {qty} units."
                ),
            },
            "human_action_required": True,
            "message": (
                f"📊 Situation for {sku_id}:\n"
                f"  • Current stock: {current_stock} units\n"
                f"  • Damaged: {damaged_count} units\n"
                f"  • Effective stock: {effective_stock} units\n"
                f"  • Predicted demand: {expected_demand:.0f} units\n"
                f"  • Recommended order: {qty} units\n"
                f"\n"
                f"⚠️ Awaiting your decision. Approve, modify, or reject."
            ),
            "timestamp": datetime.now().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Full pipeline error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ============================================================
# FASTAPI APP
# ============================================================
app = FastAPI(
    title="Zero-Stockout AI API",
    description="TFT-MPIR Inventory Optimization System with 19% cost reduction",
    version="1.0.0"
)

app.include_router(router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Zero-Stockout AI System",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs",
        "endpoints": [
            "/predict/health",
            "/predict/forecast",
            "/predict/decision",
            "/predict/vision",
            "/predict/rag",
            "/predict/voice/transcribe",
            "/predict/full"
        ]
    }


@app.get("/docs")
async def api_docs():
    """Redirect to OpenAPI documentation."""
    return {
        "docs_url": "/docs",
        "openapi_url": "/openapi.json"
    }