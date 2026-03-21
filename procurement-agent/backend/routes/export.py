from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from models.base import get_db
from models.user import User
from models.quote import Quote
from models.procurement import ProcurementRequest
from routes.auth import get_current_user
from services.export_service import generate_csv, generate_excel

router = APIRouter()


async def get_quotes_for_export(procurement_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession):
    """Shared helper — fetch quotes and verify ownership."""
    req_result = await db.execute(
        select(ProcurementRequest).where(
            ProcurementRequest.id == procurement_id,
            ProcurementRequest.user_id == user_id
        )
    )
    req = req_result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=404, detail="Procurement request not found")

    quotes_result = await db.execute(
        select(Quote)
        .where(Quote.procurement_request_id == procurement_id)
        .order_by(Quote.score.desc().nullslast())
    )
    quotes = quotes_result.scalars().all()

    return req, [
        {
            "supplier_name":    q.supplier_name,
            "supplier_url":     q.supplier_url,
            "unit_price":       q.unit_price,
            "total_price":      q.total_price,
            "currency":         q.currency,
            "delivery_days":    q.delivery_days,
            "minimum_order_qty":q.minimum_order_qty,
            "payment_terms":    q.payment_terms,
            "additional_notes": q.additional_notes,
            "score":            q.score,
            "is_recommended":   q.is_recommended,
            "status":           q.status,
            "fetched_at":       q.fetched_at.isoformat() if q.fetched_at else None
        }
        for q in quotes
    ]


@router.get("/csv/{procurement_id}")
async def export_csv(
    procurement_id: uuid.UUID,
    current_user:   User = Depends(get_current_user),
    db:             AsyncSession = Depends(get_db)
):
    """Download all quotes as CSV file."""
    req, quotes = await get_quotes_for_export(procurement_id, current_user.id, db)
    product_name = (req.parsed_spec or {}).get("product_name", req.raw_description[:50])

    csv_bytes = generate_csv(quotes, product_name)
    filename  = f"quotes_{product_name[:30].replace(' ', '_')}_{str(procurement_id)[:8]}.csv"

    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/excel/{procurement_id}")
async def export_excel(
    procurement_id: uuid.UUID,
    current_user:   User = Depends(get_current_user),
    db:             AsyncSession = Depends(get_db)
):
    """Download all quotes as Excel (.xlsx) file."""
    req, quotes = await get_quotes_for_export(procurement_id, current_user.id, db)
    product_name = (req.parsed_spec or {}).get("product_name", req.raw_description[:50])

    excel_bytes = generate_excel(quotes, product_name)
    filename    = f"quotes_{product_name[:30].replace(' ', '_')}_{str(procurement_id)[:8]}.xlsx"

    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )