from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import uuid

from models.base import get_db
from models.user import User
from models.quote import Quote
from models.procurement import ProcurementRequest
from routes.auth import get_current_user

router = APIRouter()


# ── Helpers ───────────────────────────────────────────────────────────────────
def _fmt(q: Quote) -> dict:
    return {
        "id":                     str(q.id),
        "procurement_request_id": str(q.procurement_request_id),
        "supplier_name":          q.supplier_name,
        "supplier_url":           q.supplier_url,
        "unit_price":             q.unit_price,
        "total_price":            q.total_price,
        "currency":               q.currency,
        "minimum_order_qty":      q.minimum_order_qty,
        "delivery_days":          q.delivery_days,
        "payment_terms":          q.payment_terms,
        "additional_notes":       q.additional_notes,
        "score":                  q.score,
        "is_recommended":         q.is_recommended,
        "status":                 q.status,
        "fetched_at":             q.fetched_at.isoformat() if q.fetched_at else None,
        "created_at":             q.created_at.isoformat(),
    }


async def _verify_ownership(
    procurement_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> ProcurementRequest:
    """Raise 404 if procurement doesn't exist or doesn't belong to this user."""
    result = await db.execute(
        select(ProcurementRequest).where(
            ProcurementRequest.id == procurement_id,
            ProcurementRequest.user_id == user_id,
        )
    )
    req = result.scalar_one_or_none()
    if not req:
        raise HTTPException(404, "Procurement request not found")
    return req


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/{procurement_id}")
async def list_quotes(
    procurement_id: uuid.UUID,
    current_user:   User = Depends(get_current_user),
    db:             AsyncSession = Depends(get_db),
):
    """Return all quotes for a procurement, ranked by score."""
    await _verify_ownership(procurement_id, current_user.id, db)

    result = await db.execute(
        select(Quote)
        .where(Quote.procurement_request_id == procurement_id)
        .order_by(Quote.score.desc().nullslast())
    )
    quotes = result.scalars().all()
    return [_fmt(q) for q in quotes]


@router.get("/{procurement_id}/recommended")
async def get_recommended_quote(
    procurement_id: uuid.UUID,
    current_user:   User = Depends(get_current_user),
    db:             AsyncSession = Depends(get_db),
):
    """Return the single AI-recommended quote for a procurement."""
    await _verify_ownership(procurement_id, current_user.id, db)

    result = await db.execute(
        select(Quote).where(
            Quote.procurement_request_id == procurement_id,
            Quote.is_recommended == True,
        )
    )
    quote = result.scalar_one_or_none()
    if not quote:
        raise HTTPException(404, "No recommended quote found yet")
    return _fmt(quote)


@router.post("/{quote_id}/select")
async def select_quote(
    quote_id:     uuid.UUID,
    current_user: User = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    """Mark a quote as selected; deselect all siblings."""
    result = await db.execute(select(Quote).where(Quote.id == quote_id))
    quote = result.scalar_one_or_none()
    if not quote:
        raise HTTPException(404, "Quote not found")

    # Verify ownership via procurement
    await _verify_ownership(quote.procurement_request_id, current_user.id, db)

    # Deselect siblings
    siblings_result = await db.execute(
        select(Quote).where(
            Quote.procurement_request_id == quote.procurement_request_id,
            Quote.id != quote_id,
        )
    )
    for sibling in siblings_result.scalars().all():
        sibling.status = "rejected"
        sibling.is_recommended = False

    quote.status = "selected"
    quote.is_recommended = True
    await db.commit()
    return {"selected_quote_id": str(quote_id)}


@router.get("/{procurement_id}/compare")
async def compare_quotes(
    procurement_id: uuid.UUID,
    current_user:   User = Depends(get_current_user),
    db:             AsyncSession = Depends(get_db),
):
    """Return quotes with a side-by-side comparison summary."""
    await _verify_ownership(procurement_id, current_user.id, db)

    result = await db.execute(
        select(Quote)
        .where(
            Quote.procurement_request_id == procurement_id,
            Quote.status.in_(["received", "selected"]),
        )
        .order_by(Quote.score.desc().nullslast())
    )
    quotes = result.scalars().all()
    if not quotes:
        raise HTTPException(404, "No quotes available for comparison")

    best = min((q for q in quotes if q.total_price), key=lambda q: q.total_price, default=None)

    return {
        "procurement_id": str(procurement_id),
        "total_quotes":   len(quotes),
        "best_price_id":  str(best.id) if best else None,
        "top_scored_id":  str(quotes[0].id) if quotes else None,
        "quotes":         [_fmt(q) for q in quotes],
    }