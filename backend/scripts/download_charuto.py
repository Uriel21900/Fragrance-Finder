import httpx
from bs4 import BeautifulSoup
import os

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def download_charuto():
    url = "https://perfumeonline.com/products/charuto-tobacco-vanille-pendora"
    with httpx.Client(headers=HEADERS, follow_redirects=True) as client:
        resp = client.get(url)
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            img = soup.select_one('.product__media img, .product-single__photo img, .product-gallery img')
            if not img:
                # Try any product image
                imgs = soup.find_all('img')
                for i in imgs:
                    src = i.get('src') or i.get('data-src') or ''
                    if 'charuto' in src.lower() or 'products' in src.lower():
                        img = i
                        break
            if img:
                src = img.get('src') or img.get('data-src')
                if src.startswith('//'):
                    src = f"https:{src}"
                print(f"Found Image URL: {src}")
                img_data = client.get(src).content
                out_path = os.path.join(os.getcwd(), 'frontend', 'public', 'images', 'charuto_tobacco_vanille.jpg')
                with open(out_path, 'wb') as f:
                    f.write(img_data)
                print(f"Saved to {out_path} ({len(img_data)} bytes)")

if __name__ == '__main__':
    download_charuto()
