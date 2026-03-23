"""
services/db_service.py
────────────────────────────────────────────────────────────────────
Database service layer - abstracts all database operations.

Provides clean functions for CRUD operations on all models.
Handles transactions, error handling, and session management.
"""

import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, func
from sqlalchemy.exc import SQLAlchemyError


# ─────────────────────────────────────────────────────────────────────
# PROCUREMENT OPERATIONS
# ─────────────────────────────────────────────────────────────────────

async def create_procurement_request(
    user_id: uuid.UUID,
    product_spec_raw: str,
    product_spec_parsed: Dict,
    db: AsyncSession
) -> Any:
    """
    Create a new procurement request.
    
    Args:
        user_id: User creating the request
        product_spec_raw: Original user input
        product_spec_parsed: Parsed structured data
        db: Database session
    
    Returns:
        Procurement object
    """
    try:
        from models.procurement import ProcurementRequest, ProcurementStatus
        
        procurement = ProcurementRequest(
            id=uuid.uuid4(),
            user_id=user_id,
            product_spec_raw=product_spec_raw,
            product_spec_parsed=product_spec_parsed,
            status=ProcurementStatus.PENDING,
            total_suppliers=0,
            completed_suppliers=0,
            quotes_received=0,
            created_at=datetime.utcnow()
        )
        
        db.add(procurement)
        await db.commit()
        await db.refresh(procurement)
        
        return procurement
    
    except Exception as e:
        await db.rollback()
        raise Exception(f"Failed to create procurement request: {str(e)}")


async def update_procurement_status(
    procurement_id: uuid.UUID,
    status: str,
    message: Optional[str] = None,
    db: Optional[AsyncSession] = None
):
    """
    Update procurement request status.
    
    Args:
        procurement_id: Procurement request ID
        status: New status (e.g., "RUNNING", "COMPLETED", "FAILED")
        message: Optional status message
        db: Database session
    """
    try:
        from models.procurement import ProcurementRequest
        
        stmt = (
            update(ProcurementRequest)
            .where(ProcurementRequest.id == procurement_id)
            .values(
                status=status,
                status_message=message,
                updated_at=datetime.utcnow()
            )
        )
        
        await db.execute(stmt)
        await db.commit()
    
    except Exception as e:
        await db.rollback()
        print(f"Error updating procurement status: {str(e)}")


async def update_procurement_progress(
    procurement_id: uuid.UUID,
    completed_suppliers: int,
    quotes_received: int,
    db: AsyncSession
):
    """
    Update procurement progress counters.
    
    Args:
        procurement_id: Procurement request ID
        completed_suppliers: Number of suppliers completed
        quotes_received: Number of quotes received
        db: Database session
    """
    try:
        from models.procurement import ProcurementRequest
        
        stmt = (
            update(ProcurementRequest)
            .where(ProcurementRequest.id == procurement_id)
            .values(
                completed_suppliers=completed_suppliers,
                quotes_received=quotes_received,
                updated_at=datetime.utcnow()
            )
        )
        
        await db.execute(stmt)
        await db.commit()
    
    except Exception as e:
        await db.rollback()
        print(f"Error updating procurement progress: {str(e)}")


async def get_procurement_request(
    procurement_id: uuid.UUID,
    db: AsyncSession
) -> Optional[Any]:
    """
    Get procurement request by ID.
    
    Args:
        procurement_id: Procurement request ID
        db: Database session
    
    Returns:
        ProcurementRequest object or None
    """
    try:
        from models.procurement import ProcurementRequest
        
        stmt = select(ProcurementRequest).where(
            ProcurementRequest.id == procurement_id
        )
        
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    except Exception as e:
        print(f"Error fetching procurement request: {str(e)}")
        return None


