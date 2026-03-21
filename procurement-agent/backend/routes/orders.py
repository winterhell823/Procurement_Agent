from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, colum, String, DateTime, Float, ForeignKey, JSON
from pydantic import BAseModel
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from typing import Optional
import uuid

from models.base import get_db, Base
from models.user import User
from models.quote import Quote
from models.procurement import ProcurementRequest
from routes.auth import get_current_user
from agents.order_agent import run_order_agent

router = APIRouter()

#--Order DB Model-------------------

class Order(Base):
    __tablename__ = "orders"
 
    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id             = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    quote_id            = Column(UUID(as_uuid=True), ForeignKey("quotes.id"), nullable=False)
    procurement_id      = Column(UUID(as_uuid=True), ForeignKey("procurement_requests.id"), nullable=False)
    supplier_name       = Column(String(255))
    supplier_url        = Column(String(500))
    order_id            = Column(String(255))        # supplier's order/confirmation number
    invoice_number      = Column(String(255))
    total_amount        = Column(Float)
    estimated_delivery  = Column(String(255))
    status              = Column(String(50), default="placing")
    raw                 = Column(JSON)
    placed_at           = Column(DateTime, default=datetime.utcnow)
    created_at          = Column(DateTime, default=datetime.utcnow)

#---Schemas---------------------------------

class PlaceOrderRequest(BaseModel):
    quote_id: uuid.UUID
    quantity: Optional[int] = None

#-------Routes---------------------------------

@router.post("/place")
async def place_order(
    body:             PlaceOrderRequest,
    background_tasks: BackgroundTasks,
    current_user:     User = Depends(get_current_user),
    db:               AsyncSession = Depends(get_db)
):
    """
    Place an order for the selected quote.
    Agent navigates supplier site and places the order.
    """
    # Get quote
    q_result = await db.execute(
        select(Quote).where(Quote.id == body.quote_id)
    )
    quote = q_result.scalar_one_or_none()
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
 
    # Get procurement request for product spec
    pr_result = await db.execute(
        select(ProcurementRequest).where(
            ProcurementRequest.id == quote.procurement_request_id,
            ProcurementRequest.user_id == current_user.id
        )
    )
    req = pr_result.scalar_one_or_none()
    if not req:
        raise HTTPException(status_code=403, detail="Not authorized")
 
    # Create order record
    order = Order(
        user_id=current_user.id,
        quote_id=quote.id,
        procurement_id=req.id,
        supplier_name=quote.supplier_name,
        supplier_url=quote.supplier_url,
        status="placing"
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
 
    company_profile = {
        "company_name":   current_user.company_name,
        "contact_person": current_user.contact_person,
        "email":          current_user.email,
        "phone":          current_user.company_phone,
        "address":        current_user.company_address,
        "payment_terms":  current_user.payment_terms,
        "gst_number":     current_user.gst_number
    }
 
    product_spec = req.parsed_spec or {"product_name": req.raw_description}
    product_spec["expected_unit_price"] = quote.unit_price
 
    async def run_and_save():
        result = await run_order_agent(
            supplier_url=quote.supplier_url,
            supplier_name=quote.supplier_name,
            quote_ref_id=(quote.raw_extracted_data or {}).get("reference_id"),
            product_spec=product_spec,
            company_profile=company_profile,
            quantity=body.quantity or req.quantity or 1
        )
        # Update order record
        order.order_id           = result.get("order_id")
        order.invoice_number     = result.get("invoice_number")
        order.total_amount       = result.get("total_amount")
        order.estimated_delivery = result.get("estimated_delivery")
        order.status             = result.get("status", "failed")
        order.raw                = result
        order.placed_at          = datetime.utcnow()
        await db.commit()
 
    background_tasks.add_task(run_and_save)
 
    return {
        "order_db_id": str(order.id),
        "status":      "placing",
        "message":     "Order agent started. Check status at /orders/" + str(order.id)
    }
 
 
@router.get("/")
async def list_orders(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Order).where(Order.user_id == current_user.id)
        .order_by(Order.created_at.desc())
    )
    orders = result.scalars().all()
    return [
        {
            "id":                str(o.id),
            "supplier_name":     o.supplier_name,
            "order_id":          o.order_id,
            "total_amount":      o.total_amount,
            "estimated_delivery":o.estimated_delivery,
            "status":            o.status,
            "placed_at":         o.placed_at.isoformat() if o.placed_at else None
        }
        for o in orders
    ]
 
 
@router.get("/{order_id}")
async def get_order(
    order_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Order).where(
            Order.id == order_id,
            Order.user_id == current_user.id
        )
    )
    order = result.scalar_one_or_none()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
 
    return {
        "id":                str(order.id),
        "supplier_name":     order.supplier_name,
        "supplier_url":      order.supplier_url,
        "order_id":          order.order_id,
        "invoice_number":    order.invoice_number,
        "total_amount":      order.total_amount,
        "estimated_delivery":order.estimated_delivery,
        "status":            order.status,
        "raw":               order.raw,
        "placed_at":         order.placed_at.isoformat() if order.placed_at else None
    }
   

