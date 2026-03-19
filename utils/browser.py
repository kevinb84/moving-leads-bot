from playwright.sync_api import sync_playwright
import random
import time
import os
from utils.logger import logger
from dotenv import load_dotenv

load_dotenv()

CANADIAN_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]

def get_browser_context(playwright, headless=True):
    """
    Returns a browser and context with stealth and Canadian proxy settings.
    """
    proxy_url = os.getenv("PROXY_SERVER")
    proxy_settings = None
    
    if proxy_url:
        # If it's just the apify_proxy_... password, construct the full URL for Calgary
        if proxy_url.startswith("apify_proxy_") and "://" not in proxy_url:
            username = "groups-RESIDENTIAL,country-CA"
            proxy_url = f"http://{username}:{proxy_url}@proxy.apify.com:8000"
            logger.info("Constructing Apify Residential Proxy (CA targeting) from token.")

        # Check if auth is in the URL: http://user:pass@host:port
        if "@" in proxy_url:
            try:
                protocol_part, auth_part = proxy_url.split("://")
                auth, server = auth_part.split("@")
                username, password = auth.split(":")
                proxy_settings = {
                    "server": f"{protocol_part}://{server}",
                    "username": username,
                    "password": password
                }
            except Exception as e:
                logger.error(f"Error parsing proxy URL: {e}")
                proxy_settings = {"server": proxy_url}
        else:
            proxy_settings = {"server": proxy_url}

    browser_args = [
        "--disable-blink-features=AutomationControlled",
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--window-size=1920,1080"
    ]
    
    browser = playwright.chromium.launch(
        headless=headless,
        args=browser_args,
        proxy=proxy_settings
    )
    
    context_args = {
        "user_agent": random.choice(CANADIAN_USER_AGENTS),
        "viewport": {'width': 1920, 'height': 1080},
        "locale": "en-CA",
        "timezone_id": "America/Edmonton"
    }
    
    if os.path.exists("cookies.json"):
        context_args["storage_state"] = "cookies.json"
        
    context = browser.new_context(**context_args)
    
    return browser, context

def random_delay(min_sec=8, max_sec=45):
    """Adds a human-like delay between 8 and 45 seconds as requested."""
    delay = random.uniform(min_sec, max_sec)
    logger.info(f"Stealth delay: {delay:.2f}s")
    time.sleep(delay)

def human_move(page):
    """Performs small random mouse movements."""
    try:
        x, y = random.randint(100, 800), random.randint(100, 600)
        page.mouse.move(x, y)
        time.sleep(random.uniform(0.1, 0.5))
    except:
        pass

def wait_for_selector_safe(page, selector, timeout=10000):
    try:
        page.wait_for_selector(selector, timeout=timeout)
        return True
    except Exception:
        return False
