"""
TinyFish Web Agent client wrapper.
Handles agent execution (sync & streaming), result parsing, error handling.
Uses official tinyfish SDK which reads TINYFISH_API_KEY from env via config.
"""

import json
import logging
from typing import Dict, Any, AsyncGenerator, Optional, Callable
from datetime import datetime

try:
    from tinyfish import TinyFish  # pip install tinyfish
except ImportError:  # pragma: no cover - optional dependency in local/dev setups
    TinyFish = None
from config import settings
# from .llm_service import clean_extraction_with_llm  # We'll add later — optional cleanup

logger = logging.getLogger(__name__)

class TinyFishClient:
    """
    Service wrapper for TinyFish agent API.
    Provides sync/streaming methods tailored for procurement quote workflows.
    """

    def __init__(self):
        """Initialize TinyFish client (API key from env via pydantic settings)."""
        if TinyFish is None:
            raise ImportError(
                "tinyfish SDK is not installed. Install it before running supplier agents."
            )
        if not settings.TINYFISH_API_KEY:
            raise ValueError("TINYFISH_API_KEY not set in environment/config")
        
        self.client = TinyFish()  # Auto-loads TINYFISH_API_KEY
        logger.info("TinyFish client initialized")

    async def run_quote_task_stream(
        self,
        supplier: Dict,
        product_spec: Dict,
        contact_info: Dict,
        procurement_id: str,  # for logging/context
        on_progress: Optional[Callable[[str], None]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream a TinyFish agent task for one supplier quote request.
        Yields progress events + final parsed result.
        
        Args:
            supplier: Supplier dict from supplier_matcher (name, website_url, etc.)
            product_spec: Parsed spec e.g. {"product": "industrial gloves", "quantity": 500, ...}
            contact_info: {"company": "...", "email": "...", ...}
            procurement_id: For context/logging
            on_progress: Optional callback for UI updates
        
        Yields:
            Dict events like {"type": "progress", "message": "..."} or final {"type": "complete", "quote": {...}}
        """
        start_url = supplier.get("quote_form_url") or supplier["website_url"]
        supplier_name = supplier["name"]

        # Build detailed, reliable goal
        goal = f"""
You are an expert procurement assistant filling quote/RFQ forms.
Navigate to {start_url}.
Find the quote request, contact, or RFQ form.

Fill with these exact details:
Product: {product_spec.get('product_name', 'unknown')}, Quantity: {product_spec.get('quantity', 'unknown')}, 
Details: {product_spec.get('description', '')}, Size/Other specs: {product_spec.get('specs', '')}

Contact: Company: {contact_info.get('company', 'Unknown Corp')}, 
Email: {contact_info.get('email', 'procurement@example.com')}, 
Phone: {contact_info.get('phone', '')}

Submit the form if possible.
After submission, extract: confirmation ID/number, estimated price (unit & total), currency, lead time/delivery days, any errors/messages, quote reference.

Always return final answer as clean JSON only:
{{
  "success": true/false,
  "quote_id": str or null,
  "unit_price": float or null,
  "total_price": float or null,
  "currency": str,
  "delivery_days": int or null,
  "notes": str,
  "error": str or null
}}
No other text outside the JSON.
"""

        logger.info(f"Starting TinyFish stream for supplier {supplier_name} | procurement {procurement_id}")

        try:
            async with self.client.agent.stream(
                url=start_url,
                goal=goal.strip(),
                # timeout=300,  # seconds — if supported, add later
            ) as stream:
                async for event in stream:
                    event_type = event.get("type")

                    if on_progress:
                        if event_type in ["step", "action", "thinking"]:
                            on_progress(f"{supplier_name}: {event.get('message', 'Processing...')}")

                    yield {
                        "type": event_type,
                        "status": event.get("status"),
                        "message": event.get("message", ""),
                        "step": event.get("step"),
                    }

                    if event_type == "COMPLETE":
                        raw_result = event.get("result", {})
                        if isinstance(raw_result, str):
                            try:
                                raw_result = json.loads(raw_result)
                            except:
                                raw_result = {"raw_text": raw_result}

                        # Optional: clean/refine with LLM later
                        # cleaned = await clean_extraction_with_llm(raw_result)

                        final_quote = {
                            "supplier_name": supplier_name,
                            "supplier_url": start_url,
                            "price_per_unit": raw_result.get("unit_price"),
                            "total_price": raw_result.get("total_price"),
                            "currency": raw_result.get("currency", "USD"),
                            "delivery_days": raw_result.get("delivery_days"),
                            "quote_reference": raw_result.get("quote_id"),
                            "notes": raw_result.get("notes") or raw_result.get("error"),
                            "status": "received" if raw_result.get("success") else "failed",
                            "raw_data": raw_result,
                            "extraction_method": "tinyfish",
                            # Add screenshot/quote_url if TinyFish returns media
                        }

                        yield {
                            "type": "complete",
                            "quote": final_quote,
                            "success": raw_result.get("success", False)
                        }
                        return

        except Exception as e:
            logger.error(f"TinyFish error for {supplier_name}: {str(e)}")
            yield {
                "type": "error",
                "message": str(e),
                "supplier": supplier_name
            }

    # Add sync version later if needed for batch
    # def run_quote_task_sync(...): ...

# Singleton / global instance (common in services)
def get_tinyfish_client():
    return TinyFishClient()