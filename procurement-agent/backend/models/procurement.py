from sqlalchemy import Column, String, Integer, Float, DateTime, JSON, Enum as PgEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from models.base import Base


class ProcurementStatus(str, enum.Enum):
    PENDING    = "pending"
    SEARCHING  = "searching"
    QUOTES_IN  = "quotes_in"
    COMPLETED  = "completed"
    CANCELLED  = "cancelled"


class ProcurementRequest(Base):
    __tablename__ = "procurement_requests"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)

    # Raw input from user
    raw_description = Column(String(2000), nullable=False)

    # LLM-parsed structured spec
    # e.g. {"product_name": "...", "quantity": 10, "unit": "pcs", "budget": 5000}
    parsed_spec     = Column(JSON, nullable=True)

    # Convenience fields extracted from parsed_spec for quick querying
    product_name    = Column(String(500),  nullable=True)
    quantity        = Column(Integer,      nullable=True)
    budget          = Column(Float,        nullable=True)
    currency        = Column(String(3),    default="USD")
    category        = Column(String(255),  nullable=True)

    status          = Column(PgEnum(ProcurementStatus), default=ProcurementStatus.PENDING, nullable=False)
    notes           = Column(String(2000), nullable=True)

    created_at      = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user   = relationship("User",  back_populates="procurement_requests")
    quotes = relationship("Quote", back_populates="procurement_request", lazy="selectin")

    def __repr__(self) -> str:
        return f"<ProcurementRequest {self.product_name or self.raw_description[:30]} [{self.status}]>"