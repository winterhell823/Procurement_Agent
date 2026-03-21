import asyncio
import uuid
import time
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agents.supplier_agent import run_supplier_agent
from engine.spec_parser import parse_spec
from engine.supplier_matcher import match_suppliers
from engine.quote_comparator import rank_quotes
from services.llm_service import summarize_results
from services.db_service import (
    update_procurement_status,
    save_quote,
    append_agent_log
)
from services.notification_service import notify_quotes_ready    # Feature 1
from services.currency_service import normalize_quotes_currency  # Feature 8
from services.reliability_service import record_quote_attempt    # Feature 10
from services.validity_service import create_validity_record     # Feature 5
from models.procurement import ProcurementStatus
from models.user import User


async def run_procurement_pipeline(
    procurement_id:  uuid.UUID,
    raw_description: str,
    user_id:         uuid.UUID,
    db:              AsyncSession
) -> dict:
    """
    Master pipeline — runs end to end:
    1.  Parse product spec
    2.  Get user/company profile
    3.  Match suppliers
    4.  Run TinyFish agents in parallel
    5.  Normalize currencies to INR         (Feature 8)
    6.  Update supplier reliability scores  (Feature 10)
    7.  Rank quotes
    8.  Save quotes + validity records      (Feature 5)
    9.  Send WhatsApp/Telegram notification (Feature 1)
    10. Return summary
    """

    async def log(message: str):
        await append_agent_log(procurement_id, message, db)

    try:
        # STEP 1: Parse spec
        await update_procurement_status(
            procurement_id, ProcurementStatus.PARSING,
            "Parsing product specification...", db
        )
        await log("🧠 Parsing your product description...")
        spec = await parse_spec(raw_description)
        await log(
            f"✅ Parsed: {spec['product_name']} · "
            f"qty: {spec.get('quantity')} {spec.get('unit')} · "
            f"category: {spec['category']}"
        )

        # STEP 2: Get user profile
        result = await db.execute(select(User).where(User.id == user_id))
        user   = result.scalar_one_or_none()

        company_profile = {
            "company_name":   user.company_name    or "My Company",
            "contact_person": user.contact_person  or user.full_name or "",
            "email":          user.email,
            "phone":          user.company_phone   or "",
            "address":        user.company_address or "",
            "payment_terms":  user.payment_terms   or "Net 30",
            "gst_number":     user.gst_number      or ""
        }

        # STEP 3: Match suppliers
        await update_procurement_status(
            procurement_id, ProcurementStatus.RUNNING,
            "Finding suppliers...", db
        )
        suppliers = await match_suppliers(spec["category"], user_id, db, limit=5)
        await log(
            f"🔍 Found {len(suppliers)} suppliers: "
            f"{', '.join(s['name'] for s in suppliers)}"
        )

        # STEP 4: Run agents in parallel
        await log("🤖 Launching browser agents in parallel...")

        async def run_one(supplier):
            start  = time.time()
            result = await run_supplier_agent(
                supplier=supplier,
                product_spec=spec,
                company_profile=company_profile,
                on_status=log
            )
            elapsed = time.time() - start
            # Feature 10 - record reliability data
            try:
                await record_quote_attempt(
                    supplier_name=supplier["name"],
                    supplier_url=supplier["website_url"],
                    success=(result.get("status") != "failed"),
                    response_time_s=elapsed,
                    db=db
                )
            except Exception:
                pass
            return result

        quotes_raw = await asyncio.gather(
            *[run_one(s) for s in suppliers],
            return_exceptions=True
        )

        quotes = []
        for q in quotes_raw:
            if isinstance(q, Exception):
                await log(f"⚠️ Agent error: {str(q)[:80]}")
            else:
                quotes.append(q)

        successful = [q for q in quotes if q.get("status") != "failed"]
        failed     = [q for q in quotes if q.get("status") == "failed"]
        await log(
            f"📊 Received {len(successful)} quotes · "
            f"{len(failed)} failed out of {len(suppliers)} suppliers"
        )

        # STEP 5: Normalize currencies to INR (Feature 8)
        if successful:
            await log("💱 Normalizing currencies to INR...")
            quotes = await normalize_quotes_currency(quotes)

        # STEP 6: Rank quotes
        await log("⚖️ Ranking quotes by price, delivery, and reliability...")
        ranked_quotes = await rank_quotes(quotes, spec)

        # STEP 7: Save quotes + validity records
        for q in ranked_quotes:
            saved = await save_quote(procurement_id, q, db)
            # Feature 5 - track quote validity/expiry
            if q.get("status") == "received":
                try:
                    await create_validity_record(
                        quote_id=saved.id,
                        procurement_id=procurement_id,
                        user_id=user_id,
                        supplier_name=q.get("supplier_name", ""),
                        valid_days=30,
                        db=db
                    )
                except Exception:
                    pass

        # STEP 8: Summary
        summary = await summarize_results(ranked_quotes, spec)
        await log(f"💡 {summary}")

        # STEP 9: Send notifications (Feature 1)
        try:
            await notify_quotes_ready(
                user_phone    =getattr(user, "phone_number", None),
                user_telegram =getattr(user, "telegram_chat_id", None),
                product_name  =spec.get("product_name", raw_description[:50]),
                quotes        =ranked_quotes,
                procurement_id=str(procurement_id)
            )
            await log("📱 Notification sent")
        except Exception as e:
            await log(f"⚠️ Notification failed (non-critical): {str(e)[:60]}")

        # STEP 10: Mark complete
        await update_procurement_status(
            procurement_id,
            ProcurementStatus.COMPLETED,
            f"Done — {len(successful)} quotes received",
            db
        )

        return {
            "status":       "completed",
            "quotes_count": len(successful),
            "summary":      summary,
            "top_quote":    ranked_quotes[0] if ranked_quotes else None
        }

    except Exception as e:
        await log(f"❌ Pipeline failed: {str(e)}")
        await update_procurement_status(
            procurement_id, ProcurementStatus.FAILED, str(e), db
        )
        raise