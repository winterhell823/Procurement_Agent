from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from models.base import Base


class Supplier(Base):
    __tablename__ = "suppliers"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name            = Column(String(255), nullable=False, index=True)
    website         = Column(String(500), nullable=True)
    contact_email   = Column(String(255), nullable=True)
    contact_phone   = Column(String(50),  nullable=True)

    # Classification
    categories      = Column(JSON,        nullable=True)   # ["IT Hardware", "Office Supplies"]
    country         = Column(String(100), nullable=True)

    # Agent config: tells browser agent how to interact with this supplier's site
    scrape_config   = Column(JSON, nullable=True)
    """
    {
      "quote_url":       "https://supplier.com/rfq",
      "form_selectors":  { "product": "#sku", "qty": "#qty", "submit": "#btn" },
      "result_selector": ".price-result",
      "requires_login":  false,
      "order_url":       "https://supplier.com/order"
    }
    """

    # Performance stats — updated by reliability_service
    reliability_score       = Column(Float,   nullable=True)   # 0–100
    avg_lead_time_days      = Column(Integer, nullable=True)
    avg_price_index         = Column(Float,   nullable=True)
    total_quotes_received   = Column(Integer, default=0)

    is_active   = Column(Boolean, default=True,  nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    notes       = Column(String(2000), nullable=True)

    created_at  = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self) -> str:
        return f"<Supplier {self.name}>"