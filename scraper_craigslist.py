from playwright.sync_api import sync_playwright
import time
import random
import os
from utils.logger import logger
from utils.browser import get_browser_context, human_move

CRAIGSLIST_URLS = [
    "https://calgary.craigslist.org/search/wan?query=movers",
    "https://calgary.craigslist.org/search/wan?query=moving",
    "https://calgary.craigslist.org/search/wan?query=junk",
    "https://calgary.craigslist.org/search/wan?query=hauling",
    "https://calgary.craigslist.org/search/lbg?query=movers",
    "https://calgary.craigslist.org/search/lbg?query=moving",
    "https://calgary.craigslist.org/search/lbg?query=junk",
    "https://edmonton.craigslist.org/search/wan?query=movers",
    "https://edmonton.craigslist.org/search/lbg?query=movers",
    "https://edmonton.craigslist.org/search/wan?query=junk"
]

def scrape_craigslist():
    leads = []
    
    with sync_playwright() as p:
        is_github = bool(os.getenv("GITHUB_ACTIONS"))
        browser, context = get_browser_context(p, headless=True)
        page = context.new_page()
        
        for url in CRAIGSLIST_URLS:
            try:
                logger.info(f"Scraping Craigslist: {url}")
                page.goto(url, timeout=30000)
                time.sleep(random.uniform(4, 6))
                human_move(page)
                
                # Modern Craigslist uses list items in results-page
                listings = page.locator('li.cl-search-result, a.posting-title').all()
                logger.info(f"Craigslist found {len(listings)} potential listings.")
                
                for listing in listings:
                    try:
                        title = listing.inner_text().strip()
                        link = listing.get_attribute('href')
                        
                        if not link:
                            # Search for <a> inside the li
                            link_elem = listing.locator('a').first
                            if link_elem.count() > 0:
                                title = link_elem.inner_text().strip()
                                link = link_elem.get_attribute('href')
                            else: continue
                            
                        if not link: continue
                        if not link.startswith("http"): continue
                        
                        lower_title = title.lower()
                        # Keywords for people seeking help
                        keywords = ["mover", "moving", "junk", "hauling", "disposal", "truck", "load", "pack", "help", "needed", "wanted"]
                        disqualifiers = ["available", "service", "fully insured", "affordable"]
                        
                        if any(kw in lower_title for kw in keywords):
                            if not any(dkw in lower_title for dkw in disqualifiers):
                                leads.append({
                                    "text": title,
                                    "url": link,
                                    "source": "Craigslist",
                                    "status": "New"
                                })
                    except Exception:
                        continue
                        
            except Exception as e:
                logger.error(f"Failed to scrape Craigslist URL {url}: {e}")
                
        browser.close()
        
    return leads

if __name__ == "__main__":
    res = scrape_craigslist()
    print(f"Craigslist leads found: {len(res)}")
    for r in res[:10]:
        print(f"[{r['source']}] {r['text'][:100]} - {r['url']}")
