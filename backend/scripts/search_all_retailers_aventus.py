import asyncio
import os
import sys
import json
import httpx
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")
if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8')

RETAILER_DOMAINS = [
    ("Jomashop", "jomashop.com"),
    ("Fragflex", "fragflex.com"),
    ("Labelle Perfumes", "labelleperfumes.com"),
    ("Best Brands Perfume", "bestbrandsperfume.com"),
    ("The Perfume Spot", "theperfumespot.com"),
    ("Rebl Scents", "reblscents.com"),
    ("Aura Fragrance", "aurafragrance.com"),
    ("Banadir Fragrance", "banadirfragrance.com"),
    ("Triple Traders", "tripletraders.com"),
    ("Perfume Online", "perfumeonline.ca"),
    ("Shop Aromatix", "shoparomatix.com"),
    ("Aroma Concepts", "aromaconcepts.com"),
    ("Anau Store", "anaustore.com"),
    ("LRLux", "lrlux.com"),
    ("Beauty House", "beautyhouse.com"),
    ("Gift Express", "giftexpress.com"),
    ("Fragrance Shop", "fragranceshop.com"),
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

async def search_retailer(name: str, domain: str):
    print(f"\n--- Checking {name} ({domain}) ---")
    url = f"https://{domain}/search/suggest.json?q=Aventus&resources[type]=product"
    async with httpx.AsyncClient(headers=headers, timeout=12.0, follow_redirects=True) as client:
        try:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                products = data.get("resources", {}).get("results", {}).get("products", [])
                print(f"  Found {len(products)} products via suggest.json:")
                for p in products:
                    title = p.get("title", "")
                    handle = p.get("handle", "")
                    price = p.get("price", "")
                    url_full = p.get("url", f"https://{domain}/products/{handle}")
                    if not url_full.startswith("http"):
                        url_full = f"https://{domain}{url_full}"
                    print(f"    - [{title}] | Price: ${price} | URL: {url_full}")
                return products
            else:
                print(f"  Status {resp.status_code} on suggest.json. Trying standard search...")
        except Exception as e:
            print(f"  Error on suggest.json: {e}")

    # Fallback to query Shopify products.json with filter
    return []

async def main():
    tasks = [search_retailer(name, domain) for name, domain in RETAILER_DOMAINS]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())
