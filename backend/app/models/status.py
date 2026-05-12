from sqlalchemy import Column, Float, Date, Text, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class FieldDailyStatus(Base):
    __tablename__ = "field_daily_status"
    
    field_id = Column(UUID(as_uuid=True), ForeignKey("field.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    ndvi_value = Column(Float, nullable=True)
    soil_moisture = Column(Float, nullable=True) # 0-1
    rainfall_mm = Column(Float, nullable=True)
    temp_avg = Column(Float, nullable=True)
    field_health_score = Column(Float, nullable=True) # 0-100
    water_stress_index = Column(Float, nullable=True) # 0-1
    notes = Column(Text, nullable=True)

    field = relationship("Field", back_populates="daily_statuses")

    __table_args__ = (
        UniqueConstraint('field_id', 'date', name='uq_field_daily_status'),
    )
