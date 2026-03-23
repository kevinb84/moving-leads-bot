from playwright.sync_api import sync_playwright
import os

def ig_login():
    """
    Opens Instagram so you can log in manually. 
    It saves your Instagram session identically to Nextdoor and Facebook so the marketing bot can post for you.
    """
    print("=== Instagram Login Helper ===")
    print("Opening browser. Please log in to Instagram manually.")
    print("Once you are fully logged in and can see your feed, close the browser.")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        context_args = {}
        if os.path.exists("cookies.json"):
            # Load existing Facebook + Nextdoor cookies so they aren't erased
            context_args["storage_state"] = "cookies.json"
            
        context = browser.new_context(**context_args)
        page = context.new_page()
        
        try:
            page.goto("https://www.instagram.com/accounts/login/")
            print("Browser opened. Waiting for you to log in and close the window...")
            
            # Wait indefinitely until closed
            page.wait_for_event("close", timeout=0)  
            
        except Exception as e:
            print("Browser closed by user.")
            
        # Save combined storage state back to cookies.json
        context.storage_state(path="cookies.json")
        print("Successfully saved your Instagram session cookies!")

if __name__ == "__main__":
    ig_login()
