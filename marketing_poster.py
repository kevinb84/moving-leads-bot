from playwright.sync_api import sync_playwright
import time
import random
import os
from utils.browser import get_browser_context, human_move
from utils.logger import logger

FB_PAGE_URL = "https://www.facebook.com/quickmovesolutions"
IG_PAGE_URL = "https://www.instagram.com/quickmoverssolution/"

def auto_post_facebook_page(post_text, image_path=None):
    """
    Automates posting to the Official Facebook Page using Playwright.
    Make sure you are logged in and have switched to the Page Profile before running headless.
    """
    logger.info("Attempting to post to Facebook Page...")
    
    with sync_playwright() as p:
        browser, context = get_browser_context(p, headless=False, cookies_file="cookies_marketing.json")
        page = context.new_page()
        
        try:
            page.goto(FB_PAGE_URL)
            # Wait up to 15 seconds for Facebook's heavy single page app loading screen to finish
            try: page.wait_for_load_state("networkidle", timeout=15000)
            except: pass
            
            # Automatically click "Switch" or "Switch Now" if the Page banner is prompting us
            try:
                # First, target the big blue "Switch Now" banner explicitly
                switch_btn = page.get_by_text("Switch Now", exact=True).first
                if not switch_btn.is_visible(timeout=2000):
                    switch_btn = page.locator('div[role="button"]:has-text("Switch")').first
                    
                if switch_btn.is_visible(timeout=2000):
                    logger.info("Facebook is prompting us to switch profiles. Clicking 'Switch'...")
                    switch_btn.click(force=True)
                    
                    time.sleep(2) # Give the modal 2 full seconds to animate onto the screen
                    
                    # Brute force the 2-step Profile Switch Confirmation Modal blue button!
                    try:
                        clicked_modal = False
                        for btn in page.get_by_text("Switch", exact=True).all():
                            if btn.is_visible():
                                logger.info("Confirming the Switch Profile modal...")
                                btn.click(force=True, timeout=1000)
                                clicked_modal = True
                        if not clicked_modal:
                            # Fallback if "Switch" text is inside another tag
                            for btn in page.locator('div[aria-label="Switch profiles"] div[role="button"], div[role="dialog"] div[role="button"]').all():
                                if btn.is_visible() and "Switch" in btn.inner_text():
                                    logger.info("Fallback: Confirming Switch Profile modal...")
                                    btn.click(force=True, timeout=1000)
                    except Exception:
                        pass
                        
                    try:
                        page.wait_for_load_state("networkidle", timeout=10000)
                    except Exception:
                        pass
                    
                    time.sleep(random.uniform(5, 7)) # Wait for context to reload
            except Exception:
                pass
                
            # Clear any annoying "Next" or "Done" onboarding prompts that Facebook shows when you switch profiles
            try:
                for btn_text in ["Next", "Done", "Not Now", "Close"]:
                    annoying_btn = page.get_by_text(btn_text, exact=True).last
                    if annoying_btn.is_visible(timeout=1000):
                        annoying_btn.click(force=True)
                        time.sleep(1)
            except Exception:
                pass
                
            # Click "Write something..." or "Create Post" or "What's on your mind"
            post_box = None
            try:
                # Get the element exactly containing this text
                box_1 = page.get_by_text("What's on your mind?").last
                if box_1.is_visible(timeout=5000):
                    post_box = box_1
                else:
                    box_2 = page.get_by_text("Write something...").last
                    if box_2.is_visible(timeout=2000):
                        post_box = box_2
                    else:
                        box_3 = page.locator('div[aria-label="Create a post"]').first
                        if box_3.is_visible(timeout=2000):
                            post_box = box_3
            except Exception:
                pass
            
            if not post_box:
                logger.error("Could not find the 'Create Post' box. Taking screenshot for debugging...")
                try: page.screenshot(path="fb_error_debug.png")
                except: pass
                logger.error("Screenshot saved to fb_error_debug.png.")
                browser.close()
                return False
                
            logger.info("Focussing on POST box...")
            post_box.click(force=True)
            time.sleep(random.uniform(3, 4))
            
            # Type the text into the modal
            modal_textbox = None
            try:
                txt_1 = page.locator('div[role="dialog"] div[role="textbox"]').first
                if txt_1.is_visible(timeout=3000):
                    modal_textbox = txt_1
                else:
                    txt_2 = page.locator('div[aria-label*="What\'s on your mind"]').last
                    if txt_2.is_visible(timeout=3000):
                        modal_textbox = txt_2
            except Exception:
                pass
                
            if modal_textbox:
                modal_textbox.click(force=True)
            else:
                logger.warning("Could not clearly identify modal text box. Blind typing fallback triggered.")
            
            time.sleep(1)
            
            logger.info("Typing marketing post...")
            for char in post_text:
                page.keyboard.press(char)
                time.sleep(random.uniform(0.01, 0.03))
                
            # If there's an image, upload it
            if image_path and os.path.exists(image_path):
                logger.info("Uploading image attached to post...")
                # Find the Photo/Video button
                photo_button = page.locator('div[aria-label="Photo/video"]')
                if photo_button.count() > 0:
                    with page.expect_file_chooser() as fc_info:
                        photo_button.first.click()
                    file_chooser = fc_info.value
                    file_chooser.set_files(image_path)
                    time.sleep(random.uniform(3, 5))
            
            time.sleep(2)
            
            # Click "Next" if Facebook uses a 2-step composer (like for Pages linked to IG)
            try:
                clicked_next = False
                for btn in page.get_by_text("Next", exact=True).all():
                    if btn.is_visible():
                        logger.info("Composer requires 'Next' step. Clicking exact text 'Next'...")
                        btn.click(force=True, timeout=1000)
                        time.sleep(2)
                        clicked_next = True
                if not clicked_next:
                    for btn in page.locator('div[role="button"]:has-text("Next")').all():
                        if btn.is_visible():
                            btn.click(force=True, timeout=1000)
                            time.sleep(2)
            except Exception:
                pass
            
            # Click "Post" or "Publish" or "Share"
            submit_btn = None
            try:
                for target_text in ["Post", "Publish", "Share"]:
                    for btn in page.get_by_text(target_text, exact=True).all():
                        if btn.is_visible():
                            submit_btn = btn
                            break
                    if submit_btn: break
                    
                if not submit_btn:
                    # Fallback locator
                    for target_text in ["Post", "Publish", "Share"]:
                        for btn in page.locator(f'div[role="button"]:has-text("{target_text}")').all():
                            if btn.is_visible():
                                submit_btn = btn
                                break
                        if submit_btn: break
            except Exception:
                pass
                
            if submit_btn:
                submit_btn.click(force=True)
                logger.info("Successfully published post to Facebook Page!")
                
                time.sleep(3)
                # Clear optional "Add WhatsApp" upsell modals
                try:
                    for skip_text in ["Not now", "Not Now", "Close"]:
                        for btn in page.get_by_text(skip_text, exact=True).all():
                            if btn.is_visible():
                                btn.click(force=True, timeout=1000)
                except:
                    pass
                
            else:
                try: page.screenshot(path="fb_error_debug.png")
                except: pass
                logger.error("Could not find the 'Post' button. Extracted screenshot. Aborting post.")
                browser.close()
                return False
                
            time.sleep(5)
            # Retain the context so Facebook remembers we are now acting as the Page Profile!
            context.storage_state(path="cookies_marketing.json")
            browser.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to auto-post to Facebook Page: {e}")
            browser.close()
            return False

