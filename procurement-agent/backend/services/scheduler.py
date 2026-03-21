from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import select, and_
from datetime import datetime, timedelta
import uuid
 
from models.base import AsyncSessionLocal
from models.procurement import ProcurementRequest, ProcurementStatus
from models.quote import Quote, QuoteStatus
from models.user import User
from services.validity_service import get_expiring_quotes, QuoteValidity
from services.notification_service import notify_quotes_ready
from services.email_service import send_quote_summary_email
from agents.monitor_agent import run_monitor_agent
 
scheduler = AsyncIOScheduler()
 
 
async def check_active_quotes():
    """
    Daily job — runs monitor_agent on all active quotes
    that have a reference ID from the supplier.
    """
    print(f"[Scheduler] Running daily quote check at {datetime.utcnow()}")
 
    async with AsyncSessionLocal() as db:
        # Get all received quotes with reference IDs
        result = await db.execute(
            select(Quote).where(
                Quote.status == QuoteStatus.RECEIVED,
                Quote.raw_extracted_data.isnot(None)
            ).limit(50)
        )
        quotes = result.scalars().all()
 
        checked = 0
        for quote in quotes:
            ref_id = (quote.raw_extracted_data or {}).get("reference_id")
            if ref_id and quote.supplier_url:
                try:
                    status = await run_monitor_agent(
                        supplier_url=quote.supplier_url,
                        reference_id=ref_id,
                        company_email="check@procurement.ai"
                    )
                    print(f"[Scheduler] {quote.supplier_name}: {status.get('current_status')}")
                    checked += 1
                except Exception as e:
                    print(f"[Scheduler] Monitor failed for {quote.supplier_name}: {e}")
 
        print(f"[Scheduler] Checked {checked} quotes")
 
 
async def send_expiry_alerts():
    """
    Daily job — send alerts for quotes expiring within 7 days.
    """
    print(f"[Scheduler] Running expiry check at {datetime.utcnow()}")
 
    async with AsyncSessionLocal() as db:
        expiring = await get_expiring_quotes(db, days_threshold=7)
 
        for record in expiring:
            # Get user details
            user_result = await db.execute(
                select(User).where(User.id == record.user_id)
            )
            user = user_result.scalar_one_or_none()
            if not user:
                continue
 
            days_left = (record.expires_at - datetime.utcnow()).days
 
            message = f"""
⚠️ *Quote Expiring Soon!*
 
Supplier: *{record.supplier_name}*
Expires in: *{days_left} days*
 
Act now before this quote expires.
View: http://localhost:3000/quotes/{record.procurement_id}
            """.strip()
 
            # Send notification
            if user.phone_number:
                from services.notification_service import send_whatsapp
                await send_whatsapp(user.phone_number, message)
 
            if user.telegram_chat_id:
                from services.notification_service import send_telegram
                await send_telegram(user.telegram_chat_id, message)
 
            # Mark alert as sent
            record.alert_7day_sent = True
            await db.commit()
 
        print(f"[Scheduler] Sent {len(expiring)} expiry alerts")
 
 
async def send_daily_digest():
    """
    Daily job — send each user a summary of their active procurement jobs.
    """
    print(f"[Scheduler] Sending daily digests at {datetime.utcnow()}")
 
    async with AsyncSessionLocal() as db:
        # Get all active users with pending/running jobs
        result = await db.execute(
            select(User).where(User.is_active == True)
        )
        users = result.scalars().all()
 
        for user in users:
            # Get their recent completed jobs
            jobs_result = await db.execute(
                select(ProcurementRequest).where(
                    ProcurementRequest.user_id == user.id,
                    ProcurementRequest.status == ProcurementStatus.COMPLETED,
                    ProcurementRequest.created_at >= datetime.utcnow() - timedelta(days=7)
                ).limit(5)
            )
            jobs = jobs_result.scalars().all()
 
            if not jobs:
                continue
 
            # Build digest message
            digest = f"📋 *Your Weekly Procurement Digest*\n\n"
            for job in jobs:
                digest += f"• {job.raw_description[:50]}... → ✅ {job.status}\n"
 
            if user.telegram_chat_id:
                from services.notification_service import send_telegram
                await send_telegram(user.telegram_chat_id, digest)
 
 
def start_scheduler():
    """
    Register all scheduled jobs and start the scheduler.
    Called from main.py on app startup.
    """
    # Check active quotes every day at 9 AM
    scheduler.add_job(
        check_active_quotes,
        CronTrigger(hour=9, minute=0),
        id="check_active_quotes",
        replace_existing=True
    )
 
    # Send expiry alerts every day at 9:05 AM
    scheduler.add_job(
        send_expiry_alerts,
        CronTrigger(hour=9, minute=5),
        id="send_expiry_alerts",
        replace_existing=True
    )
 
    # Send daily digest every day at 9:10 AM
    scheduler.add_job(
        send_daily_digest,
        CronTrigger(hour=9, minute=10),
        id="send_daily_digest",
        replace_existing=True
    )
 
    scheduler.start()
    print("[Scheduler] Started — daily jobs scheduled at 9 AM")
 
 
def stop_scheduler():
    """Called on app shutdown."""
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] Stopped")