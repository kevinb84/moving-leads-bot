from playwright.sync_api import sync_playwright
import time
import random
from utils.browser import get_browser_context, human_move
from utils.logger import logger

def auto_comment_facebook(post_url, comment_text):
    """
    Safely navigates to a Facebook post URL and adds a Smart Comment using Playwright.
    """
    logger.info(f"Attempting to smart-comment on: {post_url}")
    
    with sync_playwright() as p:
        # We run this headless=False for testing so you can visually confirm it works!
        browser, context = get_browser_context(p, headless=False)
        page = context.new_page()
        
        try:
            page.goto(post_url)
            time.sleep(random.uniform(3, 5))
            
            # Find the comment input box. Facebook uses various aria-labels for this.
            comment_box = page.locator('div[role="textbox"][aria-label*="Write a comment"], div[role="textbox"][aria-label*="Write a public comment"]')
            
            if comment_box.count() == 0:
                logger.error("Could not find the Facebook comment box. The post might be locked, or the UI changed.")
                browser.close()
                return False
                
            # Click and type human-like
            comment_box.first.click()
            human_move(page)
            time.sleep(random.uniform(1, 2))
            
            logger.info("Typing the AI comment...")
            # Type the comment slowly
            for char in comment_text:
                page.keyboard.press(char)
                time.sleep(random.uniform(0.01, 0.05))
                
            time.sleep(random.uniform(1, 2))
            
            # Hit Enter to submit
            page.keyboard.press("Enter")
            logger.info("Comment successfully submitted to Facebook!")
            
            # Wait a few seconds to let the network request finish before closing
            time.sleep(5)
            
            browser.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to post comment on Facebook: {e}")
            browser.close()
            return False

if __name__ == "__main__":
    # DO NOT RUN THIS TEST UNLESS YOU WANT TO ACTUALLY LEAVE A COMMENT ON YOUR OWN FACEBOOK!
    # test_url = "https://www.facebook.com/..." 
    # test_text = "Hey! Local Calgary movers here, we have a truck available and would love to help. I sent you a DM!"
    # auto_comment_facebook(test_url, test_text)
    print("comment_facebook.py initialized and ready to be connected to the Dashboard!")
