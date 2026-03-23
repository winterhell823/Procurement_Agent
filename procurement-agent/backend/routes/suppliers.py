from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional, List
import uuid

from models.base import get_db
from models.user import User
from models.supplier import Supplier
from routes.auth import get_current_user

router = APIRouter()


# ── Schemas ───────────────────────────────────────────────────────────────────
class SupplierCreate(BaseModel):
    name:          str
    website:       Optional[str]       = None
    contact_email: Optional[str]       = None
    contact_phone: Optional[str]       = None
    categories:    Optional[List[str]] = None
    country:       Optional[str]       = None
    scrape_config: Optional[dict]      = None
    notes:         Optional[str]       = None


class SupplierOut(BaseModel):
    id:                    uuid.UUID
    name:                  str
    website:               Optional[str]
    contact_email:         Optional[str]
    contact_phone:         Optional[str]
    categories:            Optional[List[str]]
    country:               Optional[str]
    is_active:             bool
    is_verified:           bool
    reliability_score:     Optional[float]
    avg_lead_time_days:    Optional[int]
    total_quotes_received: int

    class Config:
        from_attributes = True


# ── Endpoints ─────────────────────────────────────────────────────────────────
@router.get("/", response_model=List[SupplierOut])
async def list_suppliers(
    category:     Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    q = select(Supplier).where(Supplier.is_active == True).order_by(Supplier.name)
    if category:
        q = q.where(Supplier.categories.contains([category]))
    result = await db.execute(q)
    return result.scalars().all()


@router.post("/", response_model=SupplierOut, status_code=201)
async def create_supplier(
    body:         SupplierCreate,
    current_user: User = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    supplier = Supplier(**body.model_dump())
    db.add(supplier)
    await db.commit()
    await db.refresh(supplier)
    return supplier


@router.get("/{supplier_id}", response_model=SupplierOut)
async def get_supplier(
    supplier_id:  uuid.UUID,
    current_user: User = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    return supplier


@router.patch("/{supplier_id}", response_model=SupplierOut)
async def update_supplier(
    supplier_id:  uuid.UUID,
    body:         SupplierCreate,
    current_user: User = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(404, "Supplier not found")

    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(supplier, k, v)

    await db.commit()
    await db.refresh(supplier)
    return supplier


@router.delete("/{supplier_id}", status_code=204)
async def delete_supplier(
    supplier_id:  uuid.UUID,
    current_user: User = Depends(get_current_user),
    db:           AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Supplier).where(Supplier.id == supplier_id))
    supplier = result.scalar_one_or_none()
    if not supplier:
        raise HTTPException(404, "Supplier not found")
    supplier.is_active = False   # soft delete
    await db.commit()