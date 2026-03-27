"""
LLM service using OpenAI (gpt-4o by default).
Handles parsing, cleaning, categorization, and decision-making for procurement flows.
"""

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from openai import AsyncOpenAI
from config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """
    Async OpenAI client wrapper for structured tasks in procurement agent.
    """

    def __init__(self):
        if not settings.OPENAI_API_KEY:
            print("⚠️ OPENAI_API_KEY not set — LLM disabled")
            self.client = None
            return
        
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL or "gpt-4o"
        logger.info(f"LLMService initialized with model: {self.model}")

    async def parse_product_spec(
        self,
        raw_spec: str
    ) -> Dict[str, Any]:
        """
        Parse raw user input (e.g. "500 units of industrial gloves, size L, nitrile") 
        into structured dict for TinyFish goal building and supplier matching.
        """
        prompt = f"""
You are a procurement expert. Parse this raw product specification into JSON.

Raw input: "{raw_spec}"

Extract and return ONLY valid JSON with these keys (use null or empty if missing):
{{
  "product_name": str,          // main item, e.g. "industrial gloves"
  "quantity": int or null,
  "unit": str or null,          // e.g. "units", "pieces"
  "specifications": str or list[str],  // size, material, etc.
  "category": str,              // e.g. "safety_equipment", "ppe" — use standard from supplier matcher
  "description": str or null,
  "other_requirements": str or null
}}

Respond with JSON only. No explanations.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,  # deterministic for parsing
                max_tokens=300,
            )
            content = response.choices[0].message.content.strip()
            parsed = json.loads(content)
            logger.info("Product spec parsed successfully")
            return parsed
        except Exception as e:
            logger.error(f"Spec parse failed: {e}")
            return {"raw": raw_spec, "error": str(e)}

    async def clean_tinyfish_extraction(
        self,
        raw_result: Dict[str, Any],
        supplier_name: str
    ) -> Dict[str, Any]:
        """
        Clean messy TinyFish output into clean Quote-compatible dict.
        Adds INR conversions later via currency_service if needed.
        """
        prompt = f"""
Clean this raw extraction from supplier "{supplier_name}" into structured quote data.

Raw data: {json.dumps(raw_result, indent=2)}

Return ONLY JSON matching this schema (use null for missing/invalid):
{{
  "success": bool,
  "quote_id": str or null,
  "quote_reference": str or null,
  "unit_price": float or null,
  "total_price": float or null,
  "currency": str or null,      // e.g. "USD", "INR"
  "delivery_days": int or null,
  "estimated_delivery": str or null,  // date or text
  "notes": str or null,
  "error": str or null,
  "status": "received" | "failed" | "partial"
}}

Be conservative: if data looks invalid, set success=false and explain in notes/error.
JSON only.
"""

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=500,
            )
            content = response.choices[0].message.content.strip()
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            cleaned = json.loads(content)
            logger.info(f"Cleaned extraction from {supplier_name}")
            return cleaned
        except Exception as e:
            logger.error(f"Cleaning failed for {supplier_name}: {e}")
            return {"success": False, "error": str(e), "raw": raw_result}

    async def select_best_quote(
        self,
        quotes: List[Dict[str, Any]],
        criteria: str = "lowest total price after INR conversion, then shortest delivery"
    ) -> Dict[str, Any]:
        """
        From list of cleaned quotes, pick the best one with reasoning.
        """
        prompt = f"""
From these supplier quotes, select the BEST one based on: {criteria}

Quotes:
{json.dumps(quotes, indent=2)}

Return ONLY JSON:
{{
  "best_quote_index": int,      // 0-based index in input list, or -1 if none good
  "reasoning": str,
  "best_supplier": str,
  "estimated_savings_note": str or null
}}
"""

        # ... similar call as above ...

        # Parse and return
        pass  # implement similarly

# Global instance (like tinyfish_client)
llm_service = LLMService()


async def extract_quote_from_html(html_content: str, product_spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Best-effort quote extraction from raw HTML using the configured LLM service."""
    if llm_service.client is None:
        return None

    prompt = f"""
Extract quote information from this supplier page HTML.

Product spec:
{json.dumps(product_spec)}

HTML:
{html_content[:15000]}

Return ONLY JSON:
{{
  "price_per_unit": float or null,
  "total_price": float or null,
  "currency": str or null,
  "delivery_days": int or null,
  "quote_reference": str or null,
  "raw_data": dict
}}
"""

    try:
        response = await llm_service.client.chat.completions.create(
            model=llm_service.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=500,
        )
        content = (response.choices[0].message.content or "").strip()
        if content.startswith("```json"):
            content = content.split("```json", 1)[1].split("```", 1)[0].strip()
        parsed = json.loads(content)
        if not isinstance(parsed, dict):
            return None
        parsed.setdefault("raw_data", {})
        return parsed
    except Exception:
        return None


async def summarize_results(ranked_quotes: List[Dict[str, Any]], spec: Dict[str, Any]) -> str:
    """Generate a short human-readable summary for completed procurement runs."""
    if not ranked_quotes:
        return "No quotes were received from suppliers."

    top = ranked_quotes[0]
    product = spec.get("product_name") or "requested product"

    if llm_service.client is None:
        return (
            f"Received {len(ranked_quotes)} quotes for {product}. "
            f"Best option is {top.get('supplier_name', 'Unknown supplier')} "
            f"at {top.get('currency', 'USD')} {top.get('total_price', 'N/A')}."
        )

    prompt = f"""
Create a short 2-3 sentence procurement summary for the user.

Product spec:
{json.dumps(spec)}

Ranked quotes:
{json.dumps(ranked_quotes[:5])}
"""

    try:
        response = await llm_service.client.chat.completions.create(
            model=llm_service.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=180,
        )
        return (response.choices[0].message.content or "").strip() or "Quotes processed successfully."
    except Exception:
        return (
            f"Received {len(ranked_quotes)} quotes for {product}. "
            f"Top quote: {top.get('supplier_name', 'Unknown supplier')} "
            f"at {top.get('currency', 'USD')} {top.get('total_price', 'N/A')}."
        )