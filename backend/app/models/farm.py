from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.db.base_class import Base

class Farm(Base):
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    district = Column(String, nullable=False)
    state = Column(String, nullable=False)

    user = relationship("User", back_populates="farms")
    fields = relationship("Field", back_populates="farm", cascade="all, delete-orphan")
