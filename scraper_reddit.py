import requests
import json
import time
from utils.logger import logger

REDDIT_SEARCH_URLS = [
    # Calgary searches
    "https://www.reddit.com/r/Calgary/search.json?q=movers&restrict_sr=1&sort=new",
    "https://www.reddit.com/r/Calgary/search.json?q=moving+company&restrict_sr=1&sort=new",
    "https://www.reddit.com/r/Calgary/search.json?q=recommend+movers&restrict_sr=1&sort=new",
    
    # Edmonton searches
    "https://www.reddit.com/r/Edmonton/search.json?q=movers&restrict_sr=1&sort=new",
    "https://www.reddit.com/r/Edmonton/search.json?q=moving+company&restrict_sr=1&sort=new",
    "https://www.reddit.com/r/Edmonton/search.json?q=recommend+movers&restrict_sr=1&sort=new"
]

def scrape_reddit():
    leads = []
    
    headers = {
        # Reddit blocks generic requests User-Agents, must be somewhat unique
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 MovingLeadBot/1.0"
    }

    for url in REDDIT_SEARCH_URLS:
        try:
            logger.info(f"Scraping Reddit: {url}")
            response = requests.get(url, headers=headers, timeout=15)
            
            # If rate limited (429), sleep and continue
            if response.status_code == 429:
                logger.warning("Reddit API rate limit hit (429). Sleeping for 5s.")
                time.sleep(5)
                continue
                
            response.raise_for_status()
            data = response.json()
            
            posts = data.get('data', {}).get('children', [])
            logger.info(f"Reddit found {len(posts)} recent related posts.")
            
            for post in posts:
                post_data = post.get('data', {})
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                permalink = post_data.get('permalink', '')
                subreddit = post_data.get('subreddit', 'Unknown')
                created_utc = post_data.get('created_utc', 0)
                
                # Filter out very old posts (e.g., older than 30 days)
                # 30 days = 2592000 seconds
                if time.time() - created_utc > 2592000:
                    continue
                    
                full_text = f"{title}\n{selftext}"
                post_url = f"https://www.reddit.com{permalink}"
                
                # Pre-filter: looking for people asking for recommendations, not news articles
                lower_text = full_text.lower()
                if any(kw in lower_text for kw in ["recommend", "looking for", "need", "best", "help"]):
                    leads.append({
                        "text": full_text.strip(),
                        "url": post_url,
                        "source": f"Reddit: r/{subreddit}",
                        "status": "New"
                    })
                    
            # Avoid sending requests too fast
            time.sleep(1.5)
            
        except Exception as e:
            logger.error(f"Failed to scrape Reddit URL {url}: {e}")
            
    return leads

if __name__ == "__main__":
    res = scrape_reddit()
    print(f"Reddit leads found: {len(res)}")
    for r in res[:5]:
        print(r['text'][:100], "-", r['url'])
