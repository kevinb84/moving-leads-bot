from playwright.sync_api import sync_playwright
from utils.browser import get_browser_context, random_delay, human_move, wait_for_selector_safe
from utils.logger import logger
import random
import time
import os
import json

BARK_URLS = [
    "https://www.bark.com/en/ca/house-removals/",
    "https://www.bark.com/en/ca/office-removals/",
    "https://www.bark.com/en/ca/man-and-van/",
    "https://www.bark.com/en/ca/long-distance-moving/",
    "https://www.bark.com/en/ca/piano-moving/",
    "https://www.bark.com/en/ca/senior-relocation/",
    "https://www.bark.com/en/ca/junk-removal/",
    "https://www.bark.com/en/ca/house-clearance/",
    "https://www.bark.com/en/ca/office-clearance/"
]

def scrape_bark_listings():
    """
    Scrapes Bark.com for public moving requests in Canada using saved session cookies.
    """
    leads = []
    cookie_path = 'cookies_bark.json'
    
    with sync_playwright() as p:
        browser, context = get_browser_context(p, headless=True)
        
        # Load Bark session if available
        if os.path.exists(cookie_path):
            try:
                with open(cookie_path, 'r') as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
                logger.info("Loaded Bark session cookies.")
            except Exception as e:
                logger.error(f"Error loading Bark cookies: {e}")
        
        page = context.new_page()
        
        for url in BARK_URLS:
            try:
                logger.info(f"Scraping Bark category: {url}")
                page.goto(url)
                random_delay(3, 7)
                
                # Scroll to load more
                for _ in range(3):
                    page.mouse.wheel(0, 1000)
                    time.sleep(2)
                
                # Bark leads often have classes like 'public-lead-card' or 'lead-card'
                job_cards = page.query_selector_all('.lead-card, .public-lead, a[href*="/projects/"]')
                
                logger.info(f"Bark found {len(job_cards)} potential leads on {url}")

                for card in job_cards:
                    try:
                        text = card.inner_text().strip()
                        link = card.get_attribute('href')
                        if link and not link.startswith('http'):
                            link = f"https://www.bark.com{link}"
                            
                        if text:
                            lower_text = text.lower()
                            # Prioritize Calgary/Alberta
                            if any(loc in lower_text for loc in ["calgary", "alberta", "yyc", "airdrie", "okotoks", "edmonton"]):
                                leads.append({
                                    "text": text,
                                    "url": link or url,
                                    "source": "Bark.com (Canada)",
                                    "status": "New"
                                })
                    except:
                        continue
                        
            except Exception as e:
                logger.error(f"Error scraping Bark URL {url}: {e}")
                
        browser.close()
        
    return leads

if __name__ == "__main__":
    results = scrape_bark_listings()
    print(f"Total Bark leads found: {len(results)}")
