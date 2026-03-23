from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from models.base import Base


class Quote(Base):
    __tablename__ = "quotes"

    id                      = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    procurement_request_id  = Column(UUID(as_uuid=True), ForeignKey("procurement_requests.id"),
                                     nullable=False, index=True)

    # Supplier info
    supplier_name           = Column(String(255), nullable=False)
    supplier_url            = Column(String(500),  nullable=True)

    # Pricing — referenced in export.py and orders.py
    unit_price              = Column(Float,        nullable=True)
    total_price             = Column(Float,        nullable=True)
    currency                = Column(String(3),    default="USD")
    minimum_order_qty       = Column(Integer,      nullable=True)

    # Logistics
    delivery_days           = Column(Integer,      nullable=True)
    payment_terms           = Column(String(255),  nullable=True)
    additional_notes        = Column(String(2000), nullable=True)

    # AI scoring — referenced in export.py (score.desc()) and analytics.py (is_recommended)
    score                   = Column(Float,        nullable=True)   # 0.0 – 100.0
    is_recommended          = Column(Boolean,      default=False)

    # Status
    status                  = Column(String(50),   default="fetching")
    # "fetching" | "received" | "error" | "selected" | "rejected"

    # Raw data from browser agent — orders.py reads reference_id from here
    raw_extracted_data      = Column(JSON,         nullable=True)

    # Timestamps
    fetched_at              = Column(DateTime,     nullable=True)
    created_at              = Column(DateTime,     default=datetime.utcnow, nullable=False)
    updated_at              = Column(DateTime,     default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    procurement_request = relationship("ProcurementRequest", back_populates="quotes")

    def __repr__(self) -> str:
        return f"<Quote {self.supplier_name} {self.total_price} [{self.status}]>"