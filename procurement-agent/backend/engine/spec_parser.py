"""
engine/spec_parser.py
────────────────────────────────────────────────────────────────────
Parses natural language product descriptions into structured data.

Takes messy user input like "500 industrial gloves size L nitrile"
and converts it to structured JSON:
{
    "product_name": "Industrial Gloves",
    "quantity": 500,
    "size": "L",
    "material": "nitrile",
    "category": "safety_equipment"
}
"""

import re
from typing import Dict, Optional, List
import json


async def parse_spec(raw_description: str) -> Dict:
    """
    Main entry point - parse product description.
    
    Args:
        raw_description: User's free-text product description
    
    Returns:
        {
            "product_name": str,
            "category": str,
            "quantity": int,
            "unit": str,
            "material": str (optional),
            "size": str (optional),
            "color": str (optional),
            "specifications": dict (other details),
            "original_description": str
        }
    """
    
    parser = SpecParser()
    return await parser.parse(raw_description)


class SpecParser:
    """
    Parser that extracts structured data from product descriptions.
    """
    
    def __init__(self):
        """
        Initialize parser with category mappings and patterns.
        """
        # Product categories
        self.categories = {
            "safety_equipment": [
                "gloves", "helmet", "goggles", "safety shoes", "hard hat",
                "safety vest", "ear protection", "respirator", "face shield"
            ],
            "office_supplies": [
                "paper", "pen", "pencil", "folder", "binder", "stapler",
                "notebook", "envelope", "printer paper", "toner"
            ],
            "electronics": [
                "laptop", "computer", "monitor", "keyboard", "mouse",
                "cable", "charger", "phone", "tablet", "headphones"
            ],
            "furniture": [
                "desk", "chair", "table", "cabinet", "shelf", "sofa",
                "filing cabinet", "bookshelf", "office chair"
            ],
            "industrial_materials": [
                "steel", "aluminum", "plastic", "wood", "metal",
                "pipe", "sheet", "rod", "bar", "wire"
            ],
            "tools": [
                "hammer", "screwdriver", "drill", "saw", "wrench",
                "pliers", "tape measure", "level", "tool kit"
            ],
            "packaging": [
                "box", "carton", "bubble wrap", "tape", "pallet",
                "shrink wrap", "stretch film", "label", "packaging"
            ],
            "cleaning_supplies": [
                "detergent", "soap", "cleaner", "mop", "broom",
                "vacuum", "disinfectant", "wipes", "sanitizer"
            ]
        }
        
        # Common units
        self.units = [
            "units", "pieces", "pcs", "items",
            "boxes", "cartons", "pallets",
            "kg", "kilograms", "grams", "g",
            "liters", "l", "ml", "milliliters",
            "meters", "m", "cm", "feet", "inches"
        ]
    
    
    async def parse(self, raw_description: str) -> Dict:
        """
        Parse the raw description into structured data.
        """
        if not raw_description or not raw_description.strip():
            raise ValueError("Product description cannot be empty")
        
        # Clean the input
        cleaned = self._clean_description(raw_description)
        
        # Step 1: Extract quantity (always try this first)
        quantity_data = self._extract_quantity(cleaned)
        
        # Step 2: Extract size
        size = self._extract_size(cleaned)
        
        # Step 3: Extract material
        material = self._extract_material(cleaned)
        
        # Step 4: Extract color
        color = self._extract_color(cleaned)
        
        # Step 5: Determine product name (what's left after removing extracted parts)
        product_name = self._extract_product_name(
            cleaned, 
            quantity_data, 
            size, 
            material, 
            color
        )
        
        # Step 6: Categorize the product
        category = self._categorize_product(product_name)
        
        # Step 7: Extract any additional specifications
        specifications = self._extract_specifications(cleaned)
        
        return {
            "product_name": product_name,
            "category": category,
            "quantity": quantity_data["quantity"],
            "unit": quantity_data["unit"],
            "material": material,
            "size": size,
            "color": color,
            "specifications": specifications,
            "original_description": raw_description.strip()
        }
    
    
    def _clean_description(self, text: str) -> str:
        """
        Clean and normalize the description.
        """
        # Convert to lowercase for easier matching
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters (but keep hyphens and slashes)
        text = re.sub(r'[^\w\s\-/.]', '', text)
        
        return text
    
    
    def _extract_quantity(self, text: str) -> Dict:
        """
        Extract quantity and unit from text.
        
        Returns:
            {"quantity": int, "unit": str}
        """
        # Pattern 1: "500 units", "100 pieces", "50 boxes"
        pattern1 = r'(\d+)\s*(' + '|'.join(self.units) + r')'
        match = re.search(pattern1, text)
        
        if match:
            return {
                "quantity": int(match.group(1)),
                "unit": match.group(2)
            }
        
        # Pattern 2: Just a number at the start
        pattern2 = r'^(\d+)\s+'
        match = re.search(pattern2, text)
        
        if match:
            return {
                "quantity": int(match.group(1)),
                "unit": "units"  # Default unit
            }
        
        # Pattern 3: Number anywhere in text
        pattern3 = r'\b(\d+)\b'
        match = re.search(pattern3, text)
        
        if match:
            return {
                "quantity": int(match.group(1)),
                "unit": "units"
            }
        
        # Default: quantity 1
        return {
            "quantity": 1,
            "unit": "units"
        }
    
    
    def _extract_size(self, text: str) -> Optional[str]:
        """
        Extract size information.
        
        Patterns:
        - "size L", "size large"
        - "XL", "XXL"
        - "10 inch", "5 cm"
        - "small", "medium", "large"
        """
        # Pattern 1: "size X"
        match = re.search(r'size\s+([a-z0-9]+)', text)
        if match:
            return match.group(1).upper()
        
        # Pattern 2: Common sizes (S, M, L, XL, XXL, XXXL)
        match = re.search(r'\b(xs|s|m|l|xl|xxl|xxxl)\b', text)
        if match:
            return match.group(1).upper()
        
        # Pattern 3: Sizes with measurements (10 inch, 5cm, etc.)
        match = re.search(r'(\d+)\s*(inch|cm|mm|m|ft)', text)
        if match:
            return f"{match.group(1)}{match.group(2)}"
        
        # Pattern 4: Small, Medium, Large
        size_words = ["small", "medium", "large", "extra large"]
        for size_word in size_words:
            if size_word in text:
                return size_word.title()
        
        return None
    
    
    def _extract_material(self, text: str) -> Optional[str]:
        """
        Extract material information.
        """
        common_materials = [
            "nitrile", "latex", "vinyl", "rubber",
            "steel", "aluminum", "aluminium", "plastic", "wood",
            "cotton", "polyester", "nylon", "leather",
            "glass", "ceramic", "paper", "cardboard",
            "stainless steel", "copper", "brass", "iron"
        ]
        
        for material in common_materials:
            if material in text:
                return material.title()
        
        # Check for material patterns
        match = re.search(r'made of (\w+)|(\w+) material', text)
        if match:
            return (match.group(1) or match.group(2)).title()
        
        return None
    
    
    def _extract_color(self, text: str) -> Optional[str]:
        """
        Extract color information.
        """
        common_colors = [
            "red", "blue", "green", "yellow", "black", "white",
            "orange", "purple", "pink", "brown", "gray", "grey",
            "silver", "gold", "beige", "navy", "maroon"
        ]
        
        for color in common_colors:
            if color in text:
                return color.title()
        
        return None
    
    
    def _extract_product_name(
        self,
        text: str,
        quantity_data: Dict,
        size: Optional[str],
        material: Optional[str],
        color: Optional[str]
    ) -> str:
        """
        Extract the core product name by removing extracted attributes.
        """
        # Start with full text
        product_text = text
        
        # Remove quantity
        product_text = re.sub(str(quantity_data["quantity"]), '', product_text)
        product_text = re.sub(quantity_data["unit"], '', product_text)
        
        # Remove size
        if size:
            product_text = re.sub(r'size\s+' + re.escape(size.lower()), '', product_text)
            product_text = re.sub(r'\b' + re.escape(size.lower()) + r'\b', '', product_text)
        
        # Remove material
        if material:
            product_text = re.sub(re.escape(material.lower()), '', product_text)
        
        # Remove color
        if color:
            product_text = re.sub(re.escape(color.lower()), '', product_text)
        
        # Clean up
        product_text = re.sub(r'\s+', ' ', product_text).strip()
        
        # Remove common filler words
        filler_words = ["of", "for", "with", "and", "or", "the", "a", "an"]
        words = product_text.split()
        words = [w for w in words if w not in filler_words]
        product_text = ' '.join(words)
        
        # Capitalize properly
        product_text = product_text.title()
        
        # If empty, use original text
        if not product_text:
            product_text = text.title()
        
        return product_text
    
    
    def _categorize_product(self, product_name: str) -> str:
        """
        Determine product category based on name.
        
        Returns:
            Category string like "safety_equipment", "office_supplies", etc.
        """
        product_lower = product_name.lower()
        
        # Check each category's keywords
        for category, keywords in self.categories.items():
            for keyword in keywords:
                if keyword in product_lower:
                    return category
        
        # Default category if no match
        return "general"
    
    
    def _extract_specifications(self, text: str) -> Dict:
        """
        Extract any additional specifications not captured elsewhere.
        
        Returns:
            Dictionary of additional attributes
        """
        specs = {}
        
        # Check for brand
        brand_match = re.search(r'brand\s+(\w+)', text)
        if brand_match:
            specs["brand"] = brand_match.group(1).title()
        
        # Check for model
        model_match = re.search(r'model\s+([a-z0-9\-]+)', text)
        if model_match:
            specs["model"] = model_match.group(1).upper()
        
        # Check for weight
        weight_match = re.search(r'(\d+)\s*(kg|grams|g|pounds|lbs)', text)
        if weight_match:
            specs["weight"] = f"{weight_match.group(1)} {weight_match.group(2)}"
        
        # Check for dimensions
        dimension_match = re.search(r'(\d+)x(\d+)x?(\d+)?', text)
        if dimension_match:
            specs["dimensions"] = dimension_match.group(0)
        
        return specs


