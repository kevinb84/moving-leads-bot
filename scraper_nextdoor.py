from playwright.sync_api import sync_playwright
import time
from utils.logger import logger
from utils.browser import get_browser_context, random_delay, human_move

NEXTDOOR_SEARCH_URLS = [
    "https://ca.nextdoor.com/search/?query=movers",
    "https://ca.nextdoor.com/search/?query=moving%20company",
    "https://ca.nextdoor.com/search/?query=recommend%20movers"
]

def scrape_nextdoor():
    """
    Scrapes Nextdoor neighborhood feeds for people asking for movers.
    Requires an active nextdoor session in cookies.json via nextdoor_login.py.
    """
    leads = []
    
    with sync_playwright() as p:
        browser, context = get_browser_context(p, headless=True)
        page = context.new_page()
        
        for url in NEXTDOOR_SEARCH_URLS:
            try:
                logger.info(f"Scraping Nextdoor: {url}")
                page.goto(url)
                random_delay(3, 6)
                human_move(page)
                
                # Check if logged out by redirect to login
                if "login" in page.url:
                    logger.warning("Nextdoor session expired. Please run nextdoor_login.py to update cookies.")
                    return leads
                    
                # Scroll to load posts
                for _ in range(3):
                    page.mouse.wheel(0, 1000)
                    time.sleep(2)
                    
                # The DOM for nextdoor posts varies, typically they use roles or generic div classes for the timeline
                posts = page.query_selector_all('article, div[data-testid="post-content"]')
                
                logger.info(f"Nextdoor found {len(posts)} potential posts.")
                
                for post in posts:
                    try:
                        text_content = post.inner_text().strip()
                        if not text_content:
                            continue
                            
                        # Quick filter: ignore very short text or business ads
                        lower_text = text_content.lower()
                        if "sponsored" in lower_text or "promoted" in lower_text:
                            continue
                            
                        # Extract the unique URL for this specific post if possible
                        post_url_elem = post.query_selector('a[href*="/post/"], a[href*="/p/"]')
                        post_url = post_url_elem.get_attribute('href') if post_url_elem else url
                        
                        if post_url.startswith('/'):
                            post_url = f"https://ca.nextdoor.com{post_url}"
                            
                        # Basic pre-filter: text must contain moving-related keywords seeking help
                        if any(kw in lower_text for kw in ["recommend", "looking for", "need", "best", "help"]):
                            # Make sure it actually mentions moving
                            if any(kw in lower_text for kw in ["mover", "moving", "truck"]):
                                leads.append({
                                    "text": text_content,
                                    "url": post_url.split('?')[0],
                                    "source": "Nextdoor",
                                    "status": "New"
                                })
                    except Exception as e:
                        continue
                        
            except Exception as e:
                logger.error(f"Error scraping Nextdoor URL '{url}': {e}")
                
        browser.close()
        
    return leads

if __name__ == "__main__":
    results = scrape_nextdoor()
    print(f"Total Nextdoor leads found: {len(results)}")
    for r in results[:5]:
        print(r['text'][:50], "-", r['url'])
