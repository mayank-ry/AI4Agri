from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class User(Base):
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="farmer", nullable=False)
    language_preference = Column(String, default="en", nullable=False)

    farms = relationship("Farm", back_populates="user", cascade="all, delete-orphan")
    leaf_scans = relationship("LeafScan", back_populates="user", cascade="all, delete-orphan")
