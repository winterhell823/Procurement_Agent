"""
monitor_agent.py
────────────────────────────────────────────────────────────────────
Background agent that checks back on pending quotes.

When suppliers don't provide immediate quotes, they often say "we'll email you"
or "check back in 24 hours". This agent logs into their portals and checks
if quotes are now available.

Runs as a scheduled background job every 4 hours.
"""

import asyncio
from typing import Dict, List, Optional, Callable
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from services.tinyfish_client import TinyFishClient
from services.llm_service import extract_quote_from_html
from services.db_service import update_quote_status, save_quote
from models.quote import Quote
from models.procurement import ProcurementRequest


class MonitorAgent:
    """
    Agent that follows up on pending quotes.
    
    Responsibilities:
    - Check quotes marked as "pending" in database
    - Log into supplier portals
    - Check if quote status has changed
    - Extract quote data if now available
    - Update database with new information
    """
    
    def __init__(self, logger: Optional[Callable] = None):
        """
        Initialize monitor agent.
        
        Args:
            logger: Optional function for status logging
        """
        self.log = logger or (lambda msg: print(msg))
        self.tinyfish = None
        self.session_id = None
        self.timeout = 60
    
    
    async def check_pending_quotes(self, db: AsyncSession) -> Dict:
        """
        Main entry point - check all pending quotes.
        
        Args:
            db: Database session
        
        Returns:
            {
                "checked": int,
                "updated": int,
                "still_pending": int,
                "failed": int
            }
        """
        try:
            await self.log("🔍 Starting pending quote check...")
            
            # STEP 1: Get all pending quotes older than 24 hours
            pending_quotes = await self._get_pending_quotes(db)
            
            if not pending_quotes:
                await self.log("✅ No pending quotes to check")
                return {
                    "checked": 0,
                    "updated": 0,
                    "still_pending": 0,
                    "failed": 0
                }
            
            await self.log(f"📊 Found {len(pending_quotes)} pending quotes to check")
            
            # STEP 2: Check each quote
            results = {
                "checked": 0,
                "updated": 0,
                "still_pending": 0,
                "failed": 0
            }
            
            for quote in pending_quotes:
                try:
                    await self.log(f"🌐 Checking {quote.supplier_name}...")
                    
                    result = await self._check_single_quote(quote, db)
                    
                    results["checked"] += 1
                    
                    if result["status"] == "updated":
                        results["updated"] += 1
                        await self.log(f"✅ {quote.supplier_name}: Quote received!")
                    elif result["status"] == "still_pending":
                        results["still_pending"] += 1
                        await self.log(f"⏳ {quote.supplier_name}: Still pending")
                    else:
                        results["failed"] += 1
                        await self.log(f"⚠️ {quote.supplier_name}: Check failed")
                    
                    # Small delay between checks
                    await asyncio.sleep(3)
                
                except Exception as e:
                    results["failed"] += 1
                    await self.log(f"❌ Error checking {quote.supplier_name}: {str(e)}")
            
            # STEP 3: Summary
            await self.log(
                f"📈 Summary: {results['updated']} updated, "
                f"{results['still_pending']} still pending, "
                f"{results['failed']} failed"
            )
            
            return results
        
        except Exception as e:
            await self.log(f"❌ Monitor agent error: {str(e)}")
            raise
    
    
    async def _get_pending_quotes(self, db: AsyncSession) -> List[Quote]:
        """
        Fetch pending quotes from database.
        
        Only returns quotes that:
        - Status is "pending"
        - Created more than 24 hours ago
        - Not expired
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            query = select(Quote).where(
                and_(
                    Quote.status == "pending",
                    Quote.created_at < cutoff_time,
                    Quote.is_expired == False
                )
            ).order_by(Quote.created_at.asc())
            
            result = await db.execute(query)
            quotes = result.scalars().all()
            
            return list(quotes)
        
        except Exception as e:
            await self.log(f"⚠️ Database query error: {str(e)}")
            return []
    
    
    async def _check_single_quote(self, quote: Quote, db: AsyncSession) -> Dict:
        """
        Check status of a single pending quote.
        
        Args:
            quote: Quote object from database
            db: Database session
        
        Returns:
            {
                "status": "updated" | "still_pending" | "failed",
                "data": dict (if updated)
            }
        """
        try:
            # STEP 1: Initialize TinyFish
            self.tinyfish = TinyFishClient()
            
            # STEP 2: Get supplier info
            supplier_info = await self._get_supplier_info(quote, db)
            
            if not supplier_info:
                return {"status": "failed", "error": "No supplier info"}
            
            # STEP 3: Navigate to supplier portal
            navigation_result = await self._navigate_to_portal(
                supplier_info,
                quote.quote_url or supplier_info.get("website_url")
            )
            
            if not navigation_result["success"]:
                return {"status": "failed", "error": "Navigation failed"}
            
            self.session_id = navigation_result["session_id"]
            
            # STEP 4: Login if needed
            if supplier_info.get("requires_login"):
                login_result = await self._login_to_portal(supplier_info)
                if not login_result["success"]:
                    await self.log(f"  ⚠️ Login failed: {login_result.get('error')}")
                    # Try to continue without login
            
            # STEP 5: Find quote status page
            status_page_result = await self._navigate_to_quote_status(
                quote,
                supplier_info
            )
            
            if not status_page_result["success"]:
                return {"status": "failed", "error": "Could not find quote status"}
            
            # STEP 6: Check if quote is ready
            quote_status = await self._extract_quote_status()
            
            if quote_status == "ready":
                # Quote is now available!
                await self.log(f"  💰 Quote is ready - extracting data...")
                
                quote_data = await self._extract_quote_data_from_portal(quote)
                
                if quote_data:
                    # Update the quote in database
                    await self._update_quote_in_db(quote, quote_data, db)
                    
                    return {
                        "status": "updated",
                        "data": quote_data
                    }
                else:
                    return {"status": "failed", "error": "Could not extract quote data"}
            
            elif quote_status == "pending":
                # Still waiting
                return {"status": "still_pending"}
            
            elif quote_status == "expired":
                # Quote expired
                await self._mark_quote_expired(quote, db)
                return {"status": "failed", "error": "Quote expired"}
            
            else:
                return {"status": "failed", "error": "Unknown status"}
        
        except Exception as e:
            return {"status": "failed", "error": str(e)}
        
        finally:
            await self._cleanup()
    
    
    async def _get_supplier_info(self, quote: Quote, db: AsyncSession) -> Optional[Dict]:
        """
        Get supplier details from database.
        """
        try:
            from models.supplier import Supplier
            
            # Try to get supplier by name
            query = select(Supplier).where(Supplier.name == quote.supplier_name)
            result = await db.execute(query)
            supplier = result.scalar_one_or_none()
            
            if supplier:
                return {
                    "name": supplier.name,
                    "website_url": supplier.website_url,
                    "quote_status_url": supplier.quote_status_url or supplier.website_url,
                    "requires_login": supplier.requires_login,
                    "login_url": supplier.login_url,
                    "credentials": supplier.login_credentials
                }
            else:
                # Fallback to quote's stored URL
                return {
                    "name": quote.supplier_name,
                    "website_url": quote.quote_url or "",
                    "quote_status_url": quote.quote_url or "",
                    "requires_login": False
                }
        
        except Exception as e:
            await self.log(f"  ⚠️ Error getting supplier info: {str(e)}")
            return None
    
    
    async def _navigate_to_portal(self, supplier_info: Dict, url: str) -> Dict:
        """
        Navigate to supplier portal.
        
        Returns:
            {"success": bool, "session_id": str, "error": str}
        """
        try:
            if not url:
                return {"success": False, "error": "No URL"}
            
            result = await self.tinyfish.navigate(
                url=url,
                wait_for_selector="body",
                timeout=self.timeout
            )
            
            if result.get("status") == "success":
                return {
                    "success": True,
                    "session_id": result["session_id"]
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Navigation failed")
                }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    
    async def _login_to_portal(self, supplier_info: Dict) -> Dict:
        """
        Login to supplier portal.
        
        Returns:
            {"success": bool, "error": str}
        """
        try:
            credentials = supplier_info.get("credentials", {})
            
            if not credentials:
                return {"success": False, "error": "No credentials"}
            
            # Navigate to login page if separate
            login_url = supplier_info.get("login_url")
            if login_url:
                await self.tinyfish.navigate(
                    url=login_url,
                    session_id=self.session_id
                )
                await asyncio.sleep(2)
            
            # Find and fill username
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
            
            # Find and fill password
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
            
            # Verify login
            page_html = await self.tinyfish.get_page_content(self.session_id)
            login_success = "logout" in page_html.lower() or "sign out" in page_html.lower()
            
            if login_success:
                return {"success": True}
            else:
                return {"success": False, "error": "Login verification failed"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    
    async def _navigate_to_quote_status(
        self,
        quote: Quote,
        supplier_info: Dict
    ) -> Dict:
        """
        Navigate to the page where quote status can be checked.
        
        Returns:
            {"success": bool, "error": str}
        """
        try:
            page_html = await self.tinyfish.get_page_content(self.session_id)
            
            # Look for common quote-related links
            quote_links = [
                "my quotes",
                "quote history",
                "rfq history",
                "my requests",
                "quote status",
                "pending quotes"
            ]
            
            for link_text in quote_links:
                link = await self.tinyfish.find_element(
                    self.session_id,
                    selector=f'a:contains("{link_text}")'
                )
                
                if link:
                    await self.tinyfish.click_element(
                        self.session_id,
                        link["id"]
                    )
                    await asyncio.sleep(2)
                    break
            
            # If we have a quote reference, search for it
            if quote.quote_reference:
                await self._search_for_quote_reference(quote.quote_reference)
            
            return {"success": True}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    
    async def _search_for_quote_reference(self, quote_ref: str):
        """
        Search for specific quote reference on the page.
        """
        try:
            # Look for search box
            search_box = await self.tinyfish.find_element(
                self.session_id,
                selector='input[type="search"], input[name*="search"], input[placeholder*="search"]'
            )
            
            if search_box:
                await self.tinyfish.fill_input(
                    self.session_id,
                    search_box["id"],
                    quote_ref
                )
                
                # Click search button
                search_button = await self.tinyfish.find_element(
                    self.session_id,
                    selector='button[type="submit"], button:contains("Search")'
                )
                
                if search_button:
                    await self.tinyfish.click_element(
                        self.session_id,
                        search_button["id"]
                    )
                    await asyncio.sleep(2)
        
        except Exception:
            pass
    
    
    async def _extract_quote_status(self) -> str:
        """
        Determine if quote is ready, pending, or expired.
        
        Returns:
            "ready" | "pending" | "expired" | "unknown"
        """
        try:
            page_html = await self.tinyfish.get_page_content(self.session_id)
            page_text = page_html.lower()
            
            # Check for "ready" indicators
            ready_indicators = [
                "quote sent",
                "quote ready",
                "quote available",
                "price:",
                "total:",
                "download quote",
                "view quote"
            ]
            
            ready_count = sum(1 for indicator in ready_indicators if indicator in page_text)
            
            # Check for "pending" indicators
            pending_indicators = [
                "pending",
                "in progress",
                "processing",
                "under review",
                "being prepared"
            ]
            
            has_pending = any(indicator in page_text for indicator in pending_indicators)
            
            # Check for "expired" indicators
            expired_indicators = [
                "expired",
                "no longer valid",
                "quote closed",
                "cancelled"
            ]
            
            has_expired = any(indicator in page_text for indicator in expired_indicators)
            
            if has_expired:
                return "expired"
            elif ready_count >= 2:
                return "ready"
            elif has_pending:
                return "pending"
            else:
                return "unknown"
        
        except Exception:
            return "unknown"
    
    
    async def _extract_quote_data_from_portal(self, quote: Quote) -> Optional[Dict]:
        """
        Extract quote data from supplier portal page.
        
        Returns:
            {
                "price_per_unit": float,
                "total_price": float,
                "currency": str,
                "delivery_days": int,
                "quote_reference": str
            }
        """
        try:
            page_html = await self.tinyfish.get_page_content(self.session_id)
            
            # Try to extract with regex first
            import re
            
            extracted = {
                "price_per_unit": 0,
                "total_price": 0,
                "currency": "USD",
                "delivery_days": 0,
                "quote_reference": quote.quote_reference or ""
            }
            
            # Extract price
            price_patterns = [
                r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'Price:\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'Total:\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, page_html)
                if match:
                    price_str = match.group(1).replace(',', '')
                    extracted["total_price"] = float(price_str)
                    
                    # Detect currency
                    if '$' in match.group(0):
                        extracted["currency"] = "USD"
                    elif '₹' in match.group(0):
                        extracted["currency"] = "INR"
                    
                    break
            
            # Extract delivery
            delivery_match = re.search(r'(\d+)\s*days?', page_html, re.IGNORECASE)
            if delivery_match:
                extracted["delivery_days"] = int(delivery_match.group(1))
            
            # If regex extraction succeeded
            if extracted["total_price"] > 0:
                # Calculate per unit price
                quantity = quote.quantity or 1
                extracted["price_per_unit"] = extracted["total_price"] / quantity
                
                return extracted
            
            # Fallback to LLM extraction
            await self.log("  🧠 Using AI to extract quote data...")
            
            llm_result = await extract_quote_from_html(
                html_content=page_html,
                product_spec={
                    "product_name": quote.product_name or "",
                    "quantity": quote.quantity or 0
                }
            )
            
            if llm_result:
                return llm_result
            
            return None
        
        except Exception as e:
            await self.log(f"  ⚠️ Extraction error: {str(e)}")
            return None
    
    
    async def _update_quote_in_db(
        self,
        quote: Quote,
        quote_data: Dict,
        db: AsyncSession
    ):
        """
        Update quote record in database with new data.
        """
        try:
            quote.status = "received"
            quote.price_per_unit = quote_data.get("price_per_unit", 0)
            quote.total_price = quote_data.get("total_price", 0)
            quote.currency = quote_data.get("currency", "USD")
            quote.delivery_days = quote_data.get("delivery_days", 0)
            quote.updated_at = datetime.utcnow()
            
            # Take screenshot as proof
            screenshot = await self._take_screenshot()
            if screenshot:
                quote.screenshot_url = screenshot
            
            await db.commit()
            
            await self.log(f"  ✅ Database updated")
        
        except Exception as e:
            await self.log(f"  ⚠️ Database update error: {str(e)}")
            await db.rollback()
    
    
    async def _mark_quote_expired(self, quote: Quote, db: AsyncSession):
        """
        Mark quote as expired in database.
        """
        try:
            quote.status = "expired"
            quote.is_expired = True
            quote.updated_at = datetime.utcnow()
            
            await db.commit()
            
            await self.log(f"  ⏰ Marked as expired")
        
        except Exception as e:
            await self.log(f"  ⚠️ Database update error: {str(e)}")
            await db.rollback()
    
    
    async def _take_screenshot(self) -> str:
        """
        Capture screenshot of current page.
        """
        try:
            screenshot_result = await self.tinyfish.get_screenshot(self.session_id)
            
            if screenshot_result.get("status") == "success":
                return screenshot_result.get("screenshot_url", "")
            else:
                return ""
        
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


# ─────────────────────────────────────────────────────────────────────
# Background Job Setup
# ─────────────────────────────────────────────────────────────────────

from apscheduler.schedulers.asyncio import AsyncIOScheduler 
from apscheduler.triggers.interval import IntervalTrigger 


class QuoteMonitorScheduler:
    """
    Scheduler that runs monitor agent periodically.
    """
    
    def __init__(self, db_session_factory):
        """
        Initialize scheduler.
        
        Args:
            db_session_factory: Function that returns a database session
        """
        self.db_session_factory = db_session_factory
        self.scheduler = AsyncIOScheduler()
        self.monitor = MonitorAgent()
    
    
    async def check_job(self):
        """
        Job that runs on schedule.
        """
        async with self.db_session_factory() as db:
            try:
                await self.monitor.check_pending_quotes(db)
            except Exception as e:
                print(f"❌ Monitor job error: {str(e)}")
    
    
    def start(self, interval_hours: int = 4):
        """
        Start the background scheduler.
        
        Args:
            interval_hours: How often to check (default: 4 hours)
        """
        self.scheduler.add_job(
            self.check_job,
            trigger=IntervalTrigger(hours=interval_hours),
            id="quote_monitor",
            name="Check Pending Quotes",
            replace_existing=True
        )
        
        self.scheduler.start()
        print(f"⏰ Quote monitor started - checking every {interval_hours} hours")
    
    
    def stop(self):
        """
        Stop the scheduler.
        """
        self.scheduler.shutdown()
        print("⏰ Quote monitor stopped")


# ─────────────────────────────────────────────────────────────────────
# Standalone function for manual checks
# ─────────────────────────────────────────────────────────────────────

async def check_pending_quotes_now(db: AsyncSession) -> Dict:
    """
    Manually trigger a pending quote check.
    
    Usage:
        from agents.monitor_agent import check_pending_quotes_now
        
        result = await check_pending_quotes_now(db)
        print(f"Checked {result['checked']} quotes")
    
    Args:
        db: Database session
    
    Returns:
        {
            "checked": int,
            "updated": int,
            "still_pending": int,
            "failed": int
        }
    """
    monitor = MonitorAgent()
    return await monitor.check_pending_quotes(db)