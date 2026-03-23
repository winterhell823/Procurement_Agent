"""
engine/quote_comparator.py
────────────────────────────────────────────────────────────────────
Compares and ranks quotes from multiple suppliers.

Takes raw quotes, calculates scores based on price, delivery time,
and supplier reliability, then returns them ranked from best to worst.
"""

from typing import List, Dict, Optional
from datetime import datetime


async def rank_quotes(quotes: List[Dict], product_spec: Dict) -> List[Dict]:
    """
    Main entry point - rank quotes by multiple criteria.
    
    Args:
        quotes: List of quote dictionaries from suppliers
        product_spec: Original product specification
    
    Returns:
        List of quotes sorted by score (best first), with added fields:
        - "score": Overall score (0-100)
        - "price_score": Price component (0-100)
        - "delivery_score": Delivery speed component (0-100)
        - "reliability_score": Supplier reliability component (0-100)
        - "rank": Position (1, 2, 3, ...)
    """
    
    comparator = QuoteComparator()
    return await comparator.rank_quotes(quotes, product_spec)


class QuoteComparator:
    """
    Engine that analyzes and ranks quotes based on multiple factors.
    """
    
    def __init__(self):
        """
        Initialize comparator with default weights.
        """
        # Scoring weights (must add up to 1.0)
        self.weights = {
            "price": 0.50,        # 50% - Most important
            "delivery": 0.30,     # 30% - Speed matters
            "reliability": 0.20   # 20% - Trust factor
        }
    
    
    async def rank_quotes(
        self, 
        quotes: List[Dict], 
        product_spec: Dict
    ) -> List[Dict]:
        """
        Rank all quotes and add scoring information.
        """
        if not quotes:
            return []
        
        # Filter out failed quotes
        valid_quotes = [
            q for q in quotes 
            if q.get("status") == "received" and q.get("total_price", 0) > 0
        ]
        
        if not valid_quotes:
            return quotes  # Return original if none are valid
        
        # Step 1: Calculate individual scores for each quote
        scored_quotes = []
        
        for quote in valid_quotes:
            scores = self._calculate_scores(quote, valid_quotes)
            
            # Add scores to quote
            quote["price_score"] = scores["price_score"]
            quote["delivery_score"] = scores["delivery_score"]
            quote["reliability_score"] = scores["reliability_score"]
            quote["overall_score"] = scores["overall_score"]
            
            scored_quotes.append(quote)
        
        # Step 2: Sort by overall score (highest first)
        scored_quotes.sort(key=lambda q: q["overall_score"], reverse=True)
        
        # Step 3: Add rank numbers
        for idx, quote in enumerate(scored_quotes, start=1):
            quote["rank"] = idx
            quote["is_best"] = (idx == 1)
        
        # Step 4: Add failed quotes at the end (unranked)
        failed_quotes = [q for q in quotes if q.get("status") != "received"]
        for quote in failed_quotes:
            quote["rank"] = None
            quote["overall_score"] = 0
            quote["is_best"] = False
        
        return scored_quotes + failed_quotes
    
    
    def _calculate_scores(
        self, 
        quote: Dict, 
        all_quotes: List[Dict]
    ) -> Dict:
        """
        Calculate all scores for a single quote.
        
        Returns:
            {
                "price_score": float (0-100),
                "delivery_score": float (0-100),
                "reliability_score": float (0-100),
                "overall_score": float (0-100)
            }
        """
        # Get price score (lower price = higher score)
        price_score = self._calculate_price_score(quote, all_quotes)
        
        # Get delivery score (faster delivery = higher score)
        delivery_score = self._calculate_delivery_score(quote, all_quotes)
        
        # Get reliability score (based on supplier track record)
        reliability_score = self._calculate_reliability_score(quote)
        
        # Calculate weighted overall score
        overall_score = (
            price_score * self.weights["price"] +
            delivery_score * self.weights["delivery"] +
            reliability_score * self.weights["reliability"]
        )
        
        return {
            "price_score": round(price_score, 2),
            "delivery_score": round(delivery_score, 2),
            "reliability_score": round(reliability_score, 2),
            "overall_score": round(overall_score, 2)
        }
    
    
    def _calculate_price_score(
        self, 
        quote: Dict, 
        all_quotes: List[Dict]
    ) -> float:
        """
        Calculate price score (0-100).
        
        Logic:
        - Lowest price gets 100
        - Highest price gets 0
        - Others scaled linearly in between
        """
        prices = [q.get("total_price", 0) for q in all_quotes if q.get("total_price", 0) > 0]
        
        if not prices or len(prices) == 1:
            return 100.0  # Only one quote or no valid prices
        
        min_price = min(prices)
        max_price = max(prices)
        quote_price = quote.get("total_price", 0)
        
        if quote_price == 0:
            return 0.0
        
        if max_price == min_price:
            return 100.0  # All same price
        
        # Linear scaling: cheapest=100, most expensive=0
        score = 100 * (max_price - quote_price) / (max_price - min_price)
        
        return max(0.0, min(100.0, score))
    
    
    def _calculate_delivery_score(
        self, 
        quote: Dict, 
        all_quotes: List[Dict]
    ) -> float:
        """
        Calculate delivery speed score (0-100).
        
        Logic:
        - Fastest delivery gets 100
        - Slowest delivery gets 0
        - Others scaled linearly in between
        """
        delivery_times = [
            q.get("delivery_days", 999) 
            for q in all_quotes 
            if q.get("delivery_days", 0) > 0
        ]
        
        if not delivery_times or len(delivery_times) == 1:
            return 100.0  # Only one quote or no valid delivery times
        
        min_days = min(delivery_times)
        max_days = max(delivery_times)
        quote_days = quote.get("delivery_days", 999)
        
        if quote_days == 0 or quote_days == 999:
            return 50.0  # Unknown delivery time = neutral score
        
        if max_days == min_days:
            return 100.0  # All same delivery time
        
        # Linear scaling: fastest=100, slowest=0
        score = 100 * (max_days - quote_days) / (max_days - min_days)
        
        return max(0.0, min(100.0, score))
    
    
    def _calculate_reliability_score(self, quote: Dict) -> float:
        """
        Calculate supplier reliability score (0-100).
        
        Logic:
        - Based on supplier's historical success rate
        - If no history, give neutral score (70)
        """
        # Try to get supplier reliability from quote metadata
        supplier_success_rate = quote.get("supplier_success_rate")
        
        if supplier_success_rate is not None:
            # Success rate is 0.0 to 1.0, convert to 0-100
            return supplier_success_rate * 100
        
        # Check if quote has supplier reliability data
        if "supplier_reliability" in quote:
            return quote["supplier_reliability"]
        
        # Default: neutral score for unknown suppliers
        return 70.0
    
    
    def get_best_quote(self, quotes: List[Dict]) -> Optional[Dict]:
        """
        Get the single best quote from a list.
        
        Args:
            quotes: List of quotes (can be ranked or unranked)
        
        Returns:
            The best quote, or None if no valid quotes
        """
        valid_quotes = [
            q for q in quotes 
            if q.get("status") == "received" and q.get("overall_score", 0) > 0
        ]
        
        if not valid_quotes:
            return None
        
        # Sort by score and return top one
        valid_quotes.sort(key=lambda q: q.get("overall_score", 0), reverse=True)
        
        return valid_quotes[0]
    
    
    def get_cheapest_quote(self, quotes: List[Dict]) -> Optional[Dict]:
        """
        Get the cheapest quote (regardless of other factors).
        """
        valid_quotes = [
            q for q in quotes 
            if q.get("status") == "received" and q.get("total_price", 0) > 0
        ]
        
        if not valid_quotes:
            return None
        
        return min(valid_quotes, key=lambda q: q.get("total_price", float('inf')))
    
    
    def get_fastest_quote(self, quotes: List[Dict]) -> Optional[Dict]:
        """
        Get the fastest delivery quote (regardless of other factors).
        """
        valid_quotes = [
            q for q in quotes 
            if q.get("status") == "received" and q.get("delivery_days", 0) > 0
        ]
        
        if not valid_quotes:
            return None
        
        return min(valid_quotes, key=lambda q: q.get("delivery_days", float('inf')))
    
    
    def calculate_savings(
        self, 
        selected_quote: Dict, 
        all_quotes: List[Dict]
    ) -> Dict:
        """
        Calculate how much money was saved by choosing this quote.
        
        Returns:
            {
                "amount_saved": float,
                "percentage_saved": float,
                "compared_to": str (supplier name)
            }
        """
        valid_quotes = [
            q for q in all_quotes 
            if q.get("status") == "received" and q.get("total_price", 0) > 0
        ]
        
        if len(valid_quotes) < 2:
            return {
                "amount_saved": 0,
                "percentage_saved": 0,
                "compared_to": None
            }
        
        selected_price = selected_quote.get("total_price", 0)
        
        # Find most expensive quote
        most_expensive = max(valid_quotes, key=lambda q: q.get("total_price", 0))
        most_expensive_price = most_expensive.get("total_price", 0)
        
        if most_expensive_price == 0 or selected_price == 0:
            return {
                "amount_saved": 0,
                "percentage_saved": 0,
                "compared_to": None
            }
        
        amount_saved = most_expensive_price - selected_price
        percentage_saved = (amount_saved / most_expensive_price) * 100
        
        return {
            "amount_saved": round(amount_saved, 2),
            "percentage_saved": round(percentage_saved, 2),
            "compared_to": most_expensive.get("supplier_name", "Unknown")
        }
    
    
    def generate_comparison_summary(
        self, 
        quotes: List[Dict]
    ) -> str:
        """
        Generate a human-readable summary of the quotes.
        
        Returns:
            String summary like:
            "Received 7 quotes. Best value: Grainger at $2.50/unit (3 days).
             Cheapest: Uline at $2.40/unit (5 days). Fastest: Amazon at $2.80/unit (1 day)."
        """
        valid_quotes = [
            q for q in quotes 
            if q.get("status") == "received"
        ]
        
        if not valid_quotes:
            return "No valid quotes received."
        
        best = self.get_best_quote(quotes)
        cheapest = self.get_cheapest_quote(quotes)
        fastest = self.get_fastest_quote(quotes)
        
        summary_parts = []
        
        # Total count
        summary_parts.append(f"Received {len(valid_quotes)} quotes.")
        
        # Best overall
        if best:
            summary_parts.append(
                f"Best value: {best.get('supplier_name')} at "
                f"{best.get('currency', 'USD')} {best.get('price_per_unit', 0):.2f}/unit "
                f"({best.get('delivery_days', 0)} days delivery)."
            )
        
        # Cheapest (if different from best)
        if cheapest and cheapest.get("supplier_name") != best.get("supplier_name"):
            summary_parts.append(
                f"Cheapest: {cheapest.get('supplier_name')} at "
                f"{cheapest.get('currency', 'USD')} {cheapest.get('price_per_unit', 0):.2f}/unit "
                f"({cheapest.get('delivery_days', 0)} days)."
            )
        
        # Fastest (if different from best and cheapest)
        if (fastest and 
            fastest.get("supplier_name") != best.get("supplier_name") and
            fastest.get("supplier_name") != cheapest.get("supplier_name")):
            summary_parts.append(
                f"Fastest: {fastest.get('supplier_name')} at "
                f"{fastest.get('currency', 'USD')} {fastest.get('price_per_unit', 0):.2f}/unit "
                f"({fastest.get('delivery_days', 0)} days)."
            )
        
        return " ".join(summary_parts)


