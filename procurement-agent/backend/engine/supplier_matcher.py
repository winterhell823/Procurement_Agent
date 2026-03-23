"""
engine/supplier_matcher.py
────────────────────────────────────────────────────────────────────
Matches products to relevant suppliers based on category and criteria.

Takes a product category (like "safety_equipment") and returns a list
of suppliers that can provide quotes for that category.
"""

import uuid
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_


async def match_suppliers(
    category: str,
    user_id: uuid.UUID,
    db: AsyncSession,
    limit: int = 10,
    min_success_rate: float = 0.0
) -> List[Dict]:
    """
    Main entry point - find suppliers for a product category.
    
    Args:
        category: Product category (e.g., "safety_equipment")
        user_id: User requesting quotes
        db: Database session
        limit: Maximum number of suppliers to return (default: 10)
        min_success_rate: Minimum supplier success rate (0.0 to 1.0)
    
    Returns:
        List of supplier dictionaries:
        [
            {
                "id": uuid,
                "name": str,
                "website_url": str,
                "quote_form_url": str,
                "requires_login": bool,
                "login_url": str (optional),
                "credentials": dict (optional),
                "success_rate": float,
                "avg_response_time": int,
                "last_successful_quote": datetime (optional)
            }
        ]
    """
    
    matcher = SupplierMatcher(db)
    return await matcher.match_suppliers(
        category=category,
        user_id=user_id,
        limit=limit,
        min_success_rate=min_success_rate
    )


class SupplierMatcher:
    """
    Engine that matches products to relevant suppliers.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Initialize matcher with database session.
        
        Args:
            db: SQLAlchemy async database session
        """
        self.db = db
        
        # Category aliases (alternative names for same category)
        self.category_aliases = {
            "safety_equipment": ["ppe", "safety", "protective_equipment"],
            "office_supplies": ["office", "stationery", "office_products"],
            "electronics": ["electronic", "tech", "technology"],
            "furniture": ["office_furniture", "seating"],
            "industrial_materials": ["industrial", "raw_materials", "materials"],
            "tools": ["hand_tools", "power_tools", "equipment"],
            "packaging": ["packing", "shipping_supplies"],
            "cleaning_supplies": ["cleaning", "janitorial"]
        }
    
    
    async def match_suppliers(
        self,
        category: str,
        user_id: uuid.UUID,
        limit: int = 10,
        min_success_rate: float = 0.0
    ) -> List[Dict]:
        """
        Find and rank suppliers for a category.
        """
        from models.supplier import Supplier
        
        # Step 1: Get all category variations
        categories_to_search = self._get_category_variations(category)
        
        # Step 2: Query database for matching suppliers
        query = select(Supplier).where(
            and_(
                Supplier.enabled == True,  # Only enabled suppliers
                or_(
                    *[Supplier.supported_categories.contains([cat]) 
                      for cat in categories_to_search]
                ),
                Supplier.success_rate >= min_success_rate  # Filter by success rate
            )
        ).order_by(
            Supplier.success_rate.desc(),  # Best suppliers first
            Supplier.avg_response_time.asc()  # Fastest response time
        ).limit(limit * 2)  # Get extra in case some are filtered out
        
        result = await self.db.execute(query)
        suppliers = result.scalars().all()
        
        # Step 3: Convert to dictionaries and add user-specific data
        supplier_dicts = []
        
        for supplier in suppliers:
            supplier_dict = {
                "id": supplier.id,
                "name": supplier.name,
                "website_url": supplier.website_url,
                "quote_form_url": supplier.quote_form_url,
                "requires_login": supplier.requires_login,
                "login_url": supplier.login_url,
                "credentials": supplier.login_credentials if supplier.requires_login else {},
                "success_rate": float(supplier.success_rate or 0.0),
                "avg_response_time": supplier.avg_response_time or 0,
                "last_successful_quote": supplier.last_successful_quote,
                "supported_categories": supplier.supported_categories or []
            }
            
            # Check if this is a user-added supplier
            if supplier.user_id == user_id:
                supplier_dict["is_user_supplier"] = True
                supplier_dict["priority"] = 1  # User's own suppliers get priority
            else:
                supplier_dict["is_user_supplier"] = False
                supplier_dict["priority"] = 2  # System suppliers
            
            supplier_dicts.append(supplier_dict)
        
        # Step 4: Sort by priority (user suppliers first, then by success rate)
        supplier_dicts.sort(
            key=lambda s: (s["priority"], -s["success_rate"], s["avg_response_time"])
        )
        
        # Step 5: Return limited number
        return supplier_dicts[:limit]
    
    
    def _get_category_variations(self, category: str) -> List[str]:
        """
        Get all variations of a category name.
        
        Args:
            category: Primary category name
        
        Returns:
            List of category names including aliases
        """
        variations = [category.lower()]
        
        # Add aliases if they exist
        if category in self.category_aliases:
            variations.extend(self.category_aliases[category])
        
        # Also check if category is itself an alias
        for primary, aliases in self.category_aliases.items():
            if category.lower() in aliases:
                variations.append(primary)
                variations.extend(aliases)
        
        # Remove duplicates
        return list(set(variations))
    
    
    async def get_supplier_by_name(self, name: str) -> Optional[Dict]:
        """
        Get a specific supplier by name.
        
        Args:
            name: Supplier name
        
        Returns:
            Supplier dictionary or None if not found
        """
        from models.supplier import Supplier
        
        query = select(Supplier).where(Supplier.name == name)
        result = await self.db.execute(query)
        supplier = result.scalar_one_or_none()
        
        if not supplier:
            return None
        
        return {
            "id": supplier.id,
            "name": supplier.name,
            "website_url": supplier.website_url,
            "quote_form_url": supplier.quote_form_url,
            "requires_login": supplier.requires_login,
            "login_url": supplier.login_url,
            "credentials": supplier.login_credentials if supplier.requires_login else {},
            "success_rate": float(supplier.success_rate or 0.0),
            "avg_response_time": supplier.avg_response_time or 0
        }
    
    
    async def get_all_categories(self) -> List[str]:
        """
        Get list of all available categories.
        
        Returns:
            List of category names
        """
        from models.supplier import Supplier
        from sqlalchemy import func
        
        # Get unique categories from all suppliers
        query = select(func.unnest(Supplier.supported_categories)).distinct()
        result = await self.db.execute(query)
        categories = [row[0] for row in result]
        
        return sorted(categories)
    
    
    async def get_suppliers_by_ids(self, supplier_ids: List[uuid.UUID]) -> List[Dict]:
        """
        Get specific suppliers by their IDs.
        
        Args:
            supplier_ids: List of supplier UUIDs
        
        Returns:
            List of supplier dictionaries
        """
        from models.supplier import Supplier
        
        query = select(Supplier).where(Supplier.id.in_(supplier_ids))
        result = await self.db.execute(query)
        suppliers = result.scalars().all()
        
        supplier_dicts = []
        for supplier in suppliers:
            supplier_dicts.append({
                "id": supplier.id,
                "name": supplier.name,
                "website_url": supplier.website_url,
                "quote_form_url": supplier.quote_form_url,
                "requires_login": supplier.requires_login,
                "login_url": supplier.login_url,
                "credentials": supplier.login_credentials if supplier.requires_login else {},
                "success_rate": float(supplier.success_rate or 0.0),
                "avg_response_time": supplier.avg_response_time or 0
            })
        
        return supplier_dicts


