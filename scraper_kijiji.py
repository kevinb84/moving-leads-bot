import os
from playwright.sync_api import sync_playwright
import time
import random
from utils.logger import logger
from utils.browser import get_browser_context, human_move

KIJIJI_URLS = [
    "https://www.kijiji.ca/b-calgary/need-movers/k0l1700199?ad=wanted",
    "https://www.kijiji.ca/b-calgary/need-moving/k0l1700199?ad=wanted",
    "https://www.kijiji.ca/b-calgary/junk-removal/k0l1700199?ad=wanted",
    "https://www.kijiji.ca/b-edmonton/need-movers/k0l1700203?ad=wanted",
    "https://www.kijiji.ca/b-edmonton/need-moving/k0l1700203?ad=wanted",
    "https://www.kijiji.ca/b-edmonton/junk-removal/k0l1700203?ad=wanted"
]

def scrape_kijiji():
    leads = []
    
    with sync_playwright() as p:
        is_github = bool(os.getenv("GITHUB_ACTIONS"))
        browser, context = get_browser_context(p, headless=True)
        page = context.new_page()
        
        seen_urls = set()
        for url in KIJIJI_URLS:
            try:
                logger.info(f"Scraping Kijiji: {url}")
                page.goto(url, timeout=30000)
                time.sleep(random.uniform(5, 8))
                human_move(page)
                
                # Dynamic selectors for modern Kijiji React cards
                # They often use data-testid but also various sc- classes
                listings = page.locator('ul[data-testid="listing-list"] li, [class*="sc-ed38c1d6"]').all()
                logger.info(f"Kijiji found {len(listings)} potential listings.")
                
                for listing in listings:
                    try:
                        # Find link and title
                        # Most often the card itself is an <a> or has one
                        if listing.get_attribute('href'):
                            title = listing.inner_text().strip()
                            link = listing.get_attribute('href')
                        else:
                            link_elem = listing.locator('a').first
                            if link_elem.count() > 0:
                                title = link_elem.inner_text().strip()
                                link = link_elem.get_attribute('href')
                            else:
                                continue
                                
                        if not link: continue
                        if not link.startswith("http"):
                            link = "https://www.kijiji.ca" + link
                            
                        clean_url = link.split('?')[0]
                        if clean_url in seen_urls:
                            continue
                            
                        lower_title = title.lower()
                        # Keywords to find true "Wanted" ads
                        keywords = ["need", "looking", "moving", "junk", "removal", "hauling", "disposal", "help", "required", "seeking"]
                        disqualifiers = ["$", "/hr", "insured", "bonded", "movers available", "moving services"]
                        
                        if any(kw in lower_title for kw in keywords):
                            if not any(dkw in lower_title for dkw in disqualifiers):
                                leads.append({
                                    "text": title,
                                    "url": clean_url,
                                    "source": "Kijiji",
                                    "status": "New"
                                })
                                seen_urls.add(clean_url)
                    except Exception:
                        continue
            except Exception as e:
                logger.error(f"Error scraping Kijiji {url}: {e}")
                
        browser.close()
        
    return leads

if __name__ == "__main__":
    import os
    res = scrape_kijiji()
    print(f"Kijiji leads found: {len(res)}")
    for r in res[:10]:
        print(f"[{r['source']}] {r['text'][:100]} - {r['url']}")
