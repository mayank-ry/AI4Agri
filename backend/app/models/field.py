from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from app.db.base_class import Base

class Field(Base):
    farm_id = Column(UUID(as_uuid=True), ForeignKey("farm.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    crop_type = Column(String, nullable=False)
    area_ha = Column(Float, nullable=False)
    growth_stage = Column(String, nullable=False)
    soil_type = Column(String, nullable=False)
    geometry = Column(Geometry("POLYGON", srid=4326), nullable=True)

    farm = relationship("Farm", back_populates="fields")
    daily_statuses = relationship("FieldDailyStatus", back_populates="field", cascade="all, delete-orphan")
    irrigation_recommendations = relationship("IrrigationRecommendation", back_populates="field", cascade="all, delete-orphan")
    leaf_scans = relationship("LeafScan", back_populates="field", cascade="all, delete-orphan")
    weekly_reports = relationship("WeeklyReport", back_populates="field", cascade="all, delete-orphan")
