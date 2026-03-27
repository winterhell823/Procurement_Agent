"""
Email service using Twilio SendGrid API.
Handles sending notifications, quote summaries, order confirmations, etc.
Async wrapper around sync SendGrid SDK for compatibility with FastAPI.
"""

import logging
from typing import Optional, List
import asyncio

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content, Personalization
from config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """
    Async service for sending emails via SendGrid.
    Uses official sendgrid-python SDK with asyncio.to_thread for non-blocking calls.
    """

    def __init__(self):
        if not settings.SENDGRID_API_KEY:
            logger.warning("SENDGRID_API_KEY not set — email sending disabled")
            self.client = None
        else:
            self.client = SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)
            logger.info("EmailService initialized with SendGrid client")

    async def send_email(
        self,
        to_emails: List[str],
        subject: str,
        plain_text: Optional[str] = None,
        html_content: Optional[str] = None,
        from_email: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """
        Send a single email (supports text or HTML).

        Args:
            to_emails: List of recipient emails
            subject: Email subject
            plain_text: Optional plain text body
            html_content: Optional HTML body (preferred for formatted emails)
            from_email: Override default FROM_EMAIL
            reply_to: Optional reply-to address

        Returns:
            True if sent successfully (202 status), False otherwise
        """
        if not self.client:
            logger.error("Cannot send email: SENDGRID_API_KEY missing")
            return False

        from_email = from_email or settings.FROM_EMAIL
        if not from_email:
            logger.error("No from_email provided or set in config")
            return False

        # Build personalization for multiple To
        personalization = Personalization()
        for email in to_emails:
            personalization.add_to(To(email))

        mail = Mail(
            from_email=Email(from_email),
            subject=subject,
        )
        mail.add_personalization(personalization)

        if html_content:
            mail.add_content(Content("text/html", html_content))
        if plain_text:
            mail.add_content(Content("text/plain", plain_text))

        if reply_to:
            mail.reply_to = Email(reply_to)

        try:
            # Run sync SendGrid call in thread to keep async
            response = await asyncio.to_thread(
                lambda: self.client.send(mail)
            )
            status = response.status_code
            if status == 202:
                logger.info(f"Email sent successfully to {to_emails} | subject: {subject}")
                return True
            else:
                logger.warning(f"SendGrid response {status}: {response.body}")
                return False

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    async def send_quote_summary(
        self,
        to_email: str,
        procurement_id: str,
        best_quote: dict,
        all_quotes_count: int,
    ) -> bool:
        """
        Convenience: Send summary of quotes to user after procurement completes.
        """
        subject = f"Procurement Update: {procurement_id} - {all_quotes_count} Quotes Received"

        html = f"""
        <h2>Best Quote Found!</h2>
        <p>Supplier: <strong>{best_quote.get('supplier_name', 'N/A')}</strong></p>
        <p>Total Price: <strong>{best_quote.get('total_price', 'N/A')} {best_quote.get('currency', 'INR')}</strong></p>
        <p>Delivery: {best_quote.get('delivery_days', 'N/A')} days</p>
        <p>View full details in dashboard.</p>
        <p>Procurement ID: {procurement_id}</p>
        """

        return await self.send_email(
            to_emails=[to_email],
            subject=subject,
            html_content=html,
            plain_text=html.replace("<strong>", "").replace("</strong>", "").replace("<h2>", "").replace("</h2>", "\n"),
        )

    async def send_order_confirmation(
        self,
        to_email: str,
        order_data: dict,
    ) -> bool:
        """
        Send confirmation after auto-ordering with best supplier.
        """
        subject = f"Order Placed: {order_data.get('order_number', 'Procurement')}"

        html = f"""
        <h2>Order Confirmed!</h2>
        <p>Supplier: {order_data.get('supplier_name', 'N/A')}</p>
        <p>Reference: {order_data.get('quote_reference', 'N/A')}</p>
        <p>We'll notify you when updates arrive.</p>
        """

        return await self.send_email(
            to_emails=[to_email],
            subject=subject,
            html_content=html,
        )


# Global singleton instance (like other services)
email_service = EmailService()


async def send_order_email(
    to_email: str,
    subject: str,
    body: str,
    from_name: Optional[str] = None,
    from_email: Optional[str] = None,
) -> dict:
    """Compatibility helper for order workflow email fallback."""
    if not to_email:
        return {"success": False, "error": "Missing supplier recipient email"}

    ok = await email_service.send_email(
        to_emails=[to_email],
        subject=subject,
        plain_text=body,
        from_email=from_email,
    )
    return {"success": ok, "error": None if ok else "Failed to send email"}