# ─────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────

def filter_by_price_range(
    quotes: List[Dict],
    min_price: Optional[float] = None,
    max_price: Optional[float] = None
) -> List[Dict]:
    """
    Filter quotes by price range.
    
    Args:
        quotes: List of quotes
        min_price: Minimum total price (inclusive)
        max_price: Maximum total price (inclusive)
    
    Returns:
        Filtered list of quotes
    """
    filtered = quotes.copy()
    
    if min_price is not None:
        filtered = [q for q in filtered if q.get("total_price", 0) >= min_price]
    
    if max_price is not None:
        filtered = [q for q in filtered if q.get("total_price", 0) <= max_price]
    
    return filtered


def filter_by_delivery_time(
    quotes: List[Dict],
    max_days: int
) -> List[Dict]:
    """
    Filter quotes that can deliver within specified days.
    
    Args:
        quotes: List of quotes
        max_days: Maximum delivery days
    
    Returns:
        Filtered list of quotes
    """
    return [
        q for q in quotes 
        if q.get("delivery_days", 999) <= max_days
    ]


def filter_by_supplier(
    quotes: List[Dict],
    supplier_names: List[str]
) -> List[Dict]:
    """
    Filter quotes from specific suppliers.
    
    Args:
        quotes: List of quotes
        supplier_names: List of supplier names to include
    
    Returns:
        Filtered list of quotes
    """
    return [
        q for q in quotes 
        if q.get("supplier_name") in supplier_names
    ]


