from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from database.supabase_client import get_db, db_insert, storage_upload
from database.auth_helper import verify_token, get_farmer_id
from ml.disease_pipeline import run_disease_pipeline
from ml.hf_models import translate_to_hindi
import uuid
import structlog

router = APIRouter(tags=["disease"])
log = structlog.get_logger()


@router.post("/detect")
async def detect_disease(
    field_id: str = Form(...),
    image: UploadFile = File(...),
    token: dict = Depends(verify_token),
):
    # 1. Validate image
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Upload a JPG/PNG/WebP image.")

    image_bytes = await image.read()
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large. Max 10MB.")

    farmer_id = get_farmer_id(token["sub"])

    # 2. Upload to Supabase Storage
    path = f"detections/{field_id}/{uuid.uuid4()}.jpg"
    try:
        image_url = storage_upload("disease-images", path, image_bytes, "image/jpeg")
    except Exception as e:
        log.error("storage_upload_failed", error=str(e))
        image_url = ""  # Don't block detection if storage fails

    # 3. Run combined CNN + ViT pipeline
    result = run_disease_pipeline(image_bytes)

    # 4. Translate treatment to Hindi if not already translated
    if not result.get("treatment_hi"):
        result["treatment_hi"] = translate_to_hindi(result.get("treatment_en", ""))

    # 5. Translate disease name to Hindi
    disease_name_hi = translate_to_hindi(result["disease_name"])

    # 6. Save to Supabase DB
    detection_data = {
        "field_id": field_id,
        "image_url": image_url,
        "disease_name": result["disease_name"],
        "disease_name_hi": disease_name_hi,
        "confidence": result["confidence"],
        "severity": result["severity"],
        "treatment_en": result.get("treatment_en", ""),
        "treatment_hi": result.get("treatment_hi", ""),
        "top3_predictions": result.get("top3", []),
    }
    inserted = db_insert("disease_detections", detection_data)

    # 7. Create HIGH alert if severe
    if result["severity"] == "severe":
        db_insert("alerts", {
            "field_id": field_id,
            "farmer_id": farmer_id,
            "alert_type": "disease",
            "priority": "HIGH",
            "title_hi": f"⚠️ {disease_name_hi} bimari mili hai!",
            "message_hi": result.get("treatment_hi", ""),
        })

    return {
        "success": True,
        "detection": {
            **(inserted if inserted else detection_data),
            "disease_name_hi": disease_name_hi,
            "model_source": result.get("model_source", "unknown"),
            "estimated_cost": result.get("estimated_cost", ""),
            "cnn_result": result.get("cnn_result"),
            "vit_result": result.get("vit_result"),
        },
    }


@router.get("/history/{field_id}")
async def get_history(field_id: str, token: dict = Depends(verify_token)):
    db = get_db()
    resp = (
        db.table("disease_detections")
        .select("*")
        .eq("field_id", field_id)
        .order("detected_at", desc=True)
        .limit(10)
        .execute()
    )
    return {"success": True, "history": resp.data}


@router.get("/models/status")
async def model_status():
    """Show status of all ML models — useful for demo/debugging."""
    from ml.model_manager import get_all_status
    return {"success": True, "models": get_all_status()}
