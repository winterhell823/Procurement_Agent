import httpx
from datetime import datetime, timedelta
from typing import Optional
from config import settings
 
# In-memory cache so we don't call the API every time
_rate_cache: dict = {}
_cache_expiry: Optional[datetime] = None
CACHE_HOURS = 6  # refresh rates every 6 hours
 
# Fallback hardcoded rates if API is unavailable
FALLBACK_RATES = {
    "USD": 83.5,
    "EUR": 90.2,
    "GBP": 105.8,
    "AED": 22.7,
    "SGD": 62.1,
    "CNY": 11.5,
    "JPY": 0.56,
    "INR": 1.0
}
 
CURRENCY_SYMBOLS = {
    "USD": "$",
    "EUR": "€",
    "GBP": "£",
    "AED": "د.إ",
    "SGD": "S$",
    "CNY": "¥",
    "INR": "₹"
}
 
 
async def get_exchange_rates() -> dict:
    """
    Fetch live rates from exchangerate-api.com
    Falls back to hardcoded rates if API fails or key not set.
    """
    global _rate_cache, _cache_expiry
 
    # Return cached rates if still fresh
    if _rate_cache and _cache_expiry and datetime.utcnow() < _cache_expiry:
        return _rate_cache
 
    # Try live API
    if settings.EXCHANGE_RATE_API_KEY:
        try:
            url = f"https://v6.exchangerate-api.com/v6/{settings.EXCHANGE_RATE_API_KEY}/latest/INR"
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(url)
                data = res.json()
 
                if data.get("result") == "success":
                    # API returns rates FROM INR, we want TO INR
                    # So invert: 1 USD = rates["USD"] INR
                    base_rates = data.get("conversion_rates", {})
                    inr_rates = {}
                    for currency, rate in base_rates.items():
                        if rate > 0:
                            inr_rates[currency] = 1 / rate * base_rates.get("INR", 1)
 
                    _rate_cache   = inr_rates
                    _cache_expiry = datetime.utcnow() + timedelta(hours=CACHE_HOURS)
                    print(f"[Currency] Rates updated at {datetime.utcnow()}")
                    return _rate_cache
 
        except Exception as e:
            print(f"[Currency] API failed, using fallback rates: {e}")
 
    # Fallback
    _rate_cache   = FALLBACK_RATES
    _cache_expiry = datetime.utcnow() + timedelta(hours=1)
    return _rate_cache
 
 
async def convert_to_inr(amount: float, from_currency: str) -> dict:
    """
    Convert an amount from any currency to INR.
    Returns dict with original and converted values.
    """
    if not amount:
        return {"original": amount, "currency": from_currency, "inr": None}
 
    currency = from_currency.upper().strip()
 
    if currency == "INR":
        return {
            "original":  amount,
            "currency":  "INR",
            "inr":       amount,
            "rate":      1.0,
            "converted": False
        }
 
    rates = await get_exchange_rates()
    rate  = rates.get(currency, FALLBACK_RATES.get(currency, 1.0))
    inr_amount = round(amount * rate, 2)
 
    return {
        "original":      amount,
        "currency":      currency,
        "symbol":        CURRENCY_SYMBOLS.get(currency, currency),
        "inr":           inr_amount,
        "rate":          rate,
        "rate_note":     f"1 {currency} = ₹{rate}",
        "converted":     True,
        "rate_date":     datetime.utcnow().strftime("%Y-%m-%d")
    }
 
 
async def normalize_quote_currency(quote: dict) -> dict:
    """
    Takes a quote dict, converts unit_price and total_price to INR
    if they are in a foreign currency.
    Adds inr_unit_price and inr_total_price fields.
    """
    currency = (quote.get("currency") or "INR").upper()
 
    if currency == "INR":
        quote["inr_unit_price"]  = quote.get("unit_price")
        quote["inr_total_price"] = quote.get("total_price")
        return quote
 
    if quote.get("unit_price"):
        result = await convert_to_inr(quote["unit_price"], currency)
        quote["inr_unit_price"]     = result["inr"]
        quote["currency_converted"] = True
        quote["exchange_rate_note"] = result["rate_note"]
 
    if quote.get("total_price"):
        result = await convert_to_inr(quote["total_price"], currency)
        quote["inr_total_price"] = result["inr"]
 
    return quote
 
 
async def normalize_quotes_currency(quotes: list[dict]) -> list[dict]:
    """Normalize currency for all quotes in a list."""
    return [await normalize_quote_currency(q) for q in quotes]