# ─────────────────────────────────────────────────────────────────────
# Supplier Filtering and Ranking Functions
# ─────────────────────────────────────────────────────────────────────

def filter_by_success_rate(
    suppliers: List[Dict],
    min_rate: float
) -> List[Dict]:
    """
    Filter suppliers by minimum success rate.
    
    Args:
        suppliers: List of supplier dictionaries
        min_rate: Minimum success rate (0.0 to 1.0)
    
    Returns:
        Filtered list
    """
    return [
        s for s in suppliers 
        if s.get("success_rate", 0) >= min_rate
    ]


def filter_by_response_time(
    suppliers: List[Dict],
    max_seconds: int
) -> List[Dict]:
    """
    Filter suppliers by maximum response time.
    
    Args:
        suppliers: List of supplier dictionaries
        max_seconds: Maximum average response time
    
    Returns:
        Filtered list
    """
    return [
        s for s in suppliers 
        if s.get("avg_response_time", 999999) <= max_seconds
    ]


def rank_by_reliability(suppliers: List[Dict]) -> List[Dict]:
    """
    Sort suppliers by reliability (success rate + response time).
    
    Args:
        suppliers: List of supplier dictionaries
    
    Returns:
        Sorted list (most reliable first)
    """
    def reliability_score(supplier):
        success_rate = supplier.get("success_rate", 0)
        response_time = supplier.get("avg_response_time", 999)
        
        # Normalize response time (lower is better)
        # Assume 60s is "good", anything higher is worse
        time_score = max(0, 1 - (response_time / 120))
        
        # Combined score (70% success rate, 30% response time)
        return (success_rate * 0.7) + (time_score * 0.3)
    
    return sorted(suppliers, key=reliability_score, reverse=True)


def diversify_suppliers(
    suppliers: List[Dict],
    max_per_type: int = 3
) -> List[Dict]:
    """
    Diversify supplier selection to avoid putting all eggs in one basket.
    
    Args:
        suppliers: List of supplier dictionaries
        max_per_type: Maximum suppliers per type/category
    
    Returns:
        Diversified list
    """
    # Group by primary category
    by_category = {}
    
    for supplier in suppliers:
        # Get first category as primary
        categories = supplier.get("supported_categories", [])
        primary_category = categories[0] if categories else "general"
        
        if primary_category not in by_category:
            by_category[primary_category] = []
        
        by_category[primary_category].append(supplier)
    
    # Take max_per_type from each category
    diversified = []
    
    for category_suppliers in by_category.values():
        diversified.extend(category_suppliers[:max_per_type])
    
    return diversified


