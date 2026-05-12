from fastapi import APIRouter, Query, Path
from app.schemas.drs import DRSResult
from app.services.drs_engine import DRSEngine
import structlog

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.get("/field/{field_id}/disease-risk", response_model=DRSResult)
async def get_disease_risk(
    field_id: str = Path(..., description="The ID of the field"),
    crop_type: str = Query(..., description="Type of crop in the field"),
    humidity: float = Query(..., description="Current relative humidity %"),
    temperature: float = Query(..., description="Current temperature in Celsius"),
    rainfall_3d: float = Query(..., description="Total rainfall in mm over last 3 days")
):
    """
    Calculate the Disease Risk Score (DRS) for a given field based on environmental parameters.
    This provides an Explainable AI output detailing exactly why a certain score was assigned.
    """
    logger.info("calculating_drs", field_id=field_id, crop_type=crop_type)
    
    result = DRSEngine.calculate_drs(
        crop_type=crop_type,
        current_humidity=humidity,
        current_temp=temperature,
        rainfall_3d_total=rainfall_3d
    )
    
    return result
