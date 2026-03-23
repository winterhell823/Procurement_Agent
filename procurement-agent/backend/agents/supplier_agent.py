"""
supplier_agent.py
────────────────────────────────────────────────────────────────────
Main worker agent that navigates to ONE supplier website and retrieves
a quote for the requested product.

Called by orchestrator.py for each supplier in parallel.
"""

import asyncio
import re
import json
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta
import uuid

from agents.form_agent import handle_complex_form
from services.tinyfish_client import TinyFishClient
from services.llm_service import extract_quote_from_html, parse_price_text


async def run_supplier_agent(
    supplier: Dict,
    product_spec: Dict,
    company_profile: Dict,
    on_status: Optional[Callable] = None
) -> Dict:
    """
    Main entry point - get a quote from ONE supplier.
    
    Args:
        supplier: {
            "name": str,
            "website_url": str,
            "quote_form_url": str,
            "requires_login": bool,
            "login_url": str (optional),
            "credentials": dict (optional)
        }
        product_spec: {
            "product_name": str,
            "category": str,
            "quantity": int,
            "unit": str,
            "material": str (optional),
            "size": str (optional),
            "specifications": dict (optional)
        }
        company_profile: {
            "company_name": str,
            "contact_person": str,
            "email": str,
            "phone": str,
            "address": str,
            "gst_number": str (optional),
            "payment_terms": str (optional)
        }
        on_status: Function to call for logging status updates
    
    Returns:
        {
            "status": "received" | "failed",
            "supplier_name": str,
            "supplier_url": str,
            "price_per_unit": float,
            "total_price": float,
            "currency": str,
            "delivery_days": int,
            "quote_reference": str,
            "quote_url": str,
            "screenshot_url": str,
            "raw_data": dict,
            "error": str (if failed)
        }
    """
    
    agent = SupplierAgent(on_status)
    return await agent.get_quote(supplier, product_spec, company_profile)


