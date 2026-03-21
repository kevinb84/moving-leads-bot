import requests
from bs4 import BeautifulSoup

url = "https://www.kijiji.ca/b-calgary/need-movers/k0l1700199"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/119.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
}
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

listings = soup.select("[data-testid='listing-card'], .search-item, .regular-ad")
print("Found", len(listings))
if listings:
    html = listings[0].prettify()
    print(html[:500]) # First 500 chars 
    
    # Try finding an 'a' tag. The title is usually in an 'a' tag.
    a_tags = listings[0].find_all('a')
    for a in a_tags:
        print("Link:", a.get('href'), "Text:", a.text.strip())
