import os
import requests
import json
from utils.logger import logger

# Load the InsForge project config to get the REST URL and API key
config_path = os.path.join(os.path.dirname(__file__), '.insforge', 'project.json')

API_URL = None
API_KEY = None

try:
    with open(config_path, 'r') as f:
        insforge_config = json.load(f)
        # Construct the PostgREST table URL
        API_URL = insforge_config.get('oss_host') + '/rest/v1/moving_leads'
        API_KEY = insforge_config.get('api_key')
except FileNotFoundError:
    logger.error("Could not find .insforge/project.json file. Run 'npx @insforge/cli link' first.")
except Exception as e:
    logger.error(f"Error reading InsForge config: {e}")

def save_to_insforge(lead, qualification):
    """
    Saves a qualified lead to the InsForge Postgres database directly.
    """
    if not API_URL or not API_KEY:
        logger.error("InsForge config missing, skipping DB insert.")
        return False
        
    headers = {
        "apikey": API_KEY,
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    payload = {
        "customer_name": qualification.get("customer_name", ""),
        "phone_number": qualification.get("phone_number", ""),
        "move_date": qualification.get("move_date", ""),
        "origin_neighborhood": qualification.get("origin_neighborhood", ""),
        "destination_city": qualification.get("destination_city", ""),
        "inventory_summary": qualification.get("inventory_summary", ""),
        "packing_service": qualification.get("packing_service", False),
        "call_summary": qualification.get("call_summary", ""),
        "raw_text": lead.get("text", ""),
        "source_url": lead.get("url", ""),
        "is_moving_lead": qualification.get("is_moving_lead", False)
    }
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        
        # If it's a conflict (23505), it means the unique URL is already in the DB
        if response.status_code == 409:
            logger.info("Lead already exists in InsForge Database (Duplicate URL Check passed).")
            return False
            
        response.raise_for_status()
        logger.info(f"🚀 Successfully saved lead to InsForge Database: {lead.get('url')}")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Error saving to InsForge Database: {e}")
        return False
