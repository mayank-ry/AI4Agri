from sqlalchemy import Column, Float, String, Date, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
from app.db.base_class import Base

class LeafScan(Base):
    __tablename__ = "leaf_scan"
    
    field_id = Column(UUID(as_uuid=True), ForeignKey("field.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    image_path = Column(String, nullable=False)
    disease_name = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    severity_level = Column(String, nullable=False)
    recommendation_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)

    field = relationship("Field", back_populates="leaf_scans")
    user = relationship("User", back_populates="leaf_scans")

class WeeklyReport(Base):
    __tablename__ = "weekly_report"
    
    field_id = Column(UUID(as_uuid=True), ForeignKey("field.id", ondelete="CASCADE"), nullable=False, index=True)
    week_start = Column(Date, nullable=False)
    week_end = Column(Date, nullable=False)
    health_summary = Column(JSON, nullable=False)
    risk_summary = Column(JSON, nullable=False)
    water_saved_liters = Column(Float, nullable=False)
    cost_saved_inr = Column(Float, nullable=False)

    field = relationship("Field", back_populates="weekly_reports")