def calculate_average_price(quotes: List[Dict]) -> float:
    """
    Calculate average price across all quotes.
    """
    valid_prices = [
        q.get("total_price", 0) 
        for q in quotes 
        if q.get("status") == "received" and q.get("total_price", 0) > 0
    ]
    
    if not valid_prices:
        return 0.0
    
    return sum(valid_prices) / len(valid_prices)


def calculate_price_spread(quotes: List[Dict]) -> Dict:
    """
    Calculate price spread (min, max, average, range).
    
    Returns:
        {
            "min": float,
            "max": float,
            "average": float,
            "range": float,
            "range_percentage": float
        }
    """
    valid_prices = [
        q.get("total_price", 0) 
        for q in quotes 
        if q.get("status") == "received" and q.get("total_price", 0) > 0
    ]
    
    if not valid_prices:
        return {
            "min": 0,
            "max": 0,
            "average": 0,
            "range": 0,
            "range_percentage": 0
        }
    
    min_price = min(valid_prices)
    max_price = max(valid_prices)
    avg_price = sum(valid_prices) / len(valid_prices)
    price_range = max_price - min_price
    range_percentage = (price_range / min_price * 100) if min_price > 0 else 0
    
    return {
        "min": round(min_price, 2),
        "max": round(max_price, 2),
        "average": round(avg_price, 2),
        "range": round(price_range, 2),
        "range_percentage": round(range_percentage, 2)
    }