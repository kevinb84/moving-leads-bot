from playwright.sync_api import sync_playwright
import os
import time

def nextdoor_login():
    """
    Opens Nextdoor so you can log in manually. 
    It then saves your combined session (Facebook + Nextdoor) so the scraper can run autonomously.
    """
    print("=== Nextdoor Login Helper ===")
    print("Opening browser. Please log in to Nextdoor manually.")
    print("Once you are fully logged in and can see your neighborhood feed, close the browser.")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        
        context_args = {}
        if os.path.exists("cookies.json"):
            # Load existing Facebook cookies so they aren't erased
            context_args["storage_state"] = "cookies.json"
            
        context = browser.new_context(**context_args)
        page = context.new_page()
        
        try:
            page.goto("https://ca.nextdoor.com/login/")
            print("Browser opened. Waiting for you to log in and close the window...")
            
            # Wait until the user closes the page/browser
            page.wait_for_event("close", timeout=0)  # Wait indefinitely until closed
            
        except Exception as e:
            # If the user closed the browser, playwright throws TargetClosedError
            print("Browser closed by user.")
            
        # Save combined storage state back to cookies.json
        context.storage_state(path="cookies.json")
        print("Successfully saved Nextdoor session cookies!")

if __name__ == "__main__":
    nextdoor_login()