async def append_agent_log(
    procurement_id: uuid.UUID,
    message: str,
    db: AsyncSession
):
    """
    Append a log message to procurement request.
    
    Args:
        procurement_id: Procurement request ID
        message: Log message
        db: Database session
    """
    try:
        from models.procurement import ProcurementRequest
        
        # Get current procurement
        procurement = await get_procurement_request(procurement_id, db)
        
        if procurement:
            # Get existing logs or initialize empty list
            logs = procurement.agent_logs or []
            
            # Append new log entry
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "message": message
            }
            logs.append(log_entry)
            
            # Update procurement
            stmt = (
                update(ProcurementRequest)
                .where(ProcurementRequest.id == procurement_id)
                .values(agent_logs=logs)
            )
            
            await db.execute(stmt)
            await db.commit()
    
    except Exception as e:
        await db.rollback()
        print(f"Error appending agent log: {str(e)}")


# ─────────────────────────────────────────────────────────────────────
# QUOTE OPERATIONS
# ─────────────────────────────────────────────────────────────────────

async def save_quote(
    procurement_id: uuid.UUID,
    quote_data: Dict,
    db: AsyncSession
) -> Any:
    """
    Save a quote to database.
    
    Args:
        procurement_id: Associated procurement request ID
        quote_data: Quote data dictionary
        db: Database session
    
    Returns:
        Quote object
    """
    try:
        from models.quote import Quote
        
        quote = Quote(
            id=uuid.uuid4(),
            procurement_id=procurement_id,
            supplier_name=quote_data.get("supplier_name", ""),
            supplier_url=quote_data.get("supplier_url", ""),
            
            price_per_unit=quote_data.get("price_per_unit", 0),
            quantity=quote_data.get("quantity", 0),
            total_price=quote_data.get("total_price", 0),
            currency=quote_data.get("currency", "USD"),
            
            # INR conversions (if present)
            inr_unit_price=quote_data.get("inr_unit_price"),
            inr_total_price=quote_data.get("inr_total_price"),
            
            delivery_days=quote_data.get("delivery_days", 0),
            estimated_delivery=quote_data.get("estimated_delivery"),
            
            quote_url=quote_data.get("quote_url", ""),
            quote_reference=quote_data.get("quote_reference", ""),
            quote_pdf_url=quote_data.get("quote_pdf_url"),
            screenshot_url=quote_data.get("screenshot_url", ""),
            
            raw_data=quote_data.get("raw_data", {}),
            extraction_method=quote_data.get("extraction_method", "tinyfish"),
            
            status=quote_data.get("status", "received"),
            
            created_at=datetime.utcnow()
        )
        
        db.add(quote)
        await db.commit()
        await db.refresh(quote)
        
        return quote
    
    except Exception as e:
        await db.rollback()
        raise Exception(f"Failed to save quote: {str(e)}")


