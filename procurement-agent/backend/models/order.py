"""
models/order.py
────────────────────────────────────────────────────────────────────
Database model for orders placed with suppliers.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

from models.base import Base


class Order(Base):
    """
    Order record - tracks actual orders placed with suppliers.
    """
    
    __tablename__ = "orders"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    quote_id = Column(UUID(as_uuid=True), ForeignKey("quotes.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    
    # Order details
    order_number = Column(String(100))  # Supplier's order number
    po_number = Column(String(100))  # Our PO number
    order_method = Column(String(20))  # "portal" or "email"
    
    # Delivery
    expected_delivery = Column(String(50), nullable=True)
    actual_delivery = Column(DateTime, nullable=True)
    
    # URLs
    confirmation_url = Column(String(500), nullable=True)
    screenshot_url = Column(String(500), nullable=True)
    
    # Status tracking
    status = Column(String(20), default="placed")  # placed, confirmed, shipped, delivered, cancelled
    
    # Additional info
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    quote = relationship("Quote", back_populates="orders")
    user = relationship("User", back_populates="orders")
    
    def __repr__(self):
        return f"<Order {self.order_number} - {self.status}>"