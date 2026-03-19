from playwright.sync_api import sync_playwright
import time
import os

def login_to_facebook():
    print("Opening browser for Facebook Login...")
    print("Please log into Facebook, and handle any 2FA/Approvals.")
    print("The browser will automatically close and save your session once you are logged in.")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        page.goto("https://www.facebook.com/")
        
        # Wait up to 5 minutes for the user to login. 
        # We assume login is successful if we see the marketplace icon, friends tab, or the home feed.
        try:
            page.wait_for_selector('a[aria-label="Home"], a[href="/marketplace/"]', timeout=300000)
            print("\nSuccessfully detected login! Saving session to cookies.json...")
            
            # Save the cookies to cookies.json
            context.storage_state(path="cookies.json")
            print("Session saved! You can now close this window and run your scraper.")
            
        except Exception as e:
            print("\nTimeout or error waiting for login. If you did login, it just couldn't detect the home screen.")
            print(f"Error: {e}")
            
        browser.close()

if __name__ == "__main__":
    login_to_facebook()