# ─────────────────────────────────────────────────────────────────────
# Advanced Parser (Uses LLM for Complex Cases)
# ─────────────────────────────────────────────────────────────────────

class LLMSpecParser:
    """
    Advanced parser that uses OpenAI GPT for complex descriptions.
    
    Use this when the basic parser isn't sufficient or for very
    complex/ambiguous product descriptions.
    """
    
    def __init__(self):
        """
        Initialize LLM parser.
        """
        self.basic_parser = SpecParser()
    
    
    async def parse(self, raw_description: str) -> Dict:
        """
        Parse using LLM with structured output.
        """
        try:
            # First try basic parser
            basic_result = await self.basic_parser.parse(raw_description)
            
            # If basic parser found a good product name and category, use it
            if (basic_result["product_name"] and 
                basic_result["category"] != "general" and
                basic_result["quantity"] > 0):
                return basic_result
            
            # Otherwise, use LLM for better parsing
            llm_result = await self._parse_with_llm(raw_description)
            
            # Merge LLM results with basic parser (LLM takes precedence)
            return {**basic_result, **llm_result}
        
        except Exception as e:
            # Fallback to basic parser if LLM fails
            return await self.basic_parser.parse(raw_description)
    
    
    async def _parse_with_llm(self, description: str) -> Dict:
        """
        Use OpenAI to parse complex descriptions.
        
        This will be implemented when we write services/llm_service.py
        """
        from services.llm_service import parse_product_description
        
        return await parse_product_description(description)


