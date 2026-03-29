import asyncio
import uuid
import json
from typing import Dict, Optional, Callable
from datetime import datetime
from services.tinyfish_client import TinyFishClient

async def run_supplier_agent(supplier: Dict, product_spec: Dict, company_profile: Dict, on_status: Optional[Callable] = None) -> Dict:
    agent = SupplierAgent(on_status)
    return await agent.get_quote(supplier, product_spec, company_profile)

class SupplierAgent:
    def __init__(self, logger: Optional[Callable] = None):
        async def default_logger(msg): print(msg)
        self.log = logger or default_logger
        self.tinyfish = None
    
    async def get_quote(self, supplier: Dict, product_spec: Dict, company_profile: Dict) -> Dict:
        supplier_name = supplier.get("name", "Unknown")
        final_quote = None
        try:
            await self.log(f"Starting quote request from {supplier_name}...")
            self.tinyfish = TinyFishClient()
            async for event in self.tinyfish.run_quote_task_stream(supplier=supplier, product_spec=product_spec, contact_info=company_profile, procurement_id=str(uuid.uuid4())):
                if event["type"] in ["progress", "step", "action", "thinking"]:
                    msg = event.get("message", "Processing...")
                    await self.log(f"{supplier_name}: {msg}")
                elif event["type"] == "complete":
                    final_quote = event["quote"]
                    break
                elif event["type"] == "error":
                    raise Exception(event.get("message", "Unknown error from agent stream"))
            if final_quote:
                await self.log(f"Quote received: {final_quote.get('currency', 'USD')} {final_quote.get('price_per_unit', 0)}/unit")
                return final_quote
            else:
                raise Exception("Agent finished without returning a quote.")
        except Exception as e:
            await self.log(f"Failed to get quote from {supplier_name}: {str(e)}")
            return {
                "status": "failed",
                "supplier_name": supplier_name,
                "supplier_url": supplier.get("website_url", ""),
                "error": str(e),
                "extracted_at": datetime.utcnow().isoformat()
            }
