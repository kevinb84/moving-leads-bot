import requests
from bs4 import BeautifulSoup
from utils.logger import logger

CRAIGSLIST_URLS = [
    # Calgary & Edmonton "Wanted" categories searching for movers
    "https://calgary.craigslist.org/search/wan?query=moving",
    "https://edmonton.craigslist.org/search/wan?query=moving",
    
    # Calgary & Edmonton "Gigs" (people offering money for someone to move their stuff)
    "https://calgary.craigslist.org/search/lbg?query=moving",
    "https://edmonton.craigslist.org/search/lbg?query=moving"
]

def scrape_craigslist():
    leads = []
    
    for url in CRAIGSLIST_URLS:
        try:
            logger.info(f"Scraping Craigslist: {url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            
            # Craigslist changed their HTML to have list items with a class of "cl-search-result"
            # or specifically title elements
            listings = soup.select("li.cl-search-result, li.result-row, div.result-info")
            
            logger.info(f"Craigslist found {len(listings)} potential listings.")
            
            for listing in listings:
                try:
                    title_elem = listing.select_one(".title, .result-title, .cl-app-anchor")
                    if not title_elem:
                        continue
                        
                    title = title_elem.text.strip()
                    link = title_elem.get('href')
                    
                    if not link.startswith("http"):
                        continue
                        
                    # Pre-filter
                    lower_title = title.lower()
                    if any(kw in lower_title for kw in ["mover", "moving", "truck", "load", "pack", "help"]):
                        leads.append({
                            "text": title,
                            "url": link,
                            "source": "Craigslist",
                            "status": "New"
                        })
                except Exception as e:
                    continue
                    
        except Exception as e:
            logger.error(f"Failed to scrape Craigslist URL {url}: {e}")
            
    return leads

if __name__ == "__main__":
    res = scrape_craigslist()
    print(f"Craigslist leads found: {len(res)}")
    for r in res:
        print(r['text'], "-", r['url'])
