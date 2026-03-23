from playwright.sync_api import sync_playwright
import time
from scraper_facebook import FB_GROUPS

def run_facebook_join_helper():
    print("=== Facebook Group Join Helper ===")
    print("This will open a browser and cycle through all your groups.")
    print("If you are not a member of a group, click 'Join Group'.")
    print("Press Enter in this console when you are ready to move to the next group!")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(storage_state="cookies.json")
        page = context.new_page()
        
        for url in FB_GROUPS:
            print(f"\nNavigating to {url}...")
            try:
                page.goto(url)
                # We simply pause and wait for the user to hit Enter in the terminal
                input("👉 Press ENTER here in the terminal when you're done with this group...")
            except Exception as e:
                print(f"Error loading {url}: {e}")
                
        print("\n✅ All finished! Updating your cookies just in case...")
        context.storage_state(path="cookies.json")
        browser.close()

if __name__ == "__main__":
    run_facebook_join_helper()