# ─────────────────────────────────────────────────────────────────────
# Category Management
# ─────────────────────────────────────────────────────────────────────

def get_category_keywords(category: str) -> List[str]:
    """
    Get search keywords for a category.
    
    Args:
        category: Category name
    
    Returns:
        List of keywords
    """
    category_keywords = {
        "safety_equipment": [
            "gloves", "helmet", "goggles", "safety", "protective",
            "ppe", "hard hat", "vest", "respirator"
        ],
        "office_supplies": [
            "paper", "pen", "pencil", "folder", "binder", "stapler",
            "office", "stationery", "desk supplies"
        ],
        "electronics": [
            "laptop", "computer", "monitor", "cable", "charger",
            "phone", "tablet", "electronics", "tech"
        ],
        "furniture": [
            "desk", "chair", "table", "cabinet", "furniture",
            "seating", "office furniture"
        ],
        "industrial_materials": [
            "steel", "aluminum", "plastic", "metal", "materials",
            "raw materials", "industrial"
        ],
        "tools": [
            "hammer", "drill", "saw", "wrench", "tools",
            "hand tools", "power tools"
        ],
        "packaging": [
            "box", "carton", "tape", "bubble wrap", "packaging",
            "shipping supplies", "pallet"
        ],
        "cleaning_supplies": [
            "detergent", "cleaner", "mop", "cleaning", "janitorial",
            "sanitizer", "disinfectant"
        ]
    }
    
    return category_keywords.get(category, [category])


def normalize_category(category: str) -> str:
    """
    Normalize category name to standard format.
    
    Args:
        category: Category name (any format)
    
    Returns:
        Standardized category name
    """
    category_mapping = {
        "ppe": "safety_equipment",
        "safety": "safety_equipment",
        "office": "office_supplies",
        "stationery": "office_supplies",
        "tech": "electronics",
        "electronic": "electronics",
        "office_furniture": "furniture",
        "industrial": "industrial_materials",
        "hand_tools": "tools",
        "power_tools": "tools",
        "packing": "packaging",
        "shipping": "packaging",
        "janitorial": "cleaning_supplies"
    }
    
    category_lower = category.lower().strip()
    return category_mapping.get(category_lower, category_lower)


# ─────────────────────────────────────────────────────────────────────
# Supplier Scoring
# ─────────────────────────────────────────────────────────────────────

def calculate_supplier_score(supplier: Dict) -> float:
    """
    Calculate overall supplier quality score (0-100).
    
    Factors:
    - Success rate (50%)
    - Response time (30%)
    - Recent activity (20%)
    
    Args:
        supplier: Supplier dictionary
    
    Returns:
        Score from 0 to 100
    """
    # Success rate score (0-50)
    success_rate = supplier.get("success_rate", 0)
    success_score = success_rate * 50
    
    # Response time score (0-30)
    response_time = supplier.get("avg_response_time", 120)
    # Good: 30s or less = 30 points
    # Acceptable: 60s = 20 points
    # Slow: 120s or more = 0 points
    if response_time <= 30:
        time_score = 30
    elif response_time <= 60:
        time_score = 20
    elif response_time <= 90:
        time_score = 10
    else:
        time_score = max(0, 30 - (response_time - 90) / 10)
    
    # Recent activity score (0-20)
    last_quote = supplier.get("last_successful_quote")
    if last_quote:
        from datetime import datetime, timedelta
        days_ago = (datetime.utcnow() - last_quote).days
        
        if days_ago <= 7:
            activity_score = 20
        elif days_ago <= 30:
            activity_score = 15
        elif days_ago <= 90:
            activity_score = 10
        else:
            activity_score = 5
    else:
        activity_score = 10  # Neutral for new suppliers
    
    total_score = success_score + time_score + activity_score
    
    return round(total_score, 2)


def add_scores_to_suppliers(suppliers: List[Dict]) -> List[Dict]:
    """
    Add quality scores to all suppliers.
    
    Args:
        suppliers: List of supplier dictionaries
    
    Returns:
        Same list with "quality_score" added to each
    """
    for supplier in suppliers:
        supplier["quality_score"] = calculate_supplier_score(supplier)
    
    return suppliers


# ─────────────────────────────────────────────────────────────────────
# Example Usage
# ─────────────────────────────────────────────────────────────────────

async def example_usage(db: AsyncSession):
    """
    Example of how to use the supplier matcher.
    """
    import uuid
    
    # Find suppliers for safety equipment
    suppliers = await match_suppliers(
        category="safety_equipment",
        user_id=uuid.uuid4(),
        db=db,
        limit=10,
        min_success_rate=0.7  # Only suppliers with 70%+ success rate
    )
    
    print(f"Found {len(suppliers)} suppliers")
    
    for supplier in suppliers:
        print(f"- {supplier['name']}: {supplier['success_rate']:.2%} success rate")
    
    # Get best supplier
    if suppliers:
        best = suppliers[0]
        print(f"\nBest supplier: {best['name']}")


if __name__ == "__main__":
    import asyncio
    # asyncio.run(example_usage(db))
    pass