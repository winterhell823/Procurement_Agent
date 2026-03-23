from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from models.base import Base


class User(Base):
    __tablename__ = "users"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email           = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Profile — referenced in orders.py company_profile block
    full_name       = Column(String(255), nullable=False)
    contact_person  = Column(String(255), nullable=True)
    company_name    = Column(String(255), nullable=True)
    company_phone   = Column(String(50),  nullable=True)
    company_address = Column(String(500), nullable=True)
    payment_terms   = Column(String(255), nullable=True)
    gst_number      = Column(String(50),  nullable=True)   # GST / tax ID for Indian SMBs

    # Access control
    is_active       = Column(Boolean, default=True,  nullable=False)
    is_admin        = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at      = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    procurement_requests = relationship(
        "ProcurementRequest", back_populates="user", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<User {self.email}>"