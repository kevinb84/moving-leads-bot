import requests
import json
import time
import os
from dotenv import load_dotenv
from utils.logger import logger

from marketing_poster import auto_post_facebook_page, auto_post_instagram_page
from comment_facebook import auto_comment_facebook

load_dotenv(override=True)

# Database Configuration
API_URL = os.getenv("INSFORGE_URL")
API_KEY = os.getenv("INSFORGE_KEY")

if not API_URL or not API_KEY:
    config_path = os.path.join(os.path.dirname(__file__), '.insforge', 'project.json')
    try:
        with open(config_path, 'r') as f:
            insforge_config = json.load(f)
            API_URL = insforge_config.get('oss_host')
            API_KEY = insforge_config.get('api_key')
    except Exception as e:
        logger.error(f"Error reading InsForge config: {e}")

import subprocess
import json
import logging
from sys import executable

def process_marketing_queue():
    """
    Checks the InsForge database via a secure NodeJS Bridge to bypass WAF.
    """
    try:
        bridge_path = os.path.join(os.path.dirname(__file__), 'dashboard', 'worker_bridge.js')
        if not os.path.exists(bridge_path):
            logger.error("NodeJS SDK bridge not found!")
            return
            
        # Fetch pending jobs
        cmd = ['node', bridge_path, 'fetch']
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            logger.error(f"Error executing Node bridge: {result.stderr}")
            return
            
        jobs_json = result.stdout.strip().split('\n')[-1] # Usually output is on the last line
        if not jobs_json or not jobs_json.startswith('['):
            return
            
        jobs = json.loads(jobs_json)
        
        if not jobs:
            return
            
        logger.info(f"Found {len(jobs)} pending marketing jobs!")
        
        for job in jobs:
            job_id = job.get('id')
            content = job.get('raw_text')
            source_url = job.get('source_url', '')
            target_url = job.get('whatsapp_draft')
            image_path = None
            
            success = False
            
            # The CRON backend stores the generated Image URL inside whatsapp_draft when queueing page/insta broadcasts
            if target_url and target_url.startswith('https://') and 'comment' not in source_url:
                try:
                    logger.info(f"Downloading attached media from Brain for job {job_id}...")
                    img_data = requests.get(target_url).content
                    image_path = os.path.join(os.path.dirname(__file__), f"temp_marketing_asset_{job_id}.jpg")
                    with open(image_path, 'wb') as f:
                        f.write(img_data)
                except Exception as e:
                    logger.error(f"Failed to download image from {target_url}: {e}")
            
            if 'facebook_page' in source_url or 'cron_generated' in source_url:
                logger.info(f"Executing Facebook Page Broadcast: {content[:30]}...")
                success = auto_post_facebook_page(content, image_path)
                
            elif 'instagram' in source_url:
                logger.info(f"Executing Instagram Broadcast: {content[:30]}...")
                success = auto_post_instagram_page(content, image_path)
                
            elif 'facebook_comment' in source_url:
                logger.info(f"Deploying Smart Comment to: {target_url}")
                success = auto_comment_facebook(target_url, content)
                
            # Cleanup temp image
            if image_path and os.path.exists(image_path):
                os.remove(image_path)

                
            # Update status in db
            new_status = 'MARKETING_BROADCAST_COMPLETED' if success else 'MARKETING_BROADCAST_FAILED'
            update_cmd = ['node', bridge_path, 'update', str(job_id), new_status]
            subprocess.run(update_cmd, capture_output=True)
            logger.info(f"Job {job_id} marked as {new_status}.")
            
    except Exception as e:
        logger.error(f"Error processing marketing queue: {e}")

if __name__ == "__main__":
    logger.info("=== Marketing Worker Engine Started ===")
    
    if os.getenv("GITHUB_ACTIONS"):
        logger.info("Running in GitHub Actions - processing queue once and exiting.")
        process_marketing_queue()
    else:
        logger.info("Listening for Broadcasts from the Dashboard...")
        while True:
            process_marketing_queue()
            # Check every 10 seconds for instant dashboard responsiveness
            time.sleep(10)
