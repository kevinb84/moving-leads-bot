import time
import os
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

from utils.logger import logger
from scraper_facebook import scrape_facebook_public
from scraper_bark import scrape_bark_listings
from qualifier import qualify_lead
from sheets_handler import save_to_sheets
from telegram_notifier import send_telegram_notification
from insforge_db import save_to_insforge

load_dotenv(override=True)

# Config
INTERVAL = int(os.getenv("SCRAPE_INTERVAL_MINUTES", 60))
SCORE_THRESHOLD = int(os.getenv("QUALIFICATION_SCORE_THRESHOLD", 7))

# Track processed URLs to avoid duplicates in a single session
PROCESSED_URLS = set()

def job():
    logger.info("Starting lead generation cycle...")
    
    all_raw_leads = []
    
    # 1. Scrape
    try:
        fb_leads = scrape_facebook_public()
        all_raw_leads.extend(fb_leads)
    except Exception as e:
        logger.error(f"FB scraping failed: {e}")

    try:
        bark_leads = scrape_bark_listings()
        all_raw_leads.extend(bark_leads)
    except Exception as e:
        logger.error(f"Bark scraping failed: {e}")

    logger.info(f"Total raw leads collected: {len(all_raw_leads)}")

    for lead in all_raw_leads:
        url = lead.get('url')
        if url in PROCESSED_URLS and url != "N/A":
            continue
        
        # 2. Local Filter (Calgary/Alberta check before AI)
        # We assume all leads from our specific Calgary Facebook groups are local.
        # Otherwise, strictly enforce that they mention the city.
        source = lead.get('source', '')
        if "Facebook Group" not in source:
            text = lead.get('text', '').lower()
            if "calgary" not in text and "alberta" not in text and "yyc" not in text:
                continue

        # 3. Qualify with AI
        logger.info(f"Qualifying lead: {url}")
        qualification = qualify_lead(lead['text'])
        
        if not qualification:
            continue
            
        # 4. Score Filter
        is_qualified = qualification.get('is_moving_lead', False)
        
        if is_qualified:
            logger.info(f"HOT LEAD FOUND: {lead['url']}")
            
            # 5. Save to Sheets & InsForge Database
            save_to_sheets(lead, qualification)
            save_to_insforge(lead, qualification)
            
            # 6. Notify Telegram
            send_telegram_notification(lead, qualification)
            
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
