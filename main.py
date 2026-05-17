import time
import os
import json
import re
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

from utils.logger import logger
from scraper_facebook import scrape_facebook_public
# from scraper_bark import scrape_bark_listings
from scraper_craigslist import scrape_craigslist
from scraper_kijiji import scrape_kijiji
from scraper_reddit import scrape_reddit
from scraper_nextdoor import scrape_nextdoor
from qualifier import qualify_lead
from sheets_handler import save_to_sheets
from telegram_notifier import send_telegram_notification
from insforge_db import save_to_insforge

load_dotenv(override=True)

# Config
INTERVAL = int(os.getenv("SCRAPE_INTERVAL_MINUTES", 60))
SCORE_THRESHOLD = int(os.getenv("QUALIFICATION_SCORE_THRESHOLD", 5))

# Track processed URLs across sessions
PROCESSED_URLS_FILE = os.getenv("PROCESSED_URLS_FILE_OVERRIDE", os.path.join(os.path.dirname(__file__), 'processed_urls.json'))
PROCESSED_URLS = set()

if os.path.exists(PROCESSED_URLS_FILE):
    try:
        with open(PROCESSED_URLS_FILE, 'r') as f:
            PROCESSED_URLS = set(json.load(f))
        logger.info(f"Loaded {len(PROCESSED_URLS)} processed URLs from disk.")
    except Exception as e:
        logger.error(f"Error loading processed URLs: {e}")

def save_processed_urls():
    try:
        with open(PROCESSED_URLS_FILE, 'w') as f:
            json.dump(list(PROCESSED_URLS), f)
    except Exception as e:
        logger.error(f"Error saving processed URLs: {e}")

def save_to_local_fallback(lead, qualification):
    """
    Saves a qualified lead to a local JSON file in the dashboard's public folder.
    This acts as a fallback when the InsForge database is unreachable.
    """
    file_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'public', 'leads.json')
    
    # Structure match for the Lead interface in dashboard/src/App.tsx
    new_lead = {
        "id": f"local_{int(time.time())}",
        "customer_name": qualification.get("customer_name", "Unknown Potential Client"),
        "phone_number": qualification.get("phone_number", ""),
        "move_date": qualification.get("move_date", ""),
        "origin_neighborhood": qualification.get("origin_neighborhood", ""),
        "destination_city": qualification.get("destination_city", ""),
        "inventory_summary": qualification.get("inventory_summary", ""),
        "packing_service": qualification.get("packing_service", False),
        "call_summary": qualification.get("call_summary", ""),
        "raw_text": lead.get("text", ""),
        "source_url": lead.get("url", ""),
        "is_moving_lead": qualification.get("is_moving_lead", True),
        "lead_intent_score": qualification.get("lead_intent_score", 0),
        "pain_points": qualification.get("pain_points", ""),
        "estimated_quote": qualification.get("estimated_quote", ""),
        "whatsapp_draft": qualification.get("whatsapp_draft", ""),
        "created_at": datetime.now().isoformat(),
        "is_client": False
    }

    try:
        leads = []
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                content = f.read().strip()
                if content:
                    leads = json.loads(content)
        
        # Check for duplicates by URL
        if any(l.get('source_url') == new_lead['source_url'] for l in leads):
            return

        leads.insert(0, new_lead) # Newest first
        
        with open(file_path, 'w') as f:
            json.dump(leads, f, indent=2)
            
        logger.info(f"✅ Lead saved to local fallback: {file_path}")
    except Exception as e:
        logger.error(f"Error saving to local fallback: {e}")

def is_competitor(text):
    """
    Checks if the lead text looks like an advertisement from another moving company.
    """
    competitor_keywords = [
        "licensed and insured", "best rates", "low rates", "call now for a quote",
        "professional movers", "booking now", "moving service available",
        "our team is ready", "discount moving", "last minute specials",
        "reliable moving", "affordable moving", "truck included", "men & truck",
        "swamper", "junk removal services", "moving services", "same day junk",
        "we pay cash", "cash for cars", "junk car buyers"
    ]
    lower_text = text.lower()
    if any(kw in lower_text for kw in competitor_keywords):
        return True
    
    # Check for phone number patterns in title (very common in competitor ads)
    if re.search(r'\d{3}[-\s\.]?\d{3}[-\s\.]?\d{4}', text):
        # But only if it also contains moving keywords (to avoid filtering out real people who leave numbers)
        moving_kws = ["moving", "mover", "junk", "removal", "hauling", "truck"]
        if any(kw in lower_text for kw in moving_kws):
            # If it's a very short text with a phone number, it's likely an ad
            if len(text) < 100:
                return True
    return False

