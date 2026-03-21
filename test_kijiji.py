import sys
from scraper_kijiji import scrape_kijiji
from scraper_craigslist import scrape_craigslist
from qualifier import qualify_lead
from insforge_db import save_to_insforge
from utils.logger import logger

def test_fast_scrapers():
    logger.info("Running fast scrapers (Kijiji & Craigslist) to test pipeline now...")
    all_raw_leads = []
    
    try:
        all_raw_leads.extend(scrape_kijiji())
    except Exception as e:
        logger.error(f"Kijiji: {e}")
        
    try:
        all_raw_leads.extend(scrape_craigslist())
    except Exception as e:
        logger.error(f"Craigslist: {e}")

    logger.info(f"Raw leads found: {len(all_raw_leads)}")
    qualified_count = 0

    for lead in all_raw_leads:
        qualification = qualify_lead(lead['text'])
        if qualification and qualification.get('is_moving_lead', False):
            logger.info(f"HOT LEAD: {lead['url']}")
            # Force save to InsForge
            saved = save_to_insforge(lead, qualification)
            if saved:
                qualified_count += 1

    logger.info(f"Test complete. Successfully saved {qualified_count} new leads to InsForge.")

if __name__ == '__main__':
    test_fast_scrapers()
