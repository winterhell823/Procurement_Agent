

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid

from models.base import get_db
from models.user import User
from models.procurement import ProcurementRequest, ProcurementStatus
from models.quote import Quote
from routes.auth import get_current_user
from services.reliability_service import get_all_scores, SupplierScore

router = APIRouter()


@router.get("/suppliers")
async def get_supplier_scores(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get reliability scores for all suppliers, sorted best first."""
    scores = await get_all_scores(db)
    return {
        "total": len(scores),
        "suppliers": scores
    }


@router.get("/summary")
async def get_user_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Summary stats for current user's procurement activity.
    Used for dashboard overview cards.
    """
    # Total requests
    total_result = await db.execute(
        select(func.count(ProcurementRequest.id)).where(
            ProcurementRequest.user_id == current_user.id
        )
    )
    total_requests = total_result.scalar() or 0

    # Completed requests
    completed_result = await db.execute(
        select(func.count(ProcurementRequest.id)).where(
            ProcurementRequest.user_id == current_user.id,
            ProcurementRequest.status == ProcurementStatus.COMPLETED
        )
    )
    completed = completed_result.scalar() or 0

    # Total quotes received
    quotes_result = await db.execute(
        select(func.count(Quote.id)).join(
            ProcurementRequest,
            Quote.procurement_request_id == ProcurementRequest.id
        ).where(
            ProcurementRequest.user_id == current_user.id
        )
    )
    total_quotes = quotes_result.scalar() or 0

    # Average quotes per request
    avg_quotes = round(total_quotes / completed, 1) if completed > 0 else 0

    # Best supplier (most recommended quotes)
    best_supplier_result = await db.execute(
        select(Quote.supplier_name, func.count(Quote.id).label("count"))
        .join(ProcurementRequest, Quote.procurement_request_id == ProcurementRequest.id)
        .where(
            ProcurementRequest.user_id == current_user.id,
            Quote.is_recommended == True
        )
        .group_by(Quote.supplier_name)
        .order_by(func.count(Quote.id).desc())
        .limit(1)
    )
    best_supplier_row = best_supplier_result.first()
    best_supplier = best_supplier_row[0] if best_supplier_row else "N/A"

    return {
        "total_requests":   total_requests,
        "completed":        completed,
        "total_quotes":     total_quotes,
        "avg_quotes":       avg_quotes,
        "best_supplier":    best_supplier,
        "success_rate":     round(completed / total_requests * 100, 1) if total_requests > 0 else 0
    }


@router.get("/validity")
async def get_quote_validity_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all active quote validity records for current user.
    Used to show which quotes are expiring soon.
    """
    from services.validity_service import QuoteValidity
    from datetime import datetime, timedelta

    result = await db.execute(
        select(QuoteValidity).where(
            QuoteValidity.user_id == current_user.id,
            QuoteValidity.is_expired == False
        ).order_by(QuoteValidity.expires_at)
    )
    records = result.scalars().all()

    return [
        {
            "id":             str(r.id),
            "supplier_name":  r.supplier_name,
            "expires_at":     r.expires_at.isoformat() if r.expires_at else None,
            "days_remaining": (r.expires_at - datetime.utcnow()).days if r.expires_at else None,
            "is_expiring_soon": (r.expires_at - datetime.utcnow()).days <= 7 if r.expires_at else False,
            "procurement_id": str(r.procurement_id)
        }
        for r in records
    ]