def is_junk_lead(text):
    """
    Identifies clear 'Moving Sale' or 'Garage Sale' posts.
    Much more lenient now to avoid skipping real leads.
    """
    junk_keywords = [
        "moving sale", "garage sale", "estate sale", "yard sale", 
        "selling my", "must go", "condition", "negotiable"
    ]
    lower_text = text.lower()
    # Only skip if it's explicitly a 'sale'
    if any(jk in lower_text for jk in junk_keywords):
        # Double check it's not a 'moving service' post
        if "need" in lower_text or "help" in lower_text or "hire" in lower_text:
            return False
        return True
    return False

def job():
    logger.info("Starting lead generation cycle...")
    
    all_raw_leads = []
    
    # 1. Scrape
    try:
        reddit_leads = scrape_reddit()
        all_raw_leads.extend(reddit_leads)
    except Exception as e:
        logger.error(f"Reddit scraping failed: {e}")

    try:
        craigslist_leads = scrape_craigslist()
        all_raw_leads.extend(craigslist_leads)
    except Exception as e:
        logger.error(f"Craigslist scraping failed: {e}")

    try:
        kijiji_leads = scrape_kijiji()
        all_raw_leads.extend(kijiji_leads)
    except Exception as e:
        logger.error(f"Kijiji scraping failed: {e}")

    try:
        nextdoor_leads = scrape_nextdoor()
        all_raw_leads.extend(nextdoor_leads)
    except Exception as e:
        logger.error(f"Nextdoor scraping failed: {e}")

    try:
        fb_leads = scrape_facebook_public()
        all_raw_leads.extend(fb_leads)
    except Exception as e:
        logger.error(f"FB scraping failed: {e}")

    # try:
    #     bark_leads = scrape_bark_listings()
    #     all_raw_leads.extend(bark_leads)
    # except Exception as e:
    #     logger.error(f"Bark scraping failed: {e}")

    logger.info(f"Total raw leads collected: {len(all_raw_leads)}")

    # 2. Qualify and Send (Processing ALL leads as requested)
    # Note: This will take significant time with free AI models due to rate limits.
    
    # Sort leads to prioritize high-intent sources (Reddit & Nextdoor first)
    source_priority = {
        "Reddit": 0, "Nextdoor": 1, "Craigslist": 2, "Facebook Group": 3, "Kijiji": 4
    }
    all_raw_leads.sort(key=lambda x: source_priority.get(
        next((k for k in source_priority if k in x.get('source', '')), "Kijiji"),
        99
    ))
    
    for lead in all_raw_leads:
        url = lead.get('url')
        if url in PROCESSED_URLS and url != "N/A":
            continue
        
        PROCESSED_URLS.add(url)
        save_processed_urls()
        
        source = lead.get('source', '')
        # If source is local, skip city word filter
        local_sources = [
            "Facebook Group", "Nextdoor", "Reddit: r/Calgary",
            "Reddit: r/Edmonton", "Craigslist: Calgary",
            "Craigslist: Edmonton", "Kijiji"
        ]
        
        if not any(ls in source for ls in local_sources):
            text = lead.get('text', '').lower()
            if not any(kw in text for kw in ["calgary", "alberta", "yyc", "edmonton"]):
                continue
        
        # 3. Competitor & Junk Filter
        text = lead.get('text', '')
        if is_competitor(text) or is_junk_lead(text):
            logger.info(f"Skipping junk/competitor lead: {url}")
            continue

        # 4. Qualify with AI
        logger.info(f"Qualifying lead: {url}")
        qualification = qualify_lead(lead['text'])
        
        if not qualification:
            continue
            
        # 4. Score Filter
        is_qualified = qualification.get('is_moving_lead', False)
        
        if is_qualified:
            logger.info(f"HOT LEAD FOUND: {lead['url']}")
            
            # 5. Local Fallback Sync (Always sync locally for dashboard reliability)
            save_to_local_fallback(lead, qualification)

            # 6. Save to Sheets & InsForge Database
            try:
                save_to_sheets(lead, qualification)
            except Exception as e:
                logger.error(f"Error saving to Sheets: {e}")
                
            try:
                save_to_insforge(lead, qualification)
            except Exception as e:
                logger.error(f"Error saving to InsForge: {e}")
            
            # 7. Notify Telegram
            try:
                send_telegram_notification(lead, qualification)
            except Exception as e:
                logger.error(f"Error sending Telegram notification: {e}")
            
            PROCESSED_URLS.add(url)
        else:
            logger.info(f"Lead disqualified: {url}")

    logger.info("Cycle complete. Waiting for next interval...")

def main():
    logger.info("=== Autonomous Moving Lead System Started ===")
    
    # Run once immediately
    job()
    
    if os.getenv("GITHUB_ACTIONS"):
        logger.info("Running in GitHub Actions - complete. Exiting.")
        return
        
    # Schedule (Local infinite loop)
    scheduler = BlockingScheduler()
    scheduler.add_job(job, 'interval', minutes=INTERVAL)
    
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("System stopped manually.")
    except Exception as e:
        logger.critical(f"System crashed: {e}")


if __name__ == "__main__":
    main()
