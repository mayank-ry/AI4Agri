from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import Optional
from app.db.supabase import get_supabase_client
from app.api.deps import get_current_farmer
from app.ml.disease_model import disease_model_wrapper
from app.services.hf_service import hf_service
import structlog
from PIL import Image
import io

logger = structlog.get_logger(__name__)
router = APIRouter()

async def compress_image(image_bytes: bytes) -> bytes:
    """Compress image to JPEG format if needed."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        out_io = io.BytesIO()
        img.save(out_io, format="JPEG", quality=85)
        return out_io.getvalue()
    except Exception as e:
        logger.error("image_compression_failed", error=str(e))
        return image_bytes

@router.post("/detect")
async def detect_disease(
    field_id: str = Form(...),
    file: UploadFile = File(...),
    farmer=Depends(get_current_farmer),
    supabase=Depends(get_supabase_client)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Must be an image file")
        
    try:
        contents = await file.read()
        
        # Compress if > 2MB
        if len(contents) > 2 * 1024 * 1024:
            contents = await compress_image(contents)
            
        # 1. Upload to Supabase Storage
        file_path = f"{farmer['id']}/{field_id}/{file.filename}"
        
        # Uploading to 'disease-images' bucket
        storage_resp = supabase.storage.from_("disease-images").upload(
            file_path, 
            contents, 
            {"content-type": "image/jpeg", "upsert": "true"}
        )
        image_url = supabase.storage.from_("disease-images").get_public_url(file_path)
        
        # 2. Call existing MobileNetV2 ML Model
        result = await disease_model_wrapper.predict_async(contents)
        
        # 3. Translate to Hindi using HuggingFace
        disease_name_hi = hf_service.translate_to_hindi(result['disease_name'])
        treatment_hi = hf_service.translate_to_hindi(result['recommendation_text'])
        
        # 4. Save to DB
        detection_data = {
            "field_id": field_id,
            "image_url": image_url,
            "disease_name": result["disease_name"],
            "disease_name_hi": disease_name_hi,
            "confidence": float(result["confidence"]),
            "severity": result["severity_level"],
            "treatment_en": result["recommendation_text"],
            "treatment_hi": treatment_hi,
            "top3_predictions": result["top_k_predictions"],
            "model_used": "custom_mobilenetv2"
        }
        
        db_resp = supabase.table("disease_detections").insert(detection_data).execute()
        
        # 5. Return Complete Data
        return {"success": True, "detection": db_resp.data[0] if db_resp.data else detection_data}
    except Exception as e:
        logger.error("disease_detection_error", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

@router.get("/history/{field_id}")
async def get_disease_history(field_id: str, farmer=Depends(get_current_farmer), supabase=Depends(get_supabase_client)):
    try:
        # Verify ownership
        field_check = supabase.table("fields").select("id").eq("id", field_id).eq("farmer_id", farmer["id"]).execute()
        if not field_check.data:
            raise HTTPException(status_code=404, detail="Field not found")
            
        history = supabase.table("disease_detections").select("*").eq("field_id", field_id).order("detected_at", desc=True).limit(10).execute()
        return {"success": True, "history": history.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
