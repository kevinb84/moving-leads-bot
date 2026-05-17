from playwright.sync_api import sync_playwright
import time
from utils.logger import logger
from utils.browser import get_browser_context, random_delay, human_move

NEXTDOOR_SEARCH_URLS = [
    "https://ca.nextdoor.com/search/posts/?query=movers",
    "https://ca.nextdoor.com/search/posts/?query=moving%20help",
    "https://ca.nextdoor.com/search/posts/?query=help%20moving",
    "https://ca.nextdoor.com/search/posts/?query=moving%20company",
    "https://ca.nextdoor.com/search/posts/?query=recommend%20movers",
    "https://ca.nextdoor.com/search/posts/?query=junk%20removal",
    "https://ca.nextdoor.com/search/posts/?query=garbage%20hauling"
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
                random_delay(5, 10) # More time to load
                human_move(page)
                
                # Check if logged out (Nextdoor soft login wall)
                is_logged_out = False
                if "login" in page.url:
                    is_logged_out = True
                elif page.locator('a:has-text("Log in"), button:has-text("Log in"), a[href*="/login/"]').count() > 0:
                    is_logged_out = True
                elif page.locator('text="Hear from locals on Nextdoor"').count() > 0:
                    is_logged_out = True
                
                if is_logged_out:
                    logger.warning("Nextdoor session expired or unauthenticated. Please run nextdoor_login.py to update cookies.")
                    return leads
                    
                # Take debug screenshot
                slug = url.split('=')[-1].replace('%20', '_')
                screenshot_path = f"logs/nextdoor_debug_{slug}.png"
                page.screenshot(path=screenshot_path)
                logger.info(f"Saved Nextdoor debug screenshot to {screenshot_path}")

                # Scroll to load posts
                for _ in range(3):
                    page.mouse.wheel(0, 1000)
                    time.sleep(2)
                
                page.wait_for_load_state('domcontentloaded')
                time.sleep(2) # Extra buffer
                    
                # Broadened selectors to catch more post types (including searchFeedItem container)
                posts = page.query_selector_all(
                    'article, div[role="article"], [data-testid*="searchFeedItem"], [data-testid*="post"]'
                )
                
                logger.info(
                    f"Nextdoor found {len(posts)} posts for query: {slug}"
                )
                
                for post in posts:
                    try:
                        text_content = post.inner_text().strip()
                        if not text_content:
                            continue
                            
                        # Quick filter: ignore very short text or business ads
                        lower_text = text_content.lower()
                        if "sponsored" in lower_text or "promoted" in lower_text:
                            continue
                            
                        # Extract the unique URL for this specific post
                        post_url_elem = post.query_selector(
                            'a[href*="/post/"], a[href*="/p/"]'
                        )
                        post_url = post_url_elem.get_attribute('href') \
                            if post_url_elem else url
                        
                        if post_url.startswith('/'):
                            post_url = f"https://ca.nextdoor.com{post_url}"
                            
                        # Filter: text must contain keywords seeking help
                        help_kws = [
                            "recommend", "looking for", "need", "best", "help", "hire"
                        ]
                        move_kws = [
                            "mover", "moving", "truck", "junk", "removal",
                            "hauling", "disposal", "cleanout", "clean", "haul"
                        ]
                        
                        if any(kw in lower_text for kw in help_kws):
                            if any(kw in lower_text for kw in move_kws):
                                leads.append({
                                    "text": text_content,
                                    "url": post_url.split('?')[0],
                                    "source": "Nextdoor",
                                    "status": "New"
                                })
                    except Exception:
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
