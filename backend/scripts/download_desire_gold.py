import httpx
from bs4 import BeautifulSoup
import os

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def download_desire_gold():
    # Try multiple sources
    urls = [
        "https://reblscents.com/search/suggest.json?q=Dunhill+Desire+Gold&resources[type]=product",
        "https://perfumeonline.com/search/suggest.json?q=Dunhill+Desire+Gold&resources[type]=product",
        "https://aurafragrance.com/search/suggest.json?q=Dunhill+Desire+Gold&resources[type]=product"
    ]
    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        for u in urls:
            try:
                resp = client.get(u)
                if resp.status_code == 200:
                    data = resp.json()
                    prods = data.get('resources', {}).get('results', {}).get('products', [])
                    for p in prods:
                        if 'gold' in p.get('title', '').lower():
                            img_url = p.get('image') or p.get('featured_image')
                            if img_url:
                                if img_url.startswith('//'):
                                    img_url = f"https:{img_url}"
                                print(f"Found Desire Gold Image: {img_url}")
                                img_data = client.get(img_url).content
                                out_path = os.path.join(os.getcwd(), 'frontend', 'public', 'images', 'dunhill_desire_gold.jpg')
                                with open(out_path, 'wb') as f:
                                    f.write(img_data)
                                print(f"Saved Dunhill Desire Gold image to {out_path} ({len(img_data)} bytes)")
                                return
            except Exception as e:
                print(f"Error checking {u}: {e}")

if __name__ == '__main__':
    download_desire_gold()
