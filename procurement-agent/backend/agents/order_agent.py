"""
order_agent.py
────────────────────────────────────────────────────────────────────
Agent that places actual orders with suppliers after user selects a quote.

Called when user clicks "Place Order" on a selected quote.
Navigates to supplier portal, fills order form, and confirms purchase.
"""

import asyncio
import uuid
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta

from services.tinyfish_client import TinyFishClient
from services.email_service import send_order_email


async def place_order_with_supplier(
    quote_id: uuid.UUID,
    user_id: uuid.UUID,
    db,
    on_status: Optional[Callable] = None
) -> Dict:
    """
    Main entry point - place order with supplier.
    
    Args:
        quote_id: ID of the selected quote
        user_id: User who is placing the order
        db: Database session
        on_status: Function for status logging
    
    Returns:
        {
            "status": "success" | "failed",
            "order_number": str,
            "supplier_name": str,
            "expected_delivery": str,
            "confirmation_url": str,
            "screenshot_url": str,
            "method": "portal" | "email",
            "error": str (if failed)
        }
    """
    
    agent = OrderAgent(on_status)
    return await agent.place_order(quote_id, user_id, db)


async def run_order_agent(
    supplier_url: str,
    supplier_name: str,
    quote_ref_id: Optional[str],
    product_spec: Dict,
    company_profile: Dict,
    quantity: int,
) -> Dict:
    """Compatibility wrapper used by routes/orders.py."""
    return {
        "order_id": quote_ref_id or f"PENDING-{uuid.uuid4().hex[:8].upper()}",
        "invoice_number": None,
        "total_amount": product_spec.get("expected_unit_price"),
        "estimated_delivery": "TBD",
        "status": "placing",
        "supplier_name": supplier_name,
        "supplier_url": supplier_url,
        "quantity": quantity,
    }


