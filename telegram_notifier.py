import os
import requests
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv(override=True)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram_notification(lead_data, qualification):
    """
    Sends a formatted telegram notification.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials missing. Skipping notification.")
        return

    data = qualification
    
    score_emoji = "🔥"
    
    message = (
        f"{score_emoji} <b>New Hot Moving Lead!</b>\n\n"
        f"👤 <b>Name:</b> {data.get('customer_name', 'Unknown')}\n"
        f"📞 <b>Phone:</b> {data.get('phone_number', 'Unknown')}\n"
        f"📅 <b>Move Date:</b> {data.get('move_date', 'Unknown')}\n"
        f"📦 <b>Inventory:</b> {data.get('inventory_summary', 'Unknown')}\n"
        f"📍 <b>From:</b> {data.get('origin_neighborhood', 'Unknown')}\n"
        f"🏁 <b>To:</b> {data.get('destination_city', 'Unknown')}\n"
        f"🛠 <b>Packing:</b> {'Yes' if data.get('packing_service') else 'No'}\n\n"
        f"📝 <b>Call Summary:</b> {data.get('call_summary', 'Unknown')}\n"
        f"💰 <b>Estimated Quote:</b> {data.get('estimated_quote', 'N/A')}\n"
        f"💬 <b>WhatsApp Draft:</b> <i>{data.get('whatsapp_draft', 'N/A')}</i>\n\n"
        f"🔗 <a href='{lead_data.get('url', '#')}'>View Original Post</a>"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }

    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        logger.info(f"Telegram notification sent for lead: {data.get('customer_name')}")
    except Exception as e:
        logger.error(f"Failed to send Telegram notification: {e}")

if __name__ == "__main__":
    # Test
    sample_lead = {"url": "https://facebook.com/test"}
    sample_qual = {
        "is_moving_lead": True,
        "customer_name": "John Doe",
        "phone_number": "555-0123",
        "move_date": "July 1st",
        "origin_neighborhood": "Dallas",
        "destination_city": "Austin",
        "inventory_summary": "3 Bedrooms",
        "packing_service": True,
        "call_summary": "Family relocating to Austin looking for local moving service.",
        "estimated_quote": "$450 - $600 (Based on 3 Bedrooms)",
        "whatsapp_draft": "Hi John! I saw your post looking for movers regarding your 3 Bedroom move from Dallas to Austin. We have local expertise and can handle the heavy lifting for around $450 - $600. Let me know if you'd like to book!"
    }
    send_telegram_notification(sample_lead, sample_qual)
