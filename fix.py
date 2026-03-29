import sys

code = """import uuid
import logging
from typing import List, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

logger = logging.getLogger(__name__)

async def match_suppliers(category: str, user_id: uuid.UUID, db: AsyncSession, limit: int = 5) -> List[Dict]:
    from models.supplier import Supplier
    
    query = select(Supplier).where(Supplier.is_active == True)
    result = await db.execute(query)
    all_suppliers = result.scalars().all()
    
    supplier_dicts = []
    for supplier in all_suppliers:
        supplier_dict = {
            "id": str(supplier.id),
            "name": supplier.name,
            "website_url": supplier.website or "",
            "quote_form_url": supplier.website or "",
            "reliability_score": supplier.reliability_score or 50.0
        }
        supplier_dicts.append(supplier_dict)
        
    return supplier_dicts[:limit]
"""

with open("procurement-agent/backend/engine/supplier_matcher.py", "w") as f:
    f.write(code)