class SupplierAgent:
    """
    Worker agent that handles quote retrieval from a single supplier.
    """
    
    def __init__(self, logger: Optional[Callable] = None):
        """
        Initialize the supplier agent.
        
        Args:
            logger: Optional function for status logging
        """
        self.log = logger or (lambda msg: print(msg))
        self.tinyfish = None
        self.session_id = None
        self.timeout = 60  # seconds
    
    
    async def get_quote(
        self,
        supplier: Dict,
        product_spec: Dict,
        company_profile: Dict
    ) -> Dict:
        """
        Main workflow to retrieve a quote from supplier.
        """
        supplier_name = supplier.get("name", "Unknown")
        
        try:
            await self.log(f"🌐 Starting quote request from {supplier_name}...")
            
            # STEP 1: Initialize TinyFish client
            self.tinyfish = TinyFishClient()
            
            # STEP 2: Navigate to quote form
            navigation_result = await self._navigate_to_quote_form(supplier)
            if not navigation_result["success"]:
                raise Exception(f"Navigation failed: {navigation_result['error']}")
            
            self.session_id = navigation_result["session_id"]
            
            # STEP 3: Handle login if required
            if supplier.get("requires_login", False):
                login_result = await self._handle_login(supplier)
                if not login_result["success"]:
                    await self.log(f"⚠️ Login failed, trying without login...")
            
            # STEP 4: Detect form complexity
            await self.log(f"📝 Analyzing quote form...")
            form_complexity = await self._detect_form_complexity()
            
            # STEP 5: Fill the form
            if form_complexity["is_complex"]:
                await self.log(f"📋 Complex form detected - using form agent...")
                fill_result = await self._fill_complex_form(
                    product_spec, 
                    company_profile
                )
            else:
                await self.log(f"✍️ Filling simple quote form...")
                fill_result = await self._fill_simple_form(
                    product_spec, 
                    company_profile
                )
            
            if not fill_result["success"]:
                raise Exception(f"Form filling failed: {fill_result.get('error')}")
            
            # STEP 6: Submit form
            await self.log(f"🚀 Submitting quote request...")
            submit_result = await self._submit_form()
            
            if not submit_result["success"]:
                raise Exception(f"Form submission failed: {submit_result.get('error')}")
            
            # STEP 7: Wait for response
            await self.log(f"⏳ Waiting for quote response...")
            await asyncio.sleep(5)  # Wait for page to load
            
            # STEP 8: Check if quote is immediate or pending
            quote_status = await self._check_quote_status()
            
            if quote_status == "immediate":
                # Quote is on the page - extract it
                await self.log(f"💰 Extracting quote data...")
                quote_data = await self._extract_quote_data(product_spec)
                
                if not quote_data:
                    raise Exception("Could not extract quote from page")
                
                # STEP 9: Take screenshot
                screenshot = await self._take_screenshot()
                
                # STEP 10: Build successful response
                result = {
                    "status": "received",
                    "supplier_name": supplier_name,
                    "supplier_url": supplier.get("website_url", ""),
                    "price_per_unit": quote_data["price_per_unit"],
                    "total_price": quote_data["total_price"],
                    "currency": quote_data.get("currency", "USD"),
                    "delivery_days": quote_data.get("delivery_days", 0),
                    "quote_reference": quote_data.get("quote_reference", ""),
                    "quote_url": await self._get_current_url(),
                    "screenshot_url": screenshot,
                    "raw_data": quote_data.get("raw_data", {}),
                    "extracted_at": datetime.utcnow().isoformat()
                }
                
                await self.log(
                    f"✅ Quote received: {result['currency']} {result['price_per_unit']}/unit, "
                    f"{result['delivery_days']} days delivery"
                )
                
                return result
            
            elif quote_status == "pending":
                # Quote will be sent later
                await self.log(f"📧 Quote pending - will be sent via email")
                
                screenshot = await self._take_screenshot()
                
                return {
                    "status": "pending",
                    "supplier_name": supplier_name,
                    "supplier_url": supplier.get("website_url", ""),
                    "quote_url": await self._get_current_url(),
                    "screenshot_url": screenshot,
                    "message": "Quote request submitted - awaiting email response",
                    "extracted_at": datetime.utcnow().isoformat()
                }
            
            else:
                raise Exception("Could not determine quote status")
        
        except Exception as e:
            await self.log(f"❌ Failed to get quote from {supplier_name}: {str(e)}")
            
            # Take screenshot of error if possible
            screenshot = None
            try:
                screenshot = await self._take_screenshot()
            except:
                pass
            
            return {
                "status": "failed",
                "supplier_name": supplier_name,
                "supplier_url": supplier.get("website_url", ""),
                "error": str(e),
                "screenshot_url": screenshot,
                "extracted_at": datetime.utcnow().isoformat()
            }
        
        finally:
            # Cleanup
            await self._cleanup()
    
    
    async def _navigate_to_quote_form(self, supplier: Dict) -> Dict:
        """
        Navigate to the supplier's quote request form.
        
        Returns:
            {"success": bool, "session_id": str, "error": str}
        """
        try:
            quote_url = supplier.get("quote_form_url") or supplier.get("website_url")
            
            if not quote_url:
                return {"success": False, "error": "No URL provided"}
            
            # Start TinyFish session
            result = await self.tinyfish.navigate(
                url=quote_url,
                wait_for_selector="form, input[type='text'], textarea",
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
    
    
    async def _handle_login(self, supplier: Dict) -> Dict:
        """
        Handle supplier portal login if required.
        
        Returns:
            {"success": bool, "error": str}
        """
        try:
            credentials = supplier.get("credentials", {})
            
            if not credentials:
                return {"success": False, "error": "No credentials provided"}
            
            await self.log(f"🔐 Logging into {supplier['name']} portal...")
            
            # Find login form
            login_url = supplier.get("login_url")
            if login_url and login_url != await self._get_current_url():
                # Navigate to login page
                await self.tinyfish.navigate(
                    url=login_url,
                    session_id=self.session_id
                )
                await asyncio.sleep(2)
            
            # Find username/email field
            username_field = await self.tinyfish.find_element(
                self.session_id,
                selector='input[type="email"], input[name*="email"], input[name*="username"], input[id*="email"]'
            )
            
            if username_field:
                await self.tinyfish.fill_input(
                    self.session_id,
                    username_field["id"],
                    credentials.get("username") or credentials.get("email")
                )
            
            # Find password field
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
            
            # Click login button
            login_button = await self.tinyfish.find_element(
                self.session_id,
                selector='button[type="submit"], input[type="submit"], button:contains("Login"), button:contains("Sign In")'
            )
            
            if login_button:
                await self.tinyfish.click_element(
                    self.session_id,
                    login_button["id"]
                )
                await asyncio.sleep(3)  # Wait for login
            
            # Verify login success (look for user profile or dashboard)
            page_html = await self.tinyfish.get_page_content(self.session_id)
            
            login_success = any([
                "logout" in page_html.lower(),
                "sign out" in page_html.lower(),
                "dashboard" in page_html.lower(),
                "my account" in page_html.lower()
            ])
            
            if login_success:
                await self.log(f"✅ Successfully logged in")
                return {"success": True}
            else:
                return {"success": False, "error": "Login verification failed"}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    
    async def _detect_form_complexity(self) -> Dict:
        """
        Analyze form to determine if it's simple or complex.
        
        Returns:
            {"is_complex": bool, "total_steps": int}
        """
        try:
            page_html = await self.tinyfish.get_page_content(self.session_id)
            
            # Check for multi-step indicators
            has_steps = bool(re.search(
                r'step\s+\d+\s+of\s+\d+|page\s+\d+\s+of\s+\d+',
                page_html,
                re.IGNORECASE
            ))
            
            # Check for Next/Continue buttons
            has_next = bool(re.search(
                r'<button[^>]*(next|continue)[^>]*>',
                page_html,
                re.IGNORECASE
            ))
            
            # Check for file uploads
            has_file_upload = '<input type="file"' in page_html.lower()
            
            # Check for conditional/dynamic fields
            has_dynamic = 'data-conditional' in page_html or 'data-show-if' in page_html
            
            is_complex = has_steps or has_next or has_file_upload or has_dynamic
            
            # Try to count steps
            step_match = re.search(r'of\s+(\d+)', page_html, re.IGNORECASE)
            total_steps = int(step_match.group(1)) if step_match else (2 if is_complex else 1)
            
            return {
                "is_complex": is_complex,
                "total_steps": total_steps
            }
        
        except Exception:
            return {"is_complex": False, "total_steps": 1}
    
    
    async def _fill_simple_form(
        self,
        product_spec: Dict,
        company_profile: Dict
    ) -> Dict:
        """
        Fill a simple single-page form directly.
        
        Returns:
            {"success": bool, "error": str}
        """
        try:
            # Get all form fields
            fields = await self.tinyfish.extract_form_fields(self.session_id)
            
            # Build mapping
            field_mappings = self._build_field_mappings(product_spec, company_profile)
            
            filled_count = 0
            
            for field in fields:
                field_name = field.get("name", "").lower()
                field_id = field.get("id", "")
                field_type = field.get("type", "text")
                
                # Find matching data
                value = self._match_field_value(field_name, field_id, field_mappings)
                
                if value is not None:
                    try:
                        await self.tinyfish.fill_input(
                            self.session_id,
                            field_id,
                            str(value)
                        )
                        filled_count += 1
                    except Exception as e:
                        await self.log(f"  ⚠️ Could not fill {field_name}: {str(e)}")
            
            await self.log(f"  ✓ Filled {filled_count} fields")
            
            return {"success": True, "fields_filled": filled_count}
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    
    async def _fill_complex_form(
        self,
        product_spec: Dict,
        company_profile: Dict
    ) -> Dict:
        """
        Use FormAgent to handle complex multi-step form.
        
        Returns:
            {"success": bool, "error": str}
        """
        try:
            field_mappings = self._build_field_mappings(product_spec, company_profile)
            
            result = await handle_complex_form(
                tinyfish_client=self.tinyfish,
                session_id=self.session_id,
                field_data=field_mappings,
                logger=self.log
            )
            
            return {
                "success": result["status"] == "success",
                "error": result.get("message") if result["status"] != "success" else None
            }
        
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    
    def _build_field_mappings(
        self,
        product_spec: Dict,
        company_profile: Dict
    ) -> Dict:
        """
        Build comprehensive field mappings from product_spec and company_profile.
        """
        return {
            # Product fields
            "product_name": product_spec.get("product_name", ""),
            "product": product_spec.get("product_name", ""),
            "item_name": product_spec.get("product_name", ""),
            "description": product_spec.get("product_name", ""),
            "material": product_spec.get("material", ""),
            "size": product_spec.get("size", ""),
            "category": product_spec.get("category", ""),
            
            # Quantity
            "quantity": product_spec.get("quantity", 0),
            "qty": product_spec.get("quantity", 0),
            "amount": product_spec.get("quantity", 0),
            "unit": product_spec.get("unit", "units"),
            
            # Company
            "company_name": company_profile.get("company_name", ""),
            "company": company_profile.get("company_name", ""),
            "organization": company_profile.get("company_name", ""),
            
            # Contact
            "contact_person": company_profile.get("contact_person", ""),
            "name": company_profile.get("contact_person", ""),
            "contact_name": company_profile.get("contact_person", ""),
            "email": company_profile.get("email", ""),
            "phone": company_profile.get("phone", ""),
            "mobile": company_profile.get("phone", ""),
            
            # Address
            "address": company_profile.get("address", ""),
            "delivery_address": company_profile.get("address", ""),
            "company_address": company_profile.get("address", ""),
            
            # Other
            "gst_number": company_profile.get("gst_number", ""),
            "gst": company_profile.get("gst_number", ""),
            "payment_terms": company_profile.get("payment_terms", "Net 30"),
            "notes": f"Quote request for {product_spec.get('quantity', '')} {product_spec.get('unit', 'units')} of {product_spec.get('product_name', '')}",
            "comments": "",
            "special_instructions": ""
        }
    
    
    def _match_field_value(
        self,
        field_name: str,
        field_id: str,
        field_mappings: Dict
    ) -> Optional[any]:
        """
        Match a form field to our data.
        """
        # Direct match
        if field_name in field_mappings:
            return field_mappings[field_name]
        
        if field_id.lower() in field_mappings:
            return field_mappings[field_id.lower()]
        
        # Partial match
        for key, value in field_mappings.items():
            if key in field_name or key in field_id.lower():
                return value
        
        return None
    
    
    async def _submit_form(self) -> Dict:
        """
        Find and click the submit button.
        
        Returns:
            {"success": bool, "error": str}
        """
        try:
            # Find submit button
            submit_button = await self.tinyfish.find_element(
                self.session_id,
                selector='button[type="submit"], input[type="submit"], button:contains("Submit"), button:contains("Send"), button:contains("Get Quote"), button:contains("Request Quote")'
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
    
    
    async def _check_quote_status(self) -> str:
        """
        Check if quote is displayed immediately or pending.
        
        Returns:
            "immediate" | "pending" | "error"
        """
        try:
            page_html = await self.tinyfish.get_page_content(self.session_id)
            page_text = page_html.lower()
            
            # Check for immediate quote indicators
            immediate_indicators = [
                "price",
                "quote",
                "total",
                "$",
                "₹",
                "delivery",
                "lead time"
            ]
            
            immediate_count = sum(1 for indicator in immediate_indicators if indicator in page_text)
            
            # Check for pending indicators
            pending_indicators = [
                "will contact you",
                "email you",
                "get back to you",
                "within 24 hours",
                "review your request",
                "thank you for your request",
                "we'll send you"
            ]
            
            has_pending = any(indicator in page_text for indicator in pending_indicators)
            
            if has_pending:
                return "pending"
            elif immediate_count >= 2:
                return "immediate"
            else:
                return "error"
        
        except Exception:
            return "error"
    
    
    async def _extract_quote_data(self, product_spec: Dict) -> Optional[Dict]:
        """
        Extract quote information from the response page.
        
        Returns:
            {
                "price_per_unit": float,
                "total_price": float,
                "currency": str,
                "delivery_days": int,
                "quote_reference": str,
                "raw_data": dict
            }
        """
        try:
            page_html = await self.tinyfish.get_page_content(self.session_id)
            
            # Try regex extraction first
            quote_data = self._extract_with_regex(page_html, product_spec)
            
            if quote_data and quote_data.get("price_per_unit"):
                return quote_data
            
            # Fallback to LLM extraction
            await self.log("  🧠 Using AI to parse quote...")
            llm_quote = await extract_quote_from_html(
                html_content=page_html,
                product_spec=product_spec
            )
            
            if llm_quote:
                return llm_quote
            
            return None
        
        except Exception as e:
            await self.log(f"  ⚠️ Quote extraction error: {str(e)}")
            return None
    
    
    def _extract_with_regex(self, html: str, product_spec: Dict) -> Dict:
        """
        Try to extract quote data using regex patterns.
        """
        result = {
            "price_per_unit": 0,
            "total_price": 0,
            "currency": "USD",
            "delivery_days": 0,
            "quote_reference": "",
            "raw_data": {}
        }
        
        try:
            # Extract price
            price_patterns = [
                r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $1,234.56
                r'₹\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',   # ₹1,234.56
                r'Price:\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'Total:\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
                r'Unit\s*Price:\s*\$?\s*(\d+(?:,\d{3})*(?:\.\d{2})?)'
            ]
            
            for pattern in price_patterns:
                match = re.search(pattern, html)
                if match:
                    price_str = match.group(1).replace(',', '')
                    result["total_price"] = float(price_str)
                    
                    # Calculate per unit
                    quantity = product_spec.get("quantity", 1)
                    if quantity > 0:
                        result["price_per_unit"] = result["total_price"] / quantity
                    
                    # Detect currency
                    if '$' in match.group(0):
                        result["currency"] = "USD"
                    elif '₹' in match.group(0):
                        result["currency"] = "INR"
                    
                    break
            
            # Extract delivery time
            delivery_patterns = [
                r'(\d+)\s*days?',
                r'(\d+)\s*-\s*(\d+)\s*days?',
                r'delivery:\s*(\d+)',
                r'lead\s*time:\s*(\d+)',
                r'ships?\s*in\s*(\d+)'
            ]
            
            for pattern in delivery_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    result["delivery_days"] = int(match.group(1))
                    break
            
            # Extract quote reference
            ref_patterns = [
                r'Quote\s*#?\s*([A-Z0-9-]+)',
                r'Reference\s*#?\s*([A-Z0-9-]+)',
                r'RFQ\s*#?\s*([A-Z0-9-]+)',
                r'Quotation\s*#?\s*([A-Z0-9-]+)'
            ]
            
            for pattern in ref_patterns:
                match = re.search(pattern, html, re.IGNORECASE)
                if match:
                    result["quote_reference"] = match.group(1)
                    break
            
            return result
        
        except Exception:
            return result
    
    
    async def _take_screenshot(self) -> str:
        """
        Capture screenshot of current page.
        
        Returns:
            URL/path to screenshot
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
        """Get current page URL."""
        try:
            result = await self.tinyfish.get_current_url(self.session_id)
            return result.get("url", "")
        except Exception:
            return ""
    
    
    async def _cleanup(self):
        """Clean up TinyFish session."""
        try:
            if self.tinyfish and self.session_id:
                await self.tinyfish.close_session(self.session_id)
        except Exception:
            pass