def auto_post_instagram_page(post_text, image_path):
    """
    Automates posting to Instagram using Playwright.
    Instagram requires an image for all posts.
    """
    logger.info("Attempting to post to Instagram...")
    if not image_path or not os.path.exists(image_path):
        logger.error("Instagram requires an image. Post cancelled.")
        return False
        
    with sync_playwright() as p:
        browser, context = get_browser_context(p, headless=False, cookies_file="cookies_marketing.json")
        page = context.new_page()
        
        try:
            # Instagram requires logged-in session!
            # If cookies_marketing.json doesn't have IG cookies, we will need to login manually the first time.
            page.goto("https://www.instagram.com/")
            time.sleep(random.uniform(5, 8))
            
            # Click the "Create" (+) button in the sidebar
            create_btn = page.locator('svg[aria-label="New post"]')
            if create_btn.count() == 0:
                logger.error("Could not find IG Create button. Ensure cookies_marketing.json has your Instagram login!")
                browser.close()
                return False
                
            # Upload the image directly via the file chooser
            logger.info("Uploading image to Instagram...")
            with page.expect_file_chooser() as fc_info:
                page.locator('a[href="#"], div[role="button"]:has(svg[aria-label="New post"])').first.click()
            
            file_chooser = fc_info.value
            file_chooser.set_files(image_path)
            time.sleep(random.uniform(3, 4))
            
            # Click 'Next' twice to bypass filters/crop
            page.locator('div[role="button"]:has-text("Next")').first.click()
            time.sleep(2)
            page.locator('div[role="button"]:has-text("Next")').first.click()
            time.sleep(2)
            
            # Type caption
            caption_box = page.locator('div[aria-label="Write a caption..."]')
            caption_box.first.click()
            for char in post_text:
                page.keyboard.press(char)
                time.sleep(random.uniform(0.01, 0.03))
                
            time.sleep(2)
            
            # Click 'Share'
            page.locator('div[role="button"]:has-text("Share")').first.click()
            logger.info("Successfully published post to Instagram!")
            time.sleep(8)
            
            # Save cookies in case IG session updated
            context.storage_state(path="cookies_marketing.json")
            browser.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to auto-post to Instagram: {e}")
            browser.close()
            return False

if __name__ == "__main__":
    print("marketing_poster.py initialized. These functions can be tied to your custom AI Ad Dashboard.")
    # Example Usage:
    # auto_post_facebook_page("Looking for Calgary Movers? We're available this weekend! DM us.")
    # auto_post_instagram_page("Looking for Edmonton Movers? Available now!", "promo_flyer.jpg")
