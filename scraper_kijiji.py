import requests
from bs4 import BeautifulSoup
from utils.logger import logger

KIJIJI_URLS = [
    # Calgary search for "need movers"
    "https://www.kijiji.ca/b-calgary/need-movers/k0l1700199",
    "https://www.kijiji.ca/b-calgary/need-moving/k0l1700199",
    # Edmonton search for "need movers"
    "https://www.kijiji.ca/b-edmonton/need-movers/k0l1700203",
    "https://www.kijiji.ca/b-edmonton/need-moving/k0l1700203"
]

def scrape_kijiji():
    leads = []
    
    for url in KIJIJI_URLS:
        try:
            logger.info(f"Scraping Kijiji: {url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                              "AppleWebKit/537.36 (KHTML, like Gecko) "
                              "Chrome/119.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9"
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Kijiji listings usually have a data-testid="listing-card" or class "search-item" "regular-ad" etc.
            listings = soup.select("[data-testid='listing-card'], .search-item, .regular-ad")
            
            logger.info(f"Kijiji found {len(listings)} potential listings.")
            
            for listing in listings:
                try:
                    title_elem = listing.select_one("[data-testid='listing-title'], a.title")
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    link = title_elem.get('href')
                    
                    if not link.startswith("http"):
                        link = "https://www.kijiji.ca" + link
                        
                    # Pre-filter keywords to make sure it's a person seeking movers
                    # Often "need movers", "looking for movers"
                    lower_title = title.lower()
                    if any(kw in lower_title for kw in ["need", "looking", "help", "want", "required", "iso", "seeking"]):
                        # It might be someone needing movers rather than offering services
                        leads.append({
                            "text": title,
                            "url": link,
                            "source": "Kijiji",
                            "status": "New"
                        })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to scrape Kijiji URL {url}: {e}")
            
    return leads

if __name__ == "__main__":
    res = scrape_kijiji()
    print(f"Kijiji leads found: {len(res)}")
    for r in res:
        print(r['text'], "-", r['url'])
