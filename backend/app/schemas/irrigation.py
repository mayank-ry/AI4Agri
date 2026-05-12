from pydantic import BaseModel
from typing import List

class IrrigationFactor(BaseModel):
    name: str
    value: float
    impact: str
    description: str

class IrrigationRecommendationResult(BaseModel):
    irrigation_required: bool
    recommended_amount_mm: float
    priority_index: float  # IPI
    fhs: float  # Field Health Score
    wsi: float  # Water Stress Index
    reasons: List[str]
    factors: List[IrrigationFactor]
