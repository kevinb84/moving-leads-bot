from qualifier import qualify_lead
from telegram_notifier import send_telegram_notification
# from sheets_handler import save_to_sheets # Skip if no credentials.json
import json

def dry_test():
    sample_posts = [
        {
            "text": "Hey YYC! I'm looking for a reliable moving company. Moving from a 3-bedroom house in Auburn Bay to Airdrie on July 20. Need full packing services too. Any recommendations? Please text me at 403-555-9000.",
            "url": "https://facebook.com/groups/calgarymoves/posts/12345",
            "source": "Facebook - Calgary Moving Help",
            "status": "New"
        },
        {
            "text": "I have an old couch to give away in SE Calgary. Pick up only. Not looking for movers, just someone to take it.",
            "url": "https://facebook.com/groups/calgaryfree/posts/67890",
            "source": "Facebook - Free Stuff YYC",
            "status": "New"
        }
    ]

    print("=== Starting Dry Test ===")
    for post in sample_posts:
        print(f"\nProcessing Post: {post['url']}")
        qualification = qualify_lead(post['text'])
        
        if qualification:
            print(json.dumps(qualification, indent=2))
            
            if qualification.get('is_moving_lead'):
                print(">>> SUCCESS: Hot lead detected. Sending notification (simulated if no keys).")
                # send_telegram_notification(post, qualification)
            else:
                print(">>> IGNORED: Not a hot lead.")
        else:
            print(">>> ERROR: Qualification failed.")

if __name__ == "__main__":
    dry_test()
