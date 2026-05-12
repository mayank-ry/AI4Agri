from sqlalchemy import Column, Float, Boolean, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from app.db.base_class import Base

class IrrigationRecommendation(Base):
    __tablename__ = "irrigation_recommendation"
    
    field_id = Column(UUID(as_uuid=True), ForeignKey("field.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    irrigation_required = Column(Boolean, nullable=False)
    recommended_amount_mm = Column(Float, nullable=False)
    skip_reason = Column(Text, nullable=True)
    priority_index = Column(Float, nullable=False)
    reasons = Column(JSON, nullable=False)
    factors = Column(JSON, nullable=False)

    field = relationship("Field", back_populates="irrigation_recommendations")
