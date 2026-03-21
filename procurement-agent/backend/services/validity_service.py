from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timedelta
import uuid
from models.base import Base
 
 
class QuoteValidity(Base):
    """
    Tracks validity/expiry of each quote.
    Created when a quote is received, updated by monitor_agent.
    """
    __tablename__ = "quote_validity"
 
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    quote_id        = Column(UUID(as_uuid=True), ForeignKey("quotes.id"), nullable=False)
    procurement_id  = Column(UUID(as_uuid=True), ForeignKey("procurement_requests.id"), nullable=False)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
 
    supplier_name   = Column(String(255))
    valid_days      = Column(Integer, default=30)       # how many days quote is valid
    expires_at      = Column(DateTime, nullable=True)   # calculated expiry date
    fetched_at      = Column(DateTime, default=datetime.utcnow)
 
    # Alert tracking
    alert_7day_sent  = Column(Boolean, default=False)   # 7 day warning sent?
    alert_1day_sent  = Column(Boolean, default=False)   # 1 day warning sent?
    is_expired       = Column(Boolean, default=False)
 
    created_at      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
 
 
# ── Validity Service Functions ─────────────────────────────────────────────────
 
def calculate_expiry(fetched_at: datetime, valid_days: int = 30) -> datetime:
    """Calculate when a quote expires."""
    return fetched_at + timedelta(days=valid_days)
 
def days_until_expiry(expires_at: datetime) -> int:
    """How many days until this quote expires."""
    delta = expires_at - datetime.utcnow()
    return max(0, delta.days)
 
def is_expiring_soon(expires_at: datetime, threshold_days: int = 7) -> bool:
    """Returns True if quote expires within threshold_days."""
    return days_until_expiry(expires_at) <= threshold_days
 
async def create_validity_record(
    quote_id: uuid.UUID,
    procurement_id: uuid.UUID,
    user_id: uuid.UUID,
    supplier_name: str,
    valid_days: int = 30,
    db=None
) -> QuoteValidity:
    """Create a validity tracking record when a quote is received."""
    fetched_at = datetime.utcnow()
    record = QuoteValidity(
        quote_id        = quote_id,
        procurement_id  = procurement_id,
        user_id         = user_id,
        supplier_name   = supplier_name,
        valid_days      = valid_days,
        fetched_at      = fetched_at,
        expires_at      = calculate_expiry(fetched_at, valid_days)
    )
    if db:
        db.add(record)
        await db.commit()
        await db.refresh(record)
    return record
 
async def get_expiring_quotes(db, days_threshold: int = 7) -> list:
    """
    Get all quotes expiring within threshold days.
    Called by the scheduler every morning.
    """
    from sqlalchemy import select
    cutoff = datetime.utcnow() + timedelta(days=days_threshold)
 
    result = await db.execute(
        select(QuoteValidity).where(
            QuoteValidity.expires_at <= cutoff,
            QuoteValidity.is_expired == False,
            QuoteValidity.alert_7day_sent == False
        )
    )
    return result.scalars().all()