# ─────────────────────────────────────────────────────────────────────
# Validation Functions
# ─────────────────────────────────────────────────────────────────────

def validate_parsed_spec(spec: Dict) -> Dict:
    """
    Validate and clean parsed specification.
    
    Returns:
        {
            "is_valid": bool,
            "errors": List[str],
            "warnings": List[str]
        }
    """
    errors = []
    warnings = []
    
    # Check required fields
    if not spec.get("product_name"):
        errors.append("Product name is required")
    
    if not spec.get("category"):
        errors.append("Product category is required")
    
    if spec.get("quantity", 0) <= 0:
        errors.append("Quantity must be greater than 0")
    
    # Check reasonable values
    if spec.get("quantity", 0) > 1000000:
        warnings.append("Quantity is very large - please verify")
    
    # Check product name length
    if spec.get("product_name") and len(spec["product_name"]) > 200:
        warnings.append("Product name is very long - may need simplification")
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def normalize_unit(unit: str) -> str:
    """
    Normalize unit names to standard forms.
    
    Examples:
        "pcs" → "pieces"
        "kg" → "kilograms"
        "l" → "liters"
    """
    unit_mappings = {
        "pcs": "pieces",
        "pc": "pieces",
        "kg": "kilograms",
        "g": "grams",
        "l": "liters",
        "ml": "milliliters",
        "m": "meters",
        "cm": "centimeters",
        "ft": "feet",
        "in": "inches"
    }
    
    return unit_mappings.get(unit.lower(), unit)


# ─────────────────────────────────────────────────────────────────────
# Example Usage
# ─────────────────────────────────────────────────────────────────────

async def example_usage():
    """
    Examples of how to use the parser.
    """
    parser = SpecParser()
    
    # Example 1: Simple description
    result1 = await parser.parse("500 industrial gloves size L nitrile")
    print(result1)
    # Output:
    # {
    #     "product_name": "Industrial Gloves",
    #     "category": "safety_equipment",
    #     "quantity": 500,
    #     "unit": "units",
    #     "material": "Nitrile",
    #     "size": "L",
    #     "color": None,
    #     "specifications": {},
    #     "original_description": "500 industrial gloves size L nitrile"
    # }
    
    # Example 2: With color
    result2 = await parser.parse("100 blue pens")
    print(result2)
    
    # Example 3: Complex description
    result3 = await parser.parse("Office chairs, black leather, adjustable height, 20 pieces")
    print(result3)


if __name__ == "__main__":
    import asyncio
    asyncio.run(example_usage())