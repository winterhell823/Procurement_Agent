"""
form_agent.py
────────────────────────────────────────────────────────────────────
Helper agent for handling complex multi-step forms.
Called by supplier_agent.py when encountering difficult form flows.
"""

import asyncio
import re
from typing import Dict, List, Optional, Callable
from datetime import datetime


class FormAgent:
    """
    Specialized agent for handling complex multi-step forms.
    
    Capabilities:
    - Detects form structure (single vs multi-step)
    - Navigates through wizard-style forms
    - Handles various input types (text, dropdown, radio, checkbox, date, file)
    - Manages conditional fields
    """
    
    def __init__(self, tinyfish_client, logger: Optional[Callable] = None):
        """
        Initialize FormAgent
        
        Args:
            tinyfish_client: TinyFish API client instance
            logger: Optional logging function for status updates
        """
        self.tinyfish = tinyfish_client
        self.log = logger or (lambda msg: print(msg))
    
    
    async def fill_complex_form(
        self,
        session_id: str,
        field_mappings: Dict[str, any],
        max_steps: int = 10
    ) -> Dict[str, any]:
        """
        Main entry point - handles entire multi-step form flow.
        
        Args:
            session_id: Active TinyFish browser session
            field_mappings: Data to fill (e.g., {"product_name": "gloves", "quantity": 500})
            max_steps: Maximum number of steps to prevent infinite loops
        
        Returns:
            {
                "status": "success" | "failed",
                "steps_completed": int,
                "message": str
            }
        """
        try:
            await self.log("📋 Starting multi-step form handler...")
            
            # STEP 1: Detect form structure
            form_info = await self._detect_form_structure(session_id)
            total_steps = form_info.get("total_steps", 1)
            
            if total_steps == 1:
                await self.log("✅ Simple form detected - filling directly")
                return await self._fill_single_page(session_id, field_mappings)
            
            await self.log(f"📊 Detected {total_steps}-step form")
            
            # STEP 2: Navigate through each step
            current_step = 1
            while current_step <= min(total_steps, max_steps):
                await self.log(f"📝 Processing step {current_step} of {total_steps}...")
                
                # Fill fields on current page
                filled = await self._fill_current_page(
                    session_id, 
                    field_mappings, 
                    current_step
                )
                
                if not filled:
                    await self.log(f"⚠️ No fields filled on step {current_step}")
                
                # Check if this is the last step
                is_last_step = await self._is_final_step(session_id, current_step, total_steps)
                
                if is_last_step:
                    # Submit the form
                    await self.log("🚀 Final step - submitting form...")
                    submit_result = await self._submit_form(session_id)
                    
                    if submit_result["success"]:
                        await self.log("✅ Form submitted successfully!")
                        return {
                            "status": "success",
                            "steps_completed": current_step,
                            "message": "Multi-step form completed"
                        }
                    else:
                        return {
                            "status": "failed",
                            "steps_completed": current_step,
                            "message": f"Submit failed: {submit_result.get('error')}"
                        }
                else:
                    # Click "Next" to go to next step
                    next_result = await self._click_next_button(session_id)
                    
                    if not next_result["success"]:
                        return {
                            "status": "failed",
                            "steps_completed": current_step,
                            "message": f"Navigation failed: {next_result.get('error')}"
                        }
                    
                    await self.log(f"➡️ Moved to step {current_step + 1}")
                    await asyncio.sleep(2)  # Wait for page transition
                    current_step += 1
            
            # If we hit max_steps
            return {
                "status": "failed",
                "steps_completed": current_step - 1,
                "message": f"Exceeded max steps ({max_steps})"
            }
            
        except Exception as e:
            await self.log(f"❌ Form agent error: {str(e)}")
            return {
                "status": "failed",
                "steps_completed": 0,
                "message": str(e)
            }
    
    
    async def _detect_form_structure(self, session_id: str) -> Dict:
        """
        Analyze the form to determine its structure.
        
        Returns:
            {
                "total_steps": int,
                "is_wizard": bool,
                "has_file_upload": bool
            }
        """
        try:
            # Get page HTML
            page_html = await self.tinyfish.get_page_content(session_id)
            
            # Look for step indicators
            step_patterns = [
                r'Step\s+(\d+)\s+of\s+(\d+)',
                r'(\d+)\s*/\s*(\d+)',
                r'Page\s+(\d+)\s+of\s+(\d+)',
                r'data-step=["\'](\d+)["\'].*data-total=["\'](\d+)["\']'
            ]
            
            total_steps = 1
            for pattern in step_patterns:
                match = re.search(pattern, page_html, re.IGNORECASE)
                if match:
                    total_steps = int(match.group(2))
                    break
            
            # Check for Next/Continue buttons (indicates multi-step)
            has_next = bool(re.search(
                r'<button[^>]*(next|continue|proceed)[^>]*>',
                page_html,
                re.IGNORECASE
            ))
            
            if has_next and total_steps == 1:
                total_steps = 2  # At least 2 steps if Next button exists
            
            # Check for file uploads
            has_file_upload = '<input type="file"' in page_html.lower()
            
            return {
                "total_steps": total_steps,
                "is_wizard": total_steps > 1,
                "has_file_upload": has_file_upload
            }
            
        except Exception as e:
            await self.log(f"⚠️ Form detection error: {str(e)}")
            return {"total_steps": 1, "is_wizard": False, "has_file_upload": False}
    
    
    async def _fill_single_page(
        self, 
        session_id: str, 
        field_mappings: Dict[str, any]
    ) -> Dict:
        """
        Fill a simple single-page form.
        """
        try:
            filled_count = await self._fill_current_page(session_id, field_mappings, 1)
            submit_result = await self._submit_form(session_id)
            
            if submit_result["success"]:
                return {
                    "status": "success",
                    "steps_completed": 1,
                    "message": f"Filled {filled_count} fields and submitted"
                }
            else:
                return {
                    "status": "failed",
                    "steps_completed": 1,
                    "message": submit_result.get("error", "Submit failed")
                }
        except Exception as e:
            return {
                "status": "failed",
                "steps_completed": 0,
                "message": str(e)
            }
    
    
    async def _fill_current_page(
        self, 
        session_id: str, 
        field_mappings: Dict[str, any],
        step_number: int
    ) -> int:
        """
        Fill all visible fields on the current page.
        
        Returns:
            Number of fields successfully filled
        """
        filled_count = 0
        
        try:
            # Get all input fields on current page
            fields = await self._identify_visible_fields(session_id)
            
            for field in fields:
                field_name = field.get("name", "").lower()
                field_type = field.get("type", "text").lower()
                field_id = field.get("id", "")
                field_label = field.get("label", "").lower()
                
                # Match field to our data
                value = self._match_field_to_data(
                    field_name, 
                    field_label, 
                    field_mappings
                )
                
                if value is not None:
                    success = await self._fill_field(
                        session_id,
                        field,
                        value,
                        field_type
                    )
                    
                    if success:
                        filled_count += 1
                        await self.log(f"  ✓ Filled: {field_name or field_id} = {value}")
            
            # Handle conditional fields (fields that appear after filling others)
            await asyncio.sleep(1)  # Wait for any dynamic fields
            new_fields = await self._identify_visible_fields(session_id)
            
            if len(new_fields) > len(fields):
                await self.log("  🔄 New fields appeared - filling them...")
                additional_filled = await self._fill_current_page(
                    session_id, 
                    field_mappings, 
                    step_number
                )
                filled_count += additional_filled
            
            return filled_count
            
        except Exception as e:
            await self.log(f"⚠️ Error filling page: {str(e)}")
            return filled_count
    
    
    async def _identify_visible_fields(self, session_id: str) -> List[Dict]:
        """
        Get all visible input fields on current page.
        
        Returns:
            List of field dictionaries with name, type, id, label
        """
        try:
            # Use TinyFish to extract form fields
            fields_data = await self.tinyfish.extract_form_fields(session_id)
            
            # Filter out hidden fields
            visible_fields = [
                field for field in fields_data 
                if field.get("visible", True) and field.get("type") != "hidden"
            ]
            
            return visible_fields
            
        except Exception as e:
            await self.log(f"⚠️ Field identification error: {str(e)}")
            return []
    
    
    def _match_field_to_data(
        self, 
        field_name: str, 
        field_label: str, 
        field_mappings: Dict[str, any]
    ) -> Optional[any]:
        """
        Match a form field to our data based on name/label.
        
        Args:
            field_name: Field's name attribute
            field_label: Field's label text
            field_mappings: Our data to fill
        
        Returns:
            Value to fill, or None if no match
        """
        # Common field name mappings
        field_map = {
            # Product fields
            "product": ["product_name", "item_name", "product_description"],
            "item": ["product_name", "item_name"],
            "description": ["product_name", "product_description"],
            "material": ["material", "product_material"],
            
            # Quantity fields
            "quantity": ["quantity", "qty", "amount"],
            "qty": ["quantity", "qty"],
            "units": ["quantity"],
            
            # Size/dimensions
            "size": ["size", "product_size"],
            "dimension": ["dimensions", "size"],
            
            # Company fields
            "company": ["company_name", "business_name"],
            "organization": ["company_name"],
            
            # Contact fields
            "name": ["contact_person", "full_name"],
            "contact": ["contact_person"],
            "email": ["email", "contact_email"],
            "phone": ["phone", "contact_phone"],
            "mobile": ["phone"],
            
            # Address fields
            "address": ["address", "company_address"],
            "street": ["address"],
            "city": ["city"],
            "state": ["state"],
            "zip": ["zip_code", "postal_code"],
            "pincode": ["zip_code", "postal_code"],
            
            # Other
            "gst": ["gst_number"],
            "payment": ["payment_terms"],
            "delivery": ["delivery_address"],
            "notes": ["notes", "comments", "special_instructions"]
        }
        
        # Try to match field name
        for key, mappings in field_map.items():
            if key in field_name or key in field_label:
                for mapping in mappings:
                    if mapping in field_mappings:
                        return field_mappings[mapping]
        
        # Direct match
        if field_name in field_mappings:
            return field_mappings[field_name]
        
        # Check label match
        for key, value in field_mappings.items():
            if key.lower() in field_label or key.lower() in field_name:
                return value
        
        return None
    
    
    async def _fill_field(
        self,
        session_id: str,
        field: Dict,
        value: any,
        field_type: str
    ) -> bool:
        """
        Fill a single field based on its type.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            field_id = field.get("id") or field.get("name")
            
            if field_type in ["text", "email", "tel", "number"]:
                # Text input
                await self.tinyfish.fill_input(session_id, field_id, str(value))
                return True
            
            elif field_type == "textarea":
                # Text area
                await self.tinyfish.fill_textarea(session_id, field_id, str(value))
                return True
            
            elif field_type == "select" or field_type == "dropdown":
                # Dropdown
                await self.tinyfish.select_option(session_id, field_id, str(value))
                return True
            
            elif field_type == "radio":
                # Radio button
                await self.tinyfish.click_radio(session_id, field_id, str(value))
                return True
            
            elif field_type == "checkbox":
                # Checkbox
                should_check = bool(value)
                await self.tinyfish.set_checkbox(session_id, field_id, should_check)
                return True
            
            elif field_type == "date":
                # Date picker
                date_str = value if isinstance(value, str) else str(value)
                await self.tinyfish.fill_date(session_id, field_id, date_str)
                return True
            
            elif field_type == "file":
                # File upload - skip for now (would need file path)
                await self.log(f"  ⊘ Skipping file upload: {field_id}")
                return False
            
            else:
                # Unknown type - try text input
                await self.tinyfish.fill_input(session_id, field_id, str(value))
                return True
                
        except Exception as e:
            await self.log(f"  ⚠️ Failed to fill {field.get('name', 'field')}: {str(e)}")
            return False
    
    
    async def _is_final_step(
        self, 
        session_id: str, 
        current_step: int, 
        total_steps: int
    ) -> bool:
        """
        Determine if we're on the final step of the form.
        
        Returns:
            True if this is the last step
        """
        try:
            page_html = await self.tinyfish.get_page_content(session_id)
            
            # Check step number
            if current_step >= total_steps:
                return True
            
            # Look for Submit button (indicates final step)
            submit_patterns = [
                r'<button[^>]*(submit|send|get\s*quote|request\s*quote)[^>]*>',
                r'type=["\']submit["\']',
                r'<input[^>]*type=["\']submit["\']'
            ]
            
            for pattern in submit_patterns:
                if re.search(pattern, page_html, re.IGNORECASE):
                    return True
            
            # Check for absence of Next button
            has_next = bool(re.search(
                r'<button[^>]*(next|continue|proceed)[^>]*>',
                page_html,
                re.IGNORECASE
            ))
            
            return not has_next
            
        except Exception:
            return current_step >= total_steps
    
    
    async def _click_next_button(self, session_id: str) -> Dict:
        """
        Find and click the "Next" or "Continue" button.
        
        Returns:
            {"success": bool, "error": str}
        """
        try:
            # Find Next button
            next_button = await self.tinyfish.find_element(
                session_id,
                selector='button:contains("Next"), button:contains("Continue"), button:contains("Proceed")'
            )
            
            if not next_button:
                # Try finding by type or class
                next_button = await self.tinyfish.find_element(
                    session_id,
                    selector='button.next, button.continue, input[value="Next"]'
                )
            
            if next_button:
                await self.tinyfish.click_element(session_id, next_button["id"])
                return {"success": True}
            else:
                return {"success": False, "error": "Next button not found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    
    async def _submit_form(self, session_id: str) -> Dict:
        """
        Find and click the final Submit button.
        
        Returns:
            {"success": bool, "error": str}
        """
        try:
            # Find Submit button
            submit_patterns = [
                'button:contains("Submit")',
                'button:contains("Send")',
                'button:contains("Get Quote")',
                'button:contains("Request Quote")',
                'button[type="submit"]',
                'input[type="submit"]',
                'button.submit'
            ]
            
            submit_button = None
            for pattern in submit_patterns:
                submit_button = await self.tinyfish.find_element(
                    session_id,
                    selector=pattern
                )
                if submit_button:
                    break
            
            if submit_button:
                await self.tinyfish.click_element(session_id, submit_button["id"])
                await asyncio.sleep(3)  # Wait for submission
                return {"success": True}
            else:
                return {"success": False, "error": "Submit button not found"}
                
        except Exception as e:
            return {"success": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────────────
# Helper function for easy usage
# ─────────────────────────────────────────────────────────────────────

async def handle_complex_form(
    tinyfish_client,
    session_id: str,
    field_data: Dict[str, any],
    logger: Optional[Callable] = None
) -> Dict:
    """
    Convenience function to handle complex forms.
    
    Usage:
        result = await handle_complex_form(
            tinyfish_client=tinyfish,
            session_id="abc123",
            field_data={
                "product_name": "Industrial Gloves",
                "quantity": 500,
                "company_name": "Acme Corp",
                "email": "buyer@acme.com"
            },
            logger=log_function
        )
    
    Returns:
        {
            "status": "success" | "failed",
            "steps_completed": int,
            "message": str
        }
    """
    agent = FormAgent(tinyfish_client, logger)
    return await agent.fill_complex_form(session_id, field_data)