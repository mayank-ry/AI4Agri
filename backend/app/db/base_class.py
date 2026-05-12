import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy.orm import as_declarative, declared_attr
from sqlalchemy import Column, DateTime
from sqlalchemy.dialects.postgresql import UUID

@as_declarative()
class Base:
    id: Any
    __name__: str

    # Generate __tablename__ automatically from class name
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
