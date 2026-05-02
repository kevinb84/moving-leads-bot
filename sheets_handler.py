import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
from datetime import datetime
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv(override=True)

GOOGLE_SHEETS_JSON_PATH = os.getenv("GOOGLE_SHEETS_JSON_PATH", "credentials.json")
GOOGLE_SHEET_NAME = os.getenv("GOOGLE_SHEET_NAME", "Moving Leads 2026")

COLUMNS = [
    "Customer Name", "Phone Number", "Move Date", 
    "Origin Neighborhood", "Destination City", "Inventory Summary", 
    "Packing Service", "Call Summary", "Source", "Status", 
    "Timestamp", "Post URL"
]

import json

def get_sheets_client():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = None
    
    # Try loading from Environment Variable first (for Fly.io)
    env_creds = os.getenv("GOOGLE_SHEETS_CREDENTIALS_JSON")
    if env_creds:
        try:
            creds_dict = json.loads(env_creds)
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            logger.info("Loaded Google Sheets credentials from Environment Variable.")
        except Exception as e:
            logger.error(f"Failed to parse GOOGLE_SHEETS_CREDENTIALS_JSON: {e}")
            
    # Fallback to local file
    if not creds:
        if os.path.exists(GOOGLE_SHEETS_JSON_PATH):
            creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SHEETS_JSON_PATH, scope)
            logger.info(f"Loaded Google Sheets credentials from {GOOGLE_SHEETS_JSON_PATH}.")
        else:
            logger.error(f"Google Sheets credentials not found at {GOOGLE_SHEETS_JSON_PATH} or in Environment.")
            return None
            
    client = gspread.authorize(creds)
    return client

def save_to_sheets(lead_data, qualification):
    client = get_sheets_client()
    if not client:
        return

    try:
        try:
            sheet = client.open(GOOGLE_SHEET_NAME).sheet1
        except gspread.exceptions.SpreadsheetNotFound:
            # Auto-create if not found
            logger.info(f"Sheet '{GOOGLE_SHEET_NAME}' not found. Creating new one...")
            sh = client.create(GOOGLE_SHEET_NAME)
            # Share with the service account email if needed (usually it's already the owner)
            # But normally you'd want to share it with your personal email too.
            sheet = sh.sheet1
            sheet.append_row(COLUMNS)
            logger.info(f"Created sheet with headers.")

        data = qualification
        
        row = [
            data.get('customer_name', 'Unknown'),
            data.get('phone_number', 'Unknown'),
            data.get('move_date', 'Unknown'),
            data.get('origin_neighborhood', 'Unknown'),
            data.get('destination_city', 'Unknown'),
            data.get('inventory_summary', 'Unknown'),
            "Yes" if data.get('packing_service') else "No",
            data.get('call_summary', 'Unknown'),
            lead_data.get('source', 'Unknown'),
            lead_data.get('status', 'New'),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            lead_data.get('url', 'N/A')
        ]
        
        sheet.append_row(row)
        logger.info(f"Lead saved to Google Sheets: {data.get('lead_name')}")
        
    except Exception as e:
        logger.error(f"Error saving to Google Sheets: {e}")

if __name__ == "__main__":
    # Test (requires credentials.json to exist)
    pass
