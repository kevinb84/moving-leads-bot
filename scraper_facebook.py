from playwright.sync_api import sync_playwright
from utils.browser import get_browser_context, random_delay, human_move
from utils.logger import logger
from qualifier import qualify_lead
import random
import time

FB_GROUPS = [
    "https://www.facebook.com/groups/calgaryrentals",
    "https://www.facebook.com/groups/948892938621031/",
    "https://www.facebook.com/groups/152728695501487/",
    "https://www.facebook.com/groups/5131221633668517/",
    "https://www.facebook.com/groups/671775454638768/",
    "https://www.facebook.com/groups/1035444075121936/",
    "https://www.facebook.com/groups/197451927372346/",
    "https://www.facebook.com/groups/985229415745481/",
    "https://www.facebook.com/groups/732936102383065/",
    "https://www.facebook.com/groups/291741052177433/",
    "https://www.facebook.com/groups/894044065936686/",
    "https://www.facebook.com/groups/housesforrentcalgary/",
    "https://www.facebook.com/groups/750751069727344/",
    "https://www.facebook.com/groups/1404326543630054/",
    "https://www.facebook.com/groups/482368585643644/",
    # --- NEW EDMONTON & CALGARY GROUPS ---
    "https://www.facebook.com/groups/edmontonbuyandsell/",
    "https://www.facebook.com/groups/EdmontonBuySellTrade/",
    "https://www.facebook.com/groups/edmontonrentals/",
    "https://www.facebook.com/groups/yegbuyandsell/",
    "https://www.facebook.com/groups/edmontoncommunity/",
    "https://www.facebook.com/groups/yegclassified/",
    "https://www.facebook.com/groups/yegrentals/",
    "https://www.facebook.com/groups/Edmontonclassifieds/",
    "https://www.facebook.com/groups/edmontonapartments/",
    "https://www.facebook.com/groups/CalgaryHomesForRent/",
    "https://www.facebook.com/groups/calgarycommunity/"
]

def scrape_facebook_public():
    """
    Scrapes specific Facebook groups for moving leads in Calgary.
    Requires a valid cookies.json to bypass login screens.
    """
    leads = []
    
    with sync_playwright() as p:
        browser, context = get_browser_context(p, headless=True)
        page = context.new_page()
        
        for group_url in FB_GROUPS:
            try:
                # Force chronological sorting so we get recent leads, not ancient popular posts
                if "?" in group_url:
                    url = group_url + "&sorting_setting=CHRONOLOGICAL"
                else:
                    base_url = group_url
                    if base_url.endswith('/'):
                        base_url = base_url[:-1]
                    url = base_url + "/?sorting_setting=CHRONOLOGICAL"
                    
                logger.info(f"Scraping Facebook Group: {group_url}")
                
                page.goto(url)
                random_delay(5, 10)
                human_move(page)
                
                # Check if logged out (Facebook login wall)
                is_logged_out = False
                if "login" in page.url:
                    is_logged_out = True
                elif page.locator('input[name="email"], input[name="pass"], button[name="login"]').count() > 0:
                    is_logged_out = True
                elif page.locator('a:has-text("Log in"), button:has-text("Log in")').count() > 0 and page.locator('aria-label="Home"]').count() == 0:
                    is_logged_out = True
                
                if is_logged_out:
                    logger.warning("Facebook session expired or unauthenticated. Please run fb_login.py to update cookies.")
                    return leads
                
                # Scroll a bit to load more group posts
                for _ in range(4):
                    page.mouse.wheel(0, 1500)
                    time.sleep(random.uniform(2, 4))
                
                # Take a debug screenshot to verify what's on the screen
                slug = group_url.split('/')[-1] if not group_url.endswith('/') else group_url.split('/')[-2]
                screenshot_filename = f"logs/facebook_debug_group_{slug}.png"
                page.screenshot(path=screenshot_filename)
                logger.info(f"Saved Facebook debug screenshot to {screenshot_filename}")

                # Identify post containers in Groups using role="article"
                posts = page.query_selector_all('div[role="article"]')
                logger.info(f"Found {len(posts)} potential posts in group {slug}")
                
                for post in posts:
                    try:
                        text_content = post.inner_text().strip()
                        if not text_content:
                            continue
                            
                        # Extract the unique URL for this specific post if possible
                        post_url_elem = post.query_selector('a[href*="/posts/"], a[href*="/permalink/"]')
                        post_url = post_url_elem.get_attribute('href') if post_url_elem else group_url
                        
                        if post_url.startswith('/'):
                            post_url = f"https://www.facebook.com{post_url}"
                            
                        # Basic pre-filter: text must contain moving-related keywords
                        lower_text = text_content.lower()
                        keywords = ["mover", "moving", "truck", "load", "pack", "recommendation", "relocating", "u-haul", "boxes", "unloading"]
                        if any(kw in lower_text for kw in keywords):
                            leads.append({
                                "text": text_content,
                                "url": post_url.split('?')[0], # Strip tracking parameters
                                "source": f"Facebook Group: {slug}",
                                "group_url": group_url
                            })
                    except Exception as e:
                        continue
                        
            except Exception as e:
                logger.error(f"Error scraping FB group '{group_url}': {e}")
                continue
                
        browser.close()
    
    return leads

if __name__ == "__main__":
    import time
    results = scrape_facebook_public()
    print(f"Total leads found: {len(results)}")
