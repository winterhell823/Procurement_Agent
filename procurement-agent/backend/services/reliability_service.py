from sqlalchemy import Column, Float, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from models.base import Base
 
 
class SupplierScore(Base):
    """
    Tracks reliability metrics per supplier per user.
    Updated after each procurement job.
    """
    __tablename__ = "supplier_scores"
 
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    supplier_name   = Column(String(255), nullable=False, index=True)
    supplier_url    = Column(String(500), nullable=False)
    user_id         = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    # user_id = None means global score across all users
 
    # Raw counters
    total_attempts      = Column(Integer, default=0)   # times agent tried this supplier
    successful_quotes   = Column(Integer, default=0)   # times got a valid quote back
    failed_attempts     = Column(Integer, default=0)   # times agent failed
    orders_placed       = Column(Integer, default=0)   # times order was placed
    orders_fulfilled    = Column(Integer, default=0)   # times order was delivered ok
 
    # Average metrics
    avg_response_time_s = Column(Float, default=0.0)   # avg seconds to get quote
    avg_delivery_days   = Column(Float, default=0.0)   # avg actual delivery
    price_accuracy      = Column(Float, default=0.0)   # how close quote was to final price %
 
    # Computed score 0-100
    reliability_score   = Column(Float, default=50.0)
 
    last_updated        = Column(DateTime, default=datetime.utcnow)
    created_at          = Column(DateTime, default=datetime.utcnow)
 
 
# ── Scoring Functions ──────────────────────────────────────────────────────────
 
def compute_reliability_score(record: SupplierScore) -> float:
    """
    Compute reliability score 0-100 from raw counters.
 
    Formula:
    - Response rate (40%):   successful / total attempts
    - Order fulfillment (30%): fulfilled / placed
    - Speed (20%):           based on avg_response_time
    - Price accuracy (10%):  how accurate was the quoted price
    """
    if record.total_attempts == 0:
        return 50.0  # neutral for new suppliers
 
    # Response rate (0-40)
    response_rate  = record.successful_quotes / record.total_attempts
    response_score = response_rate * 40
 
    # Order fulfillment (0-30)
    if record.orders_placed > 0:
        fulfillment_rate  = record.orders_fulfilled / record.orders_placed
        fulfillment_score = fulfillment_rate * 30
    else:
        fulfillment_score = 15  # neutral if no orders yet
 
    # Speed score (0-20) — faster is better
    # Under 30s = 20, 30-60s = 15, 60-120s = 10, over 120s = 5
    t = record.avg_response_time_s
    if t <= 30:    speed_score = 20
    elif t <= 60:  speed_score = 15
    elif t <= 120: speed_score = 10
    else:          speed_score = 5
 
    # Price accuracy (0-10)
    # 95-100% accurate = 10, 90-95% = 7, below 90% = 3
    acc = record.price_accuracy
    if acc >= 95:   accuracy_score = 10
    elif acc >= 90: accuracy_score = 7
    else:           accuracy_score = 3
 
    total = response_score + fulfillment_score + speed_score + accuracy_score
    return round(min(max(total, 0), 100), 1)
 
 
async def record_quote_attempt(
    supplier_name: str,
    supplier_url:  str,
    success:       bool,
    response_time_s: float = 0,
    db=None
):
    """
    Called by supplier_agent after each attempt.
    Updates the supplier's score record.
    """
    if not db:
        return
 
    from sqlalchemy import select
    result = await db.execute(
        select(SupplierScore).where(
            SupplierScore.supplier_name == supplier_name,
            SupplierScore.user_id == None  # global score
        )
    )
    record = result.scalar_one_or_none()
 
    if not record:
        record = SupplierScore(
            supplier_name=supplier_name,
            supplier_url=supplier_url
        )
        db.add(record)
 
    record.total_attempts += 1
    if success:
        record.successful_quotes += 1
    else:
        record.failed_attempts += 1
 
    # Update rolling average response time
    if response_time_s > 0:
        total = record.avg_response_time_s * (record.total_attempts - 1)
        record.avg_response_time_s = (total + response_time_s) / record.total_attempts
 
    record.reliability_score = compute_reliability_score(record)
    record.last_updated = datetime.utcnow()
 
    await db.commit()
    return record
 
 
async def get_supplier_score(supplier_name: str, db) -> float:
    """Get reliability score for a supplier. Returns 50.0 if unknown."""
    from sqlalchemy import select
    result = await db.execute(
        select(SupplierScore).where(
            SupplierScore.supplier_name == supplier_name
        )
    )
    record = result.scalar_one_or_none()
    return record.reliability_score if record else 50.0
 
 
async def get_all_scores(db) -> list:
    """Get all supplier scores sorted by reliability."""
    from sqlalchemy import select
    result = await db.execute(
        select(SupplierScore).order_by(SupplierScore.reliability_score.desc())
    )
    records = result.scalars().all()
    return [
        {
            "supplier_name":      r.supplier_name,
            "supplier_url":       r.supplier_url,
            "reliability_score":  r.reliability_score,
            "total_attempts":     r.total_attempts,
            "successful_quotes":  r.successful_quotes,
            "response_rate":      round(r.successful_quotes / r.total_attempts * 100, 1) if r.total_attempts else 0,
            "avg_response_time_s":round(r.avg_response_time_s, 1),
            "last_updated":       r.last_updated.isoformat()
        }
        for r in records
    ]