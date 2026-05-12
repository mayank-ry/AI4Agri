from pydantic import BaseModel
from typing import List, Optional

class DiseaseFactor(BaseModel):
    name: str
    value: str
    impact: str
    description: str

class TopKPrediction(BaseModel):
    disease_name: str
    confidence: float

class DiseaseDetectionResponse(BaseModel):
    disease_name: str
    confidence: float
    severity_level: str
    recommendation_text: str
    explanation: str
    reasons: List[str]
    factors: List[DiseaseFactor]
    top_k_predictions: List[TopKPrediction]

class ModelStatusResponse(BaseModel):
    status: str
    model_loaded: bool
    error: Optional[str] = None
