from pydantic import BaseModel
from typing import List, Dict

class DRSConditionFactor(BaseModel):
    name: str
    weight: float
    met: bool
    description: str

class DRSResult(BaseModel):
    score: float  # 0 to 100
    risk_level: str  # Low, Medium, High
    reasons: List[str]
    factors: List[DRSConditionFactor]
