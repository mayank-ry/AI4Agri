from fastapi import APIRouter, UploadFile, File, HTTPException, Form, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import uuid

from app.ml.disease_model import disease_model_wrapper
from app.schemas.ai import DiseaseDetectionResponse, ModelStatusResponse
from app.services.supabase_client import supabase_storage
from app.crud.crud_leaf_scan import create_leaf_scan_record
from app.db.session import get_db
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/status", response_model=ModelStatusResponse)
async def get_model_status():
    """Check if the ML model is currently loaded and available."""
    is_loaded = disease_model_wrapper.model is not None or disease_model_wrapper.interpreter is not None
    return ModelStatusResponse(
        status="available" if is_loaded else "unavailable",
        model_loaded=is_loaded,
        error=None if is_loaded else "Model file not found or not configured."
    )

@router.post("/disease-detect", response_model=DiseaseDetectionResponse)
async def detect_disease(
    file: UploadFile = File(...),
    user_id: uuid.UUID = Form(...),
    field_id: uuid.UUID = Form(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Run crop disease detection inference on an uploaded leaf image.
    Uploads the image to Supabase Storage and persists the AI result into the PostgreSQL LeafScan table.
    """
    # Verify model is loaded
    if not (disease_model_wrapper.model or disease_model_wrapper.interpreter):
        raise HTTPException(status_code=503, detail="Inference model is currently unavailable.")
        
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")
        
    try:
        # Read file bytes
        image_bytes = await file.read()
        
        # 1. Run async-safe inference pipeline
        result_dict = await disease_model_wrapper.predict_async(image_bytes)
        result_obj = DiseaseDetectionResponse(**result_dict)
        
        # 2. Upload to Supabase Storage asynchronously
        storage_path = await supabase_storage.upload_leaf_scan(
            user_id=str(user_id),
            field_id=str(field_id),
            image_bytes=image_bytes,
            content_type=file.content_type
        )
        
        # 3. Persist to PostgreSQL Database
        await create_leaf_scan_record(
            db=db,
            user_id=user_id,
            field_id=field_id,
            image_path=storage_path,
            ai_result=result_obj
        )
        
        return result_obj
        
    except ValueError as ve:
        logger.warning("invalid_image_format", error=str(ve))
        raise HTTPException(status_code=400, detail="Invalid or corrupted image file.")
    except Exception as e:
        logger.error("inference_error", error=str(e))
        raise HTTPException(status_code=500, detail="Internal error during inference processing.")
