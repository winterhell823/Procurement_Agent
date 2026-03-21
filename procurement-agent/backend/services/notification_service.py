import httpx
from config import settings
from typing import Optional

#---Telegram-------------

async def send_telegram(chat_id: str, message: str) -> bool:
    """Send a message to a Telegram Bot api."""
    if not settings.TELEGRAM_BOT_TOKEN:
        print("Telegram bot token not configured - skipping")
        return False
    
    url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        async with httpx.AsyncClient(timeout =10.0) as client:
            response = await client.post(url, json=payload)
            return response.status_code == 200
    except Exception as e:
            print(f"Telegram send failed: {e}")
            return False
    
#---whatsapp-------------
async def send_whatsapp(to_number: str, message: str) -> bool:
    
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
         print("Twilio not configured - skipping")
         return False
    
    url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
 
    payload = {
        "From": f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}",
        "To":   f"whatsapp:{to_number}",
        "Body": message
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                url,
                data=payload,
                auth=(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            )
            return res.status_code == 201
    except Exception as e:
        print(f"WhatsApp send failed: {e}")
        return False
    
#--Main Notification Function---

async def notify_quotes_ready(
    user_phone:    Optional[str],
    user_telegram: Optional[str],
    product_name:  str,
    quotes:        list[dict],
    procurement_id: str
):
   """
    Called by orchestrator when all agents finish.
    Sends notification via WhatsApp + Telegram (whichever is configured).
    """
   best = next((q for q in quotes if q.get("is_recommended")), None)
   received = [q for q in quotes if q.get("status") == "received"]
 
    # Build message
   message = f"""
🤖 *ProcureAI — Quotes Ready!*
 
📦 Product: *{product_name}*
📊 Quotes received: *{len(received)}*
 
{"🏆 Best Quote:" if best else ""}
{"• Supplier: " + best["supplier_name"] if best else ""}
{"• Price: ₹" + str(best.get("unit_price", "N/A")) + " / unit" if best else ""}
{"• Delivery: " + str(best.get("delivery_days", "N/A")) + " days" if best else ""}
 
🔗 View all quotes:
http://localhost:3000/quotes/{procurement_id}
    """.strip()
 
    # Send both in parallel
   results = []
 
   if user_phone:
        results.append(await send_whatsapp(user_phone, message))
 
   if user_telegram:
        results.append(await send_telegram(user_telegram, message))
 
   return any(results)
 

     
    
    