class OrderAgent:
    """
    Agent that handles order placement with suppliers.
    """
    
    def __init__(self, logger: Optional[Callable] = None):
        """
        Initialize order agent.
        
        Args:
            logger: Optional function for status logging
        """
        self.log = logger or (lambda msg: print(msg))
        self.tinyfish = None
        self.session_id = None
        self.timeout = 60
    
    
    async def place_order(
        self,
        quote_id: uuid.UUID,
        user_id: uuid.UUID,
        db
    ) -> Dict:
        """
        Place order with supplier based on selected quote.
        """
        try:
            await self.log("🛒 Starting order placement...")
            
            # STEP 1: Get quote and related data from database
            order_data = await self._get_order_data(quote_id, user_id, db)
            
            if not order_data:
                raise Exception("Quote or user data not found")
            
            supplier_name = order_data["supplier_name"]
            await self.log(f"📋 Placing order with {supplier_name}...")
            
            # STEP 2: Try portal-based ordering first
            if order_data.get("supplier_portal_url"):
                portal_result = await self._place_order_via_portal(order_data)
                
                if portal_result["success"]:
                    # Save order to database
                    await self._save_order_to_db(
                        quote_id,
                        user_id,
                        portal_result,
                        "portal",
                        db
                    )
                    
                    await self.log(f"✅ Order placed successfully!")
                    
                    return {
                        "status": "success",
                        "order_number": portal_result.get("order_number", ""),
                        "supplier_name": supplier_name,
                        "expected_delivery": portal_result.get("expected_delivery", ""),
                        "confirmation_url": portal_result.get("confirmation_url", ""),
                        "screenshot_url": portal_result.get("screenshot_url", ""),
                        "method": "portal"
                    }
            
            # STEP 3: Fallback to email ordering
            await self.log("📧 Portal ordering unavailable - sending order via email...")
            
            email_result = await self._place_order_via_email(order_data)
            
            if email_result["success"]:
                # Save order to database
                await self._save_order_to_db(
                    quote_id,
                    user_id,
                    email_result,
                    "email",
                    db
                )
                
                await self.log(f"✅ Order email sent successfully!")
                
                return {
                    "status": "success",
                    "order_number": email_result.get("order_reference", "Pending"),
                    "supplier_name": supplier_name,
                    "expected_delivery": "TBD",
                    "confirmation_url": "",
                    "screenshot_url": "",
                    "method": "email",
                    "message": "Order placed via email - awaiting confirmation"
                }
            else:
                raise Exception(f"Email ordering failed: {email_result.get('error')}")
        
        except Exception as e:
            await self.log(f"❌ Order placement failed: {str(e)}")
            
            return {
                "status": "failed",
                "supplier_name": order_data.get("supplier_name", "Unknown"),
                "error": str(e),
                "method": "none"
            }
        
        finally:
            await self._cleanup()
    
    
    async def _get_order_data(
        self,
        quote_id: uuid.UUID,
        user_id: uuid.UUID,
        db
    ) -> Optional[Dict]:
        """
        Fetch all data needed for order placement.
        
        Returns:
            {
                "quote": Quote object,
                "supplier": Supplier object,
                "user": User object,
                "product_spec": dict,
                "company_profile": dict,
                ...
            }
        """
        try:
            from models.quote import Quote
            from models.supplier import Supplier
            from models.user import User
            from models.procurement import ProcurementRequest
            from sqlalchemy import select
            
            # Get quote
            result = await db.execute(
                select(Quote).where(Quote.id == quote_id)
            )
            quote = result.scalar_one_or_none()
            
            if not quote:
                return None
            
            # Get supplier
            result = await db.execute(
                select(Supplier).where(Supplier.name == quote.supplier_name)
            )
            supplier = result.scalar_one_or_none()
            
            # Get user
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                return None
            
            # Get procurement request for product details
            result = await db.execute(
                select(ProcurementRequest).where(
                    ProcurementRequest.id == quote.procurement_id
                )
            )
            procurement = result.scalar_one_or_none()
            
            return {
                "quote_id": quote_id,
                "supplier_name": quote.supplier_name,
                "supplier_url": supplier.website_url if supplier else "",
                "supplier_portal_url": supplier.order_portal_url if supplier else None,
                "requires_login": supplier.requires_login if supplier else False,
                "login_url": supplier.login_url if supplier else None,
                "credentials": supplier.login_credentials if supplier else {},
                
                "product_name": procurement.product_spec_parsed.get("product_name", "") if procurement else "",
                "quantity": quote.quantity,
                "unit": procurement.product_spec_parsed.get("unit", "units") if procurement else "units",
                "price_per_unit": quote.price_per_unit,
                "total_price": quote.total_price,
                "currency": quote.currency,
                
                "quote_reference": quote.quote_reference,
                "quote_url": quote.quote_url,
                
                "company_name": user.company_name or "",
                "contact_person": user.contact_person or user.full_name or "",
                "email": user.email,
                "phone": user.company_phone or "",
                "billing_address": user.company_address or "",
                "shipping_address": user.delivery_address or user.company_address or "",
                "gst_number": user.gst_number or "",
                "payment_terms": user.payment_terms or "Net 30",
                "po_number": self._generate_po_number(user.company_name or "")
            }
        
        except Exception as e:
            await self.log(f"⚠️ Error fetching order data: {str(e)}")
            return None
    
    
    def _generate_po_number(self, company_name: str) -> str:
        """
        Generate a purchase order number.
        
        Format: PO-COMPANY-YYYYMMDD-XXXX
        Example: PO-ACME-20260323-0001
        """
        date_str = datetime.utcnow().strftime("%Y%m%d")
        random_suffix = str(uuid.uuid4())[:4].upper()
        company_prefix = company_name[:4].upper().replace(" ", "") if company_name else "COMP"
        
        return f"PO-{company_prefix}-{date_str}-{random_suffix}"
    
    
    async def _place_order_via_portal(self, order_data: Dict) -> Dict:
        """
        Place order through supplier's web portal.
        
        Returns:
            {
                "success": bool,
                "order_number": str,
                "expected_delivery": str,
                "confirmation_url": str,
                "screenshot_url": str,
                "error": str
            }
        """
        try:
            await self.log("🌐 Navigating to supplier portal...")
            
            # Initialize TinyFish
            self.tinyfish = TinyFishClient()
            
            # Navigate to portal
            portal_url = order_data["supplier_portal_url"]
            result = await self.tinyfish.navigate(
                url=portal_url,
                wait_for_selector="body",
                timeout=self.timeout
            )
            
            if result.get("status") != "success":
                return {"success": False, "error": "Navigation failed"}
            
            self.session_id = result["session_id"]
            await asyncio.sleep(2)
            
            # Login if required
            if order_data["requires_login"]:
                await self.log("🔐 Logging in...")
                login_result = await self._login_to_portal(order_data)
                
                if not login_result["success"]:
                    return {"success": False, "error": f"Login failed: {login_result.get('error')}"}
            
            # Find order/checkout page
            await self.log("📝 Finding order form...")
            order_page_result = await self._navigate_to_order_form(order_data)
            
            if not order_page_result["success"]:
                return {"success": False, "error": "Could not find order form"}
            
            # Fill order form
            await self.log("✍️ Filling order details...")
            fill_result = await self._fill_order_form(order_data)
            
            if not fill_result["success"]:
                return {"success": False, "error": f"Form filling failed: {fill_result.get('error')}"}
            
            # Review order (if there's a review page)
            await self.log("👀 Reviewing order...")
            await asyncio.sleep(2)
            
            # Confirm/Submit order
            await self.log("🚀 Submitting order...")
            submit_result = await self._submit_order()
            
            if not submit_result["success"]:
                return {"success": False, "error": f"Submission failed: {submit_result.get('error')}"}
            
            # Wait for confirmation page
            await asyncio.sleep(3)
            
            # Extract order confirmation
            await self.log("📋 Extracting order confirmation...")
            confirmation = await self._extract_order_confirmation()
            
            # Take screenshot
            screenshot = await self._take_screenshot()
            
            return {
                "success": True,
                "order_number": confirmation.get("order_number", ""),
                "expected_delivery": confirmation.get("expected_delivery", ""),
                "confirmation_url": await self._get_current_url(),
                "screenshot_url": screenshot
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    
    async def _login_to_portal(self, order_data: Dict) -> Dict:
        """
        Login to supplier portal.
        """
        try:
            credentials = order_data.get("credentials", {})
            
            if not credentials:
                return {"success": False, "error": "No credentials"}
            
            # Navigate to login if separate URL
            login_url = order_data.get("login_url")
            if login_url:
                await self.tinyfish.navigate(
                    url=login_url,
                    session_id=self.session_id
                )
                await asyncio.sleep(2)
            
            # Fill username
            username_field = await self.tinyfish.find_element(
                self.session_id,
                selector='input[type="email"], input[name*="email"], input[name*="username"]'
            )
            
            if username_field:
                await self.tinyfish.fill_input(
                    self.session_id,
                    username_field["id"],
                    credentials.get("username") or credentials.get("email")
                )
            
            # Fill password
            password_field = await self.tinyfish.find_element(
                self.session_id,
                selector='input[type="password"]'
            )
            
            if password_field:
                await self.tinyfish.fill_input(
                    self.session_id,
                    password_field["id"],
                    credentials.get("password")
                )
            
            # Click login
            login_button = await self.tinyfish.find_element(
                self.session_id,
                selector='button[type="submit"], button:contains("Login"), button:contains("Sign In")'
            )
            
            if login_button:
                await self.tinyfish.click_element(
                    self.session_id,
                    login_button["id"]
                )
                await asyncio.sleep(3)
            
            return {"success": True}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    
    async def _navigate_to_order_form(self, order_data: Dict) -> Dict:
        """
        Navigate to order/checkout page.
        """
        try:
            page_html = await self.tinyfish.get_page_content(self.session_id)
            
            # Look for order-related links
            order_links = [
                "place order",
                "checkout",
                "convert to order",
                "accept quote",
                "proceed to order",
                "buy now",
                "purchase"
            ]
            
            for link_text in order_links:
                link = await self.tinyfish.find_element(
                    self.session_id,
                    selector=f'a:contains("{link_text}"), button:contains("{link_text}")'
                )
                
                if link:
                    await self.tinyfish.click_element(
                        self.session_id,
                        link["id"]
                    )
                    await asyncio.sleep(2)
                    return {"success": True}
            
            # If we have a quote reference, try to search for it
            if order_data.get("quote_reference"):
                # Look for the quote in "My Quotes" or similar
                quotes_link = await self.tinyfish.find_element(
                    self.session_id,
                    selector='a:contains("My Quotes"), a:contains("Quotes"), a:contains("RFQs")'
                )
                
                if quotes_link:
                    await self.tinyfish.click_element(
                        self.session_id,
                        quotes_link["id"]
                    )
                    await asyncio.sleep(2)
            
            return {"success": True}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    
    async def _fill_order_form(self, order_data: Dict) -> Dict:
        """
        Fill order form with all required details.
        """
        try:
            fields_to_fill = {
                # Quote reference
                "quote_reference": order_data.get("quote_reference", ""),
                "quote_number": order_data.get("quote_reference", ""),
                "rfq_number": order_data.get("quote_reference", ""),
                
                # PO details
                "po_number": order_data.get("po_number", ""),
                "purchase_order": order_data.get("po_number", ""),
                
                # Company info
                "company_name": order_data.get("company_name", ""),
                "company": order_data.get("company_name", ""),
                
                # Contact
                "contact_person": order_data.get("contact_person", ""),
                "name": order_data.get("contact_person", ""),
                "email": order_data.get("email", ""),
                "phone": order_data.get("phone", ""),
                
                # Addresses
                "billing_address": order_data.get("billing_address", ""),
                "shipping_address": order_data.get("shipping_address", ""),
                "delivery_address": order_data.get("shipping_address", ""),
                
                # Product (if needed)
                "product": order_data.get("product_name", ""),
                "quantity": order_data.get("quantity", ""),
                
                # Payment
                "payment_terms": order_data.get("payment_terms", ""),
                "gst_number": order_data.get("gst_number", ""),
                
                # Notes
                "notes": f"Order for quote {order_data.get('quote_reference', '')}",
                "special_instructions": ""
            }
            
            # Get form fields
            form_fields = await self.tinyfish.extract_form_fields(self.session_id)
            
            filled_count = 0
            
            for field in form_fields:
                field_name = field.get("name", "").lower()
                field_id = field.get("id", "")
                
                # Match field to our data
                for key, value in fields_to_fill.items():
                    if key in field_name or key in field_id.lower():
                        if value:
                            try:
                                await self.tinyfish.fill_input(
                                    self.session_id,
                                    field_id,
                                    str(value)
                                )
                                filled_count += 1
                            except Exception:
                                pass
                        break
            
            await self.log(f"  ✓ Filled {filled_count} fields")
            
            return {"success": True, "fields_filled": filled_count}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    
    async def _submit_order(self) -> Dict:
        """
        Find and click order submission button.
        """
        try:
            # Find submit button
            submit_button = await self.tinyfish.find_element(
                self.session_id,
                selector='button:contains("Confirm"), button:contains("Place Order"), button:contains("Submit Order"), button:contains("Complete Purchase"), button[type="submit"]'
            )
            
            if submit_button:
                await self.tinyfish.click_element(
                    self.session_id,
                    submit_button["id"]
                )
                return {"success": True}
            else:
                return {"success": False, "error": "Submit button not found"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    
    async def _extract_order_confirmation(self) -> Dict:
        """
        Extract order number and delivery date from confirmation page.
        """
        try:
            page_html = await self.tinyfish.get_page_content(self.session_id)
            
            import re
            
            result = {
                "order_number": "",
                "expected_delivery": ""
            }
            
            # Extract order number
            order_patterns = [
                r'Order\s*#?\s*([A-Z0-9-]+)',
                r'Order\s*Number:\s*([A-Z0-9-]+)',
                r'PO\s*#?\s*([A-Z0-9-]+)',
                r'Confirmation\s*#?\s*([A-Z0-9-]+)'
            ]
            
            for pattern in order_patterns:
                match = re.search(pattern, page_html, re.IGNORECASE)
                if match:
                    result["order_number"] = match.group(1)
                    break
            
            # Extract delivery date
            delivery_patterns = [
                r'Expected\s*Delivery:\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'Delivery\s*Date:\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'Ships\s*by:\s*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
                r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
            ]
            
            for pattern in delivery_patterns:
                match = re.search(pattern, page_html, re.IGNORECASE)
                if match:
                    result["expected_delivery"] = match.group(1)
                    break
            
            return result
        
        except Exception:
            return {"order_number": "", "expected_delivery": ""}
    
    
    async def _place_order_via_email(self, order_data: Dict) -> Dict:
        """
        Send order via email as fallback.
        """
        try:
            # Compose order email
            email_body = f"""
Dear {order_data['supplier_name']},

We would like to proceed with placing an order based on the following quote:

QUOTE DETAILS:
- Quote Reference: {order_data.get('quote_reference', 'N/A')}
- Product: {order_data.get('product_name', '')}
- Quantity: {order_data.get('quantity', '')} {order_data.get('unit', 'units')}
- Unit Price: {order_data.get('currency', 'USD')} {order_data.get('price_per_unit', '')}
- Total Amount: {order_data.get('currency', 'USD')} {order_data.get('total_price', '')}

PURCHASE ORDER:
- PO Number: {order_data.get('po_number', '')}
- Payment Terms: {order_data.get('payment_terms', 'Net 30')}

COMPANY DETAILS:
- Company Name: {order_data.get('company_name', '')}
- Contact Person: {order_data.get('contact_person', '')}
- Email: {order_data.get('email', '')}
- Phone: {order_data.get('phone', '')}
- GST Number: {order_data.get('gst_number', 'N/A')}

BILLING ADDRESS:
{order_data.get('billing_address', '')}

SHIPPING ADDRESS:
{order_data.get('shipping_address', '')}

Please confirm this order and send the invoice to {order_data.get('email', '')}.

Thank you,
{order_data.get('company_name', '')}
{order_data.get('contact_person', '')}
"""
            
            # Send email
            email_result = await send_order_email(
                to_email=order_data.get("supplier_email", ""),  # Need supplier email
                subject=f"Purchase Order - {order_data.get('po_number', '')}",
                body=email_body,
                from_name=order_data.get("company_name", ""),
                from_email=order_data.get("email", "")
            )
            
            if email_result.get("success"):
                return {
                    "success": True,
                    "order_reference": order_data.get("po_number", "")
                }
            else:
                return {
                    "success": False,
                    "error": email_result.get("error", "Email send failed")
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    
    async def _save_order_to_db(
        self,
        quote_id: uuid.UUID,
        user_id: uuid.UUID,
        order_result: Dict,
        method: str,
        db
    ):
        """
        Save order record to database.
        """
        try:
            from models.order import Order
            
            order = Order(
                id=uuid.uuid4(),
                quote_id=quote_id,
                user_id=user_id,
                order_number=order_result.get("order_number", ""),
                order_method=method,
                expected_delivery=order_result.get("expected_delivery"),
                confirmation_url=order_result.get("confirmation_url", ""),
                screenshot_url=order_result.get("screenshot_url", ""),
                status="placed",
                created_at=datetime.utcnow()
            )
            
            db.add(order)
            await db.commit()
            
            # Update quote status
            from models.quote import Quote
            from sqlalchemy import update
            
            await db.execute(
                update(Quote)
                .where(Quote.id == quote_id)
                .values(status="ordered")
            )
            await db.commit()
        
        except Exception as e:
            await self.log(f"⚠️ Database save error: {str(e)}")
            await db.rollback()
    
    
    async def _take_screenshot(self) -> str:
        """
        Take screenshot of confirmation page.
        """
        try:
            screenshot_result = await self.tinyfish.get_screenshot(self.session_id)
            
            if screenshot_result.get("status") == "success":
                return screenshot_result.get("screenshot_url", "")
            else:
                return ""
        except Exception:
            return ""
    
    
    async def _get_current_url(self) -> str:
        """
        Get current page URL.
        """
        try:
            result = await self.tinyfish.get_current_url(self.session_id)
            return result.get("url", "")
        except Exception:
            return ""
    
    
    async def _cleanup(self):
        """
        Clean up TinyFish session.
        """
        try:
            if self.tinyfish and self.session_id:
                await self.tinyfish.close_session(self.session_id)
        except Exception:
            pass