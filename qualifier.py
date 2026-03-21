import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv(override=True)

# Configure OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    logger.error("OPENAI_API_KEY not found in environment")
    client = None

SYSTEM_PROMPT = """
You are an expert lead qualification assistant for a high-end moving company in Calgary, Alberta.
Your goal is to analyze text from social media posts or lead platforms and identify potential customers who NEED moving services.

CRITICAL RULES:
1. ONLY qualify leads who NEED a mover. Ignore people offering moving services.
2. Focus on Calgary and surrounding Alberta areas.
3. Extract as much detail as possible.
4. If information is missing, use "Unknown".

Extract the following fields from the lead:
- customer_name
- phone_number 
- move_date
- origin_neighborhood (e.g., NW Calgary, Beltline, Airdrie, etc.)
- destination_city (e.g., Calgary)
- inventory_summary (e.g., "Family relocating and searching for housing" or "1-bedroom apartment move")
- packing_service (boolean, true if they need packing/unpacking help)
- call_summary (A 1-2 sentence summary of their post/request)
- estimated_quote (Based on the items/inventory mentioned, give a rough local price estimate. E.g., "$300 - $450" or "Requires evaluation". Assume Calgary local rates around $120-$150/hr for 2 movers)
- whatsapp_draft (A flawlessly polite and friendly first-touch text message greeting introducing your moving company, referencing their specific items/locations, and offering the estimated quote. Keep it concise, no emojis overload)

Return EXCLUSIVELY a JSON object with this EXACT structure (use true/false for booleans, empty string "" if information is missing):
{
  "is_moving_lead": boolean,
  "customer_name": "string",
  "phone_number": "string",
  "move_date": "string",
  "origin_neighborhood": "string",
  "destination_city": "string",
  "inventory_summary": "string",
  "packing_service": boolean,
  "call_summary": "string",
  "estimated_quote": "string",
  "whatsapp_draft": "string"
}
"""

def qualify_lead(text):
    if not client:
        logger.error("OpenAI client not initialized.")
        return None

    try:
        response = client.chat.completions.create(
            model="gpt-4o",  # Using a reliable model for extraction
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyze this lead text:\n\"\"\"\n{text}\n\"\"\""}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result
    except Exception as e:
        logger.error(f"Error qualifying lead with OpenAI: {e}")
        if "401" in str(e):
            logger.critical("Check your OPENAI_API_KEY in .env. It returned 401 Unauthorized.")
        return None

if __name__ == "__main__":
    # Test sample
    test_text = "Hi everyone! I'm moving from NW Calgary to Beltline on July 10th. I have a 2-bedroom house and need help with loading and packing. My number is 403-555-0199. Thanks!"
    print(json.dumps(qualify_lead(test_text), indent=2))
