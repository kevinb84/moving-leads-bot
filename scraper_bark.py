from playwright.sync_api import sync_playwright
from utils.browser import get_browser_context, random_delay, human_move, wait_for_selector_safe
from utils.logger import logger
import random
import time

BARK_URLS = [
    "https://www.bark.com/en/ca/house-removals/",
    "https://www.bark.com/en/ca/office-removals/",
    "https://www.bark.com/en/ca/man-and-van/"
]

def scrape_bark_listings():
    """
    Scrapes Bark.com for public moving requests in Canada.
    """
    leads = []
    
    with sync_playwright() as p:
        browser, context = get_browser_context(p, headless=True)
        page = context.new_page()
        
        for url in BARK_URLS:
            try:
                logger.info(f"Scraping Bark category: {url}")
                page.goto(url)
                random_delay(5, 12)
                human_move(page)
                
                # Bark often lists jobs in a list or grid
                # CSS Selectors for Bark leads (based on common patterns)
                # Note: Bark usually requires login to see full details, 
                # but sometimes previews are visible or we can find 'browse jobs' pages.
                
                # Take a debug screenshot to verify what's on the screen
                slug = url.split('/')[-2] if url.endswith('/') else url.split('/')[-1]
                screenshot_filename = f"logs/bark_debug_{slug}.png"
                page.screenshot(path=screenshot_filename)
                logger.info(f"Saved Bark debug screenshot to {screenshot_filename}")

                # Check for job cards
                # Bark leads often have classes like 'public-lead-card' or similar in browse mode
                # Let's try to find potential card elements
                job_cards = page.query_selector_all('.job-card, .public-lead, a[href*="/projects/"]')
                
                if not job_cards:
                    # Try another approach: search for text snippets
                    logger.info("No direct job cards found, looking for alternative structures.")
                
                for card in job_cards:
                    try:
                        text = card.inner_text().strip()
                        link = card.get_attribute('href')
                        if link and not link.startswith('http'):
                            link = f"https://www.bark.com{link}"
                            
                        if text:
                            leads.append({
                                "text": text,
                                "url": link or url,
                                "source": "Bark.com",
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
