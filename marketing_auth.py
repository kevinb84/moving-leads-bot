from playwright.sync_api import sync_playwright
import os

def run_marketing_auth():
    """
    Opens Facebook and Instagram sequentially so you can log into your OFFICIAL accounts.
    It saves this session completely isolated in 'cookies_marketing.json', so it never overlaps
    with your scraper's burner account in 'cookies.json'.
    """
    print("=== Official Marketing Authenticator ===")
    print("This will create a dedicated cookie file strictly for Auto-Posting.")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        context_args = {}
        if os.path.exists("cookies_marketing.json"):
            context_args["storage_state"] = "cookies_marketing.json"
            
        context = browser.new_context(**context_args)
        page = context.new_page()
        
        try:
            print("\n👉 Opening Facebook...")
            print("Please log into your official account that owns the Quick Movers Page.")
            print("Close the browser tab/window when you are fully logged in.")
            page.goto("https://www.facebook.com/")
            page.wait_for_event("close", timeout=0)  
        except Exception as e:
            pass
            
        # Reopen a new page for Instagram because the context is still alive
        try:
            page = context.new_page()
            print("\n👉 Opening Instagram...")
            print("Please log into your official @quickmoverssolution account.")
            print("Close the browser tab/window when you are fully logged in.")
            page.goto("https://www.instagram.com/accounts/login/")
            page.wait_for_event("close", timeout=0)
        except Exception:
            pass
            
        # Save exclusive marketing cookies
        context.storage_state(path="cookies_marketing.json")
        browser.close()
        print("\n✅ Successfully generated 'cookies_marketing.json'!")

if __name__ == "__main__":
    run_marketing_auth()
