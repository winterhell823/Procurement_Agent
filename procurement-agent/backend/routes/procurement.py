from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import uuid

from models.base import get_db
from models.user import User
from models.procurement import ProcurementRequest, ProcurementStatus
from routes.auth import get_current_user
from agents.orchestrator import run_procurement_pipeline

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────
class ProcurementCreate(BaseModel):
    raw_description: str
    quantity:        Optional[int]   = None
    budget:          Optional[float] = None
    currency:        str             = "USD"
    category:        Optional[str]   = None


class ProcurementOut(BaseModel):
    id:              uuid.UUID
    raw_description: str
    product_name:    Optional[str]
    quantity:        Optional[int]
    budget:          Optional[float]
    currency:        str
    category:        Optional[str]
    status:          ProcurementStatus
    parsed_spec:     Optional[dict]
    notes:           Optional[str]
    created_at:      str
    logs:            list = []

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_fmt(cls, p: ProcurementRequest):
        return cls(
            id=p.id,
            raw_description=p.raw_description,
            product_name=p.product_name,
            quantity=p.quantity,
            budget=p.budget,
            currency=p.currency,
            category=p.category,
            status=p.status,
            parsed_spec=p.parsed_spec,
            notes=p.notes,
            created_at=p.created_at.isoformat(),
            logs=p.agent_logs or []
        )


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.post("/", status_code=201)
async def create_procurement(
    body:             ProcurementCreate,
    background_tasks: BackgroundTasks,
    current_user:     User = Depends(get_current_user),
    db:               AsyncSession = Depends(get_db),
):
    """
    Submit a new procurement request.
    Immediately kicks off the AI pipeline in the background.
    """
    proc = ProcurementRequest(
        user_id=current_user.id,
        raw_description=body.raw_description,
        quantity=body.quantity,
        budget=body.budget,
        currency=body.currency,
        category=body.category,
        status=ProcurementStatus.PENDING,
    )
    db.add(proc)
    await db.commit()
    await db.refresh(proc)

    # Fire AI pipeline asynchronously
    background_tasks.add_task(
        run_procurement_pipeline,
        proc.id,
        body.raw_description,
        current_user.id,
        None,
    )

    return ProcurementOut.from_orm_fmt(proc)


@router.get("/")
async def list_procurements(
    status:       Optional[ProcurementStatus] = None,
    current_user: User = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    q = (
        select(ProcurementRequest)
        .where(ProcurementRequest.user_id == current_user.id)
        .order_by(ProcurementRequest.created_at.desc())
    )
    if status:
        q = q.where(ProcurementRequest.status == status)
    result = await db.execute(q)
    procs = result.scalars().all()
    return [ProcurementOut.from_orm_fmt(p) for p in procs]


@router.get("/{proc_id}")
async def get_procurement(
    proc_id:      uuid.UUID,
    current_user: User = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProcurementRequest).where(
            ProcurementRequest.id == proc_id,
            ProcurementRequest.user_id == current_user.id,
        )
    )
    proc = result.scalar_one_or_none()
    if not proc:
        raise HTTPException(404, "Procurement request not found")
    return ProcurementOut.from_orm_fmt(proc)


@router.patch("/{proc_id}/cancel")
async def cancel_procurement(
    proc_id:      uuid.UUID,
    current_user: User = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProcurementRequest).where(
            ProcurementRequest.id == proc_id,
            ProcurementRequest.user_id == current_user.id,
        )
    )
    proc = result.scalar_one_or_none()
    if not proc:
        raise HTTPException(404, "Procurement request not found")
    if proc.status == ProcurementStatus.COMPLETED:
        raise HTTPException(400, "Cannot cancel a completed request")

    proc.status = ProcurementStatus.CANCELLED
    await db.commit()
    return {"id": proc_id, "status": ProcurementStatus.CANCELLED}


@router.delete("/{proc_id}", status_code=204)
async def delete_procurement(
    proc_id:      uuid.UUID,
    current_user: User = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ProcurementRequest).where(
            ProcurementRequest.id == proc_id,
            ProcurementRequest.user_id == current_user.id,
        )
    )
    proc = result.scalar_one_or_none()
    if not proc:
        raise HTTPException(404, "Procurement request not found")
    await db.delete(proc)
    await db.commit()