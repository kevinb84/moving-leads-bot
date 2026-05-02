import os
import json
import time
import re
from openai import OpenAI
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv(override=True)

# Configure Providers
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
openrouter_client = OpenAI(
    api_key=OPENROUTER_API_KEY,
    base_url="https://openrouter.ai/api/v1"
) if OPENROUTER_API_KEY else None

SYSTEM_PROMPT = """
You are an expert lead qualification assistant for a high-end moving and junk removal company. 
Your goal is to distinguish between 'HOT LEADS' (people looking to hire a mover or junk remover) and 'JUNK LEADS' (people selling items, looking for moving boxes, etc.).

CRITICAL LEAD QUALIFICATION RULES:

1. INTENT IS EVERYTHING:
   - If the person is asking for moving help, junk removal, movers, or a quote -> is_moving_lead = true
   - If the person is offering moving services (competitor) -> is_moving_lead = false
   - If the person is selling items (furniture, garage sale) -> is_moving_lead = false

2. SCORING SYSTEM (0 to 10):
   - Score high (8-10) for high intent: "need a mover ASAP", "looking to hire", "need quote"
   - Score medium (5-7) for general intent: "moving next month", "recommendations for movers", "need help moving"
   - Score low (0-4) for low intent or irrelevant posts.

3. FINAL DECISION:
   - ONLY set is_moving_lead to true IF the person is genuinely seeking moving/junk removal services (Score >= 5).

Return EXCLUSIVELY a JSON object with this EXACT structure:
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
  "lead_intent_score": integer,
  "pain_points": "string",
  "estimated_quote": "string",
  "whatsapp_draft": "string",
  "relevance_explanation": "string (Briefly explain your intent assessment)"
}
"""

def qualify_with_openai(text):
    if not openai_client: return None
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Analyze this lead text:\n\"\"\"\n{text}\n\"\"\""
                }
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        logger.error(f"OpenAI Qualification Failed: {e}")
        return None

def qualify_with_openrouter(text):
    if not openrouter_client: return None
    
    # Pruned list of the most stable free models
    FREE_MODELS = [
        "google/gemma-3-4b-it:free",
        "google/gemma-3-12b-it:free",
        "google/gemma-3-27b-it:free",
        "qwen/qwen3-coder:free",
        "meta-llama/llama-3.2-3b-instruct:free",
        "liquid/lfm-2.5-1.2b-instruct:free"
    ]
    
    attempts = 0
    for model_name in FREE_MODELS:
        try:
            logger.info(f"Attempting OpenRouter Qualification ({model_name})...")
            
            response = openrouter_client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT + "\nIMPORTANT: JSON ONLY."
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this lead text and return JSON:\n{text}"
                    }
                ],
                timeout=15 # Don't wait forever
            )
            
            content = response.choices[0].message.content.strip()
            
            # 1. Robust JSON Extraction
            start_idx = content.find('{')
            end_idx = content.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                content = content[start_idx:end_idx + 1]
            else:
                continue
            
            # 2. Aggressive Cleaning
            content = re.sub(r',\s*([\]}])', r'\1', content)
            content = "".join(char for char in content if ord(char) >= 32 or char in "\n\r\t")
            
            return json.loads(content)

        except Exception as e:
            if "429" in str(e):
                attempts += 1
                if attempts >= 3:
                    logger.warning("Provider overloaded. Skipping lead to move faster.")
                    return None
                continue
            logger.error(f"OpenRouter Error on {model_name}: {e}")
            continue
            
    return None

def qualify_with_keywords(text):
    """
    Super fast fallback if all AI models are busy.
    Looks for high-intent moving keywords using the STRICT criteria.
    """
    lower_text = text.lower()
    
    # 4. Disqualification Filters (STRICT)
    disqualifiers = ["just checking prices", "cheapest movers", "planning next month", "planning next year", "diy move", "truck rental", "selling my"]
    if any(dq in lower_text for dq in disqualifiers):
        return None
        
    score = 0
    signals_present = 0
    
    # 1. Strong Intent / Urgency (+3)
    primary_kws = ["need a mover today", "asap move", "urgent move", "mover canceled", "mover cancelled", "last minute move", "need movers now", "urgent", "today", "asap"]
    if any(kw in lower_text for kw in primary_kws):
        score += 3
        signals_present += 1 # Counts as Timeline
        
    # Clear Date (+2)
    timeline_kws = ["tomorrow", "this weekend", "moving this week", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if any(kw in lower_text for kw in timeline_kws):
        score += 2
        signals_present += 1 # Counts as Timeline
        
    # Location Mentioned (+2)
    location_kws = ["calgary", "edmonton", "ne", "nw", "se", "sw", "downtown", "beltline", "sandstone", "acadia"]
    if any(kw in lower_text for kw in location_kws):
        score += 2
        signals_present += 1 # Counts as Location
        
    # Move Type (+1)
    move_type_kws = ["apartment", "house", "office", "storage", "basement", "condo", "junk removal"]
    if any(kw in lower_text for kw in move_type_kws):
        score += 1
        signals_present += 1 # Counts as Move Type
        
    # Emotional Signals (+2)
    emotional_kws = ["disappointed", "stressed", "cancelled", "canceled", "need help fast", "running out of time"]
    if any(kw in lower_text for kw in emotional_kws):
        score += 2
        
    # Budget/Quote (+1)
    if "quote" in lower_text or "price" in lower_text or "cost" in lower_text:
        score += 1

    # Secondary Intent (Base check)
    secondary_kws = ["looking for movers", "recommend moving company", "office relocation", "apartment move", "help moving", "need a mover"]
    if any(kw in lower_text for kw in secondary_kws):
        # We don't add to score here because the components (office, apartment, move) are already scored above,
        # but we use it as a general signal booster if they missed other keywords
        if score < 2:
            score += 2
            
    # FINAL DECISION: Any strong intent signals or secondary intent keywords
    if score >= 1 or signals_present >= 1 or any(kw in lower_text for kw in secondary_kws):
        final_score = max(5, min(score * 2 + 3, 10))
        return {
            "is_moving_lead": True,
            "customer_name": "Potential Client (Fast Match)",
            "phone_number": "Check post for details",
            "move_date": "Not extracted (Fast Match)",
            "inventory_summary": f"Detected via keywords",
            "packing_service": False,
            "call_summary": text[:200] + "...",
            "lead_intent_score": final_score,
            "relevance_explanation": f"AUTOMATIC FALLBACK: Found strong moving intent keywords."
        }
    return None

def qualify_lead(text):
    """
    Main entry point for lead qualification.
    Attempts OpenAI first, falls back to OpenRouter, then to Keywords.
    """
    # Try OpenAI first
    result = qualify_with_openai(text)
    
    if result is None:
        logger.warning("OpenAI failed or quota exceeded. Switching to OpenRouter...")
        result = qualify_with_openrouter(text)
        
    if result is None:
        logger.warning("AI providers failing/slow. Using Keyword Fallback...")
        result = qualify_with_keywords(text)
        
    if result:
        # Final safety check on structure
        if "is_moving_lead" not in result:
            result["is_moving_lead"] = False
        return result
        
    return None

if __name__ == "__main__":
    # Test sample
    test_text = "Hi everyone! I'm moving from NW Calgary to Beltline on July 10th. I have a 2-bedroom house and need help with loading and packing. My number is 403-555-0199. Thanks!"
    print("Testing Qualification System...")
    result = qualify_lead(test_text)
    if result:
        print(json.dumps(result, indent=2))
    else:
        print("Qualification Failed on all providers.")
