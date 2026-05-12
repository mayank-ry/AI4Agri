from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from app.models.ai import LeafScan
from app.schemas.ai import DiseaseDetectionResponse

async def create_leaf_scan_record(
    db: AsyncSession,
    user_id: uuid.UUID,
    field_id: uuid.UUID,
    image_path: str,
    ai_result: DiseaseDetectionResponse
) -> LeafScan:
    """
    Persist the LeafScan and its AI results to PostgreSQL.
    """
    db_scan = LeafScan(
        user_id=user_id,
        field_id=field_id,
        image_path=image_path,
        disease_name=ai_result.disease_name,
        confidence=ai_result.confidence,
        severity_level=ai_result.severity_level,
        recommendation_text=ai_result.recommendation_text,
        explanation=ai_result.explanation
    )
    
    db.add(db_scan)
    await db.commit()
    await db.refresh(db_scan)
    return db_scan