async def get_quote_by_id(
    quote_id: uuid.UUID,
    db: AsyncSession
) -> Optional[Any]:
    """
    Get quote by ID.
    
    Args:
        quote_id: Quote ID
        db: Database session
    
    Returns:
        Quote object or None
    """
    try:
        from models.quote import Quote
        
        stmt = select(Quote).where(Quote.id == quote_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    except Exception as e:
        print(f"Error fetching quote: {str(e)}")
        return None


async def get_quotes_by_procurement(
    procurement_id: uuid.UUID,
    db: AsyncSession
) -> List[Any]:
    """
    Get all quotes for a procurement request.
    
    Args:
        procurement_id: Procurement request ID
        db: Database session
    
    Returns:
        List of Quote objects
    """
    try:
        from models.quote import Quote
        
        stmt = select(Quote).where(
            Quote.procurement_id == procurement_id
        ).order_by(Quote.created_at.desc())
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    except Exception as e:
        print(f"Error fetching quotes: {str(e)}")
        return []


async def update_quote_status(
    quote_id: uuid.UUID,
    status: str,
    db: AsyncSession
):
    """
    Update quote status.
    
    Args:
        quote_id: Quote ID
        status: New status
        db: Database session
    """
    try:
        from models.quote import Quote
        
        stmt = (
            update(Quote)
            .where(Quote.id == quote_id)
            .values(
                status=status,
                updated_at=datetime.utcnow()
            )
        )
        
        await db.execute(stmt)
        await db.commit()
    
    except Exception as e:
        await db.rollback()
        print(f"Error updating quote status: {str(e)}")


async def delete_quote(
    quote_id: uuid.UUID,
    db: AsyncSession
):
    """
    Soft delete a quote.
    
    Args:
        quote_id: Quote ID
        db: Database session
    """
    try:
        from models.quote import Quote
        
        stmt = (
            update(Quote)
            .where(Quote.id == quote_id)
            .values(
                status="deleted",
                updated_at=datetime.utcnow()
            )
        )
        
        await db.execute(stmt)
        await db.commit()
    
    except Exception as e:
        await db.rollback()
        print(f"Error deleting quote: {str(e)}")


# ─────────────────────────────────────────────────────────────────────
# SUPPLIER OPERATIONS
# ─────────────────────────────────────────────────────────────────────

async def get_supplier_by_name(
    name: str,
    db: AsyncSession
) -> Optional[Any]:
    """
    Get supplier by name.
    
    Args:
        name: Supplier name
        db: Database session
    
    Returns:
        Supplier object or None
    """
    try:
        from models.supplier import Supplier
        
        stmt = select(Supplier).where(Supplier.name == name)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    except Exception as e:
        print(f"Error fetching supplier: {str(e)}")
        return None


async def get_all_suppliers(
    db: AsyncSession,
    enabled_only: bool = True
) -> List[Any]:
    """
    Get all suppliers.
    
    Args:
        db: Database session
        enabled_only: Only return enabled suppliers
    
    Returns:
        List of Supplier objects
    """
    try:
        from models.supplier import Supplier
        
        stmt = select(Supplier)
        
        if enabled_only:
            stmt = stmt.where(Supplier.enabled == True)
        
        stmt = stmt.order_by(Supplier.name)
        
        result = await db.execute(stmt)
        return list(result.scalars().all())
    
    except Exception as e:
        print(f"Error fetching suppliers: {str(e)}")
        return []


async def create_supplier(
    supplier_data: Dict,
    db: AsyncSession
) -> Any:
    """
    Create a new supplier.
    
    Args:
        supplier_data: Supplier data dictionary
        db: Database session
    
    Returns:
        Supplier object
    """
    try:
        from models.supplier import Supplier
        
        supplier = Supplier(
            id=uuid.uuid4(),
            name=supplier_data["name"],
            website_url=supplier_data["website_url"],
            quote_form_url=supplier_data.get("quote_form_url", supplier_data["website_url"]),
            
            requires_login=supplier_data.get("requires_login", False),
            login_url=supplier_data.get("login_url"),
            login_credentials=supplier_data.get("credentials"),
            
            supported_categories=supplier_data.get("supported_categories", []),
            enabled=supplier_data.get("enabled", True),
            is_system_supplier=supplier_data.get("is_system_supplier", True),
            
            user_id=supplier_data.get("user_id"),
            
            created_at=datetime.utcnow()
        )
        
        db.add(supplier)
        await db.commit()
        await db.refresh(supplier)
        
        return supplier
    
    except Exception as e:
        await db.rollback()
        raise Exception(f"Failed to create supplier: {str(e)}")


async def update_supplier(
    supplier_id: uuid.UUID,
    updates: Dict,
    db: AsyncSession
):
    """
    Update supplier information.
    
    Args:
        supplier_id: Supplier ID
        updates: Dictionary of fields to update
        db: Database session
    """
    try:
        from models.supplier import Supplier
        
        stmt = (
            update(Supplier)
            .where(Supplier.id == supplier_id)
            .values(**updates)
        )
        
        await db.execute(stmt)
        await db.commit()
    
    except Exception as e:
        await db.rollback()
        print(f"Error updating supplier: {str(e)}")


# ─────────────────────────────────────────────────────────────────────
# USER OPERATIONS
# ─────────────────────────────────────────────────────────────────────

async def get_user_by_id(
    user_id: uuid.UUID,
    db: AsyncSession
) -> Optional[Any]:
    """
    Get user by ID.
    
    Args:
        user_id: User ID
        db: Database session
    
    Returns:
        User object or None
    """
    try:
        from models.user import User
        
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    except Exception as e:
        print(f"Error fetching user: {str(e)}")
        return None


async def get_user_by_email(
    email: str,
    db: AsyncSession
) -> Optional[Any]:
    """
    Get user by email.
    
    Args:
        email: User email
        db: Database session
    
    Returns:
        User object or None
    """
    try:
        from models.user import User
        
        stmt = select(User).where(User.email == email)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    except Exception as e:
        print(f"Error fetching user by email: {str(e)}")
        return None


async def create_user(
    user_data: Dict,
    db: AsyncSession
) -> Any:
    """
    Create a new user.
    
    Args:
        user_data: User data dictionary
        db: Database session
    
    Returns:
        User object
    """
    try:
        from models.user import User
        
        user = User(
            id=uuid.uuid4(),
            email=user_data["email"],
            hashed_password=user_data["hashed_password"],
            full_name=user_data.get("full_name"),
            company_name=user_data.get("company_name"),
            company_phone=user_data.get("company_phone"),
            company_address=user_data.get("company_address"),
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    except Exception as e:
        await db.rollback()
        raise Exception(f"Failed to create user: {str(e)}")


async def update_user(
    user_id: uuid.UUID,
    updates: Dict,
    db: AsyncSession
):
    """
    Update user information.
    
    Args:
        user_id: User ID
        updates: Dictionary of fields to update
        db: Database session
    """
    try:
        from models.user import User
        
        stmt = (
            update(User)
            .where(User.id == user_id)
            .values(**updates)
        )
        
        await db.execute(stmt)
        await db.commit()
    
    except Exception as e:
        await db.rollback()
        print(f"Error updating user: {str(e)}")


# ─────────────────────────────────────────────────────────────────────
# ORDER OPERATIONS
# ─────────────────────────────────────────────────────────────────────

async def create_order(
    order_data: Dict,
    db: AsyncSession
) -> Any:
    """
    Create a new order.
    
    Args:
        order_data: Order data dictionary
        db: Database session
    
    Returns:
        Order object
    """
    try:
        from models.order import Order
        
        order = Order(
            id=uuid.uuid4(),
            quote_id=order_data["quote_id"],
            user_id=order_data["user_id"],
            
            order_number=order_data.get("order_number", ""),
            po_number=order_data.get("po_number", ""),
            order_method=order_data.get("order_method", "portal"),
            
            expected_delivery=order_data.get("expected_delivery"),
            confirmation_url=order_data.get("confirmation_url", ""),
            screenshot_url=order_data.get("screenshot_url", ""),
            
            status="placed",
            notes=order_data.get("notes"),
            
            created_at=datetime.utcnow()
        )
        
        db.add(order)
        await db.commit()
        await db.refresh(order)
        
        return order
    
    except Exception as e:
        await db.rollback()
        raise Exception(f"Failed to create order: {str(e)}")


async def get_order_by_id(
    order_id: uuid.UUID,
    db: AsyncSession
) -> Optional[Any]:
    """
    Get order by ID.
    
    Args:
        order_id: Order ID
        db: Database session
    
    Returns:
        Order object or None
    """
    try:
        from models.order import Order
        
        stmt = select(Order).where(Order.id == order_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    except Exception as e:
        print(f"Error fetching order: {str(e)}")
        return None


async def update_order_status(
    order_id: uuid.UUID,
    status: str,
    db: AsyncSession
):
    """
    Update order status.
    
    Args:
        order_id: Order ID
        status: New status
        db: Database session
    """
    try:
        from models.order import Order
        
        stmt = (
            update(Order)
            .where(Order.id == order_id)
            .values(
                status=status,
                updated_at=datetime.utcnow()
            )
        )
        
        await db.execute(stmt)
        await db.commit()
    
    except Exception as e:
        await db.rollback()
        print(f"Error updating order status: {str(e)}")


# ─────────────────────────────────────────────────────────────────────
# STATISTICS & ANALYTICS
# ─────────────────────────────────────────────────────────────────────

async def get_user_stats(
    user_id: uuid.UUID,
    db: AsyncSession
) -> Dict:
    """
    Get statistics for a user.
    
    Returns:
        {
            "total_procurements": int,
            "total_quotes": int,
            "total_orders": int,
            "avg_quotes_per_request": float,
            "total_savings": float
        }
    """
    try:
        from models.procurement import ProcurementRequest
        from models.quote import Quote
        from models.order import Order
        
        # Count procurements
        proc_stmt = select(func.count(ProcurementRequest.id)).where(
            ProcurementRequest.user_id == user_id
        )
        proc_result = await db.execute(proc_stmt)
        total_procurements = proc_result.scalar()
        
        # Count quotes
        quote_stmt = select(func.count(Quote.id)).join(
            ProcurementRequest
        ).where(ProcurementRequest.user_id == user_id)
        quote_result = await db.execute(quote_stmt)
        total_quotes = quote_result.scalar()
        
        # Count orders
        order_stmt = select(func.count(Order.id)).where(
            Order.user_id == user_id
        )
        order_result = await db.execute(order_stmt)
        total_orders = order_result.scalar()
        
        # Average quotes per request
        avg_quotes = total_quotes / total_procurements if total_procurements > 0 else 0
        
        return {
            "total_procurements": total_procurements or 0,
            "total_quotes": total_quotes or 0,
            "total_orders": total_orders or 0,
            "avg_quotes_per_request": round(avg_quotes, 2)
        }
    
    except Exception as e:
        print(f"Error fetching user stats: {str(e)}")
        return {
            "total_procurements": 0,
            "total_quotes": 0,
            "total_orders": 0,
            "avg_quotes_per_request": 0
        }


async def get_supplier_stats(
    supplier_name: str,
    db: AsyncSession
) -> Dict:
    """
    Get statistics for a supplier.
    
    Returns:
        {
            "total_quotes": int,
            "successful_quotes": int,
            "success_rate": float,
            "avg_response_time": float
        }
    """
    try:
        from models.quote import Quote
        
        # Count total attempts
        total_stmt = select(func.count(Quote.id)).where(
            Quote.supplier_name == supplier_name
        )
        total_result = await db.execute(total_stmt)
        total_quotes = total_result.scalar()
        
        # Count successful quotes
        success_stmt = select(func.count(Quote.id)).where(
            and_(
                Quote.supplier_name == supplier_name,
                Quote.status == "received"
            )
        )
        success_result = await db.execute(success_stmt)
        successful_quotes = success_result.scalar()
        
        # Calculate success rate
        success_rate = successful_quotes / total_quotes if total_quotes > 0 else 0
        
        return {
            "total_quotes": total_quotes or 0,
            "successful_quotes": successful_quotes or 0,
            "success_rate": round(success_rate, 2)
        }
    
    except Exception as e:
        print(f"Error fetching supplier stats: {str(e)}")
        return {
            "total_quotes": 0,
            "successful_quotes": 0,
            "success_rate": 0.0
        }


# ─────────────────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────────────────

async def safe_commit(db: AsyncSession) -> bool:
    """
    Safely commit transaction with error handling.
    
    Returns:
        True if successful, False otherwise
    """
    try:
        await db.commit()
        return True
    except Exception as e:
        await db.rollback()
        print(f"Database commit error: {str(e)}")
        return False


async def safe_rollback(db: AsyncSession):
    """
    Safely rollback transaction.
    """
    try:
        await db.rollback()
    except Exception as e:
        print(f"Database rollback error: {str(e)}")