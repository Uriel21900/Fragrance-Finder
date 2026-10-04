import asyncio
import os
import sys
import re
import uuid
import httpx
import asyncpg
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")
if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8')

# The 17 websites requested by user
TARGET_STORES = [
    ("Jomashop", "jomashop.com", "https://www.jomashop.com"),
    ("Fragflex", "fragflex.com", "https://fragflex.com"),
    ("Labelle Perfumes", "labelleperfumes.com", "https://labelleperfumes.com"),
    ("Best Brands Perfume", "bestbrandsperfume.com", "https://bestbrandsperfume.com"),
    ("The Perfume Spot", "theperfumespot.com", "https://theperfumespot.com"),
    ("Rebl Scents", "reblscents.com", "https://reblscents.com"),
    ("Aura Fragrance", "aurafragrance.com", "https://www.aurafragrance.com"),
    ("Banadir Fragrance", "banadirfragrance.com", "https://banadirfragrance.com"),
    ("Triple Traders", "tripletraders.com", "https://tripletraders.com"),
    ("Perfume Online", "perfumeonline.ca", "https://perfumeonline.ca"),
    ("Shop Aromatix", "shoparomatix.com", "https://shoparomatix.com"),
    ("Aroma Concepts", "aromaconcepts.com", "https://aromaconcepts.com"),
    ("Anau Store", "anaustore.com", "https://anaustore.com"),
    ("LRLux", "lrlux.com", "https://lrlux.com"),
    ("Beauty House", "beautyhouse.com", "https://beautyhouse.com"),
    ("Gift Express", "giftexpress.com", "https://giftexpress.com"),
    ("Fragrance Shop", "fragranceshop.com", "https://fragranceshop.com"),
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Accept": "application/json, text/html, */*"
}

def classify_aventus_product(title: str, url: str):
    full_text = f"{title} {url}".lower()
    
    # Check if clone or inspired by (e.g. Club de Nuit, L'Aventure, Banadir, French Avenue)
    clone_indicators = [
        "club de nuit", "l'aventure", "laventure", "insurrection", "supremacy silver",
        "montblanc explorer", "explorer", "french avenue", "volare", "inspired by",
        "dupe", "clone", "banadirfragrance 01"
    ]
    if any(ci in full_text for ci in clone_indicators) and not "creed" in full_text:
        return "clone", None

    # Check flankers
    if "absolu" in full_text:
        return "aventus_absolu", None
    if "cologne" in full_text and not "eau de cologne" in full_text:
        return "aventus_cologne", "masculine"
    
    # Check women's version
    women_indicators = ["for her", "for women", "for woman", "woman", "women", "pour femme", "femme", "ladies"]
    if any(wi in full_text for wi in women_indicators):
        return "aventus_for_her", "feminine"
    
    # Otherwise, it's classic men's Aventus
    if "aventus" in full_text:
        return "aventus_men", "masculine"
    
    return "other", None

async def query_store(client: httpx.AsyncClient, name: str, domain: str, base_url: str):
    results = []
    
    # Strategy 1: Shopify suggest.json
    suggest_url = f"https://{domain}/search/suggest.json?q=Creed+Aventus&resources[type]=product"
    try:
        resp = await client.get(suggest_url, timeout=10.0)
        if resp.status_code == 200:
            data = resp.json()
            products = data.get("resources", {}).get("results", {}).get("products", [])
            for p in products:
                title = p.get("title", "")
                handle = p.get("handle", "")
                raw_price = p.get("price", "0")
                try:
                    price_val = float(str(raw_price).replace("$", "").replace(",", ""))
                except:
                    price_val = 0.0
                
                prod_url = p.get("url", f"/products/{handle}")
                if not prod_url.startswith("http"):
                    prod_url = f"https://{domain}{prod_url}"
                
                # Clean URL (remove tracking params)
                prod_url = prod_url.split("?")[0]
                
                cat, gender = classify_aventus_product(title, prod_url)
                if cat in ("aventus_men", "aventus_for_her", "aventus_cologne"):
                    results.append({
                        "store": name,
                        "domain": domain,
                        "title": title,
                        "price": price_val,
                        "url": prod_url,
                        "category": cat,
                        "gender": gender,
                        "image_url": p.get("image", p.get("featured_image", ""))
                    })
    except Exception as e:
        pass

    # Strategy 2: Shopify products.json with search if suggest didn't return
    if not results:
        prod_json_url = f"https://{domain}/products.json?limit=250"
        try:
            resp = await client.get(prod_json_url, timeout=12.0)
            if resp.status_code == 200:
                data = resp.json()
                for p in data.get("products", []):
                    title = p.get("title", "")
                    handle = p.get("handle", "")
                    body = p.get("body_html", "") or ""
                    if "aventus" in title.lower() or "aventus" in handle.lower():
                        variants = p.get("variants", [])
                        price_val = 0.0
                        if variants:
                            try:
                                price_val = float(variants[0].get("price", 0))
                            except:
                                price_val = 0.0
                        
                        img = ""
                        images = p.get("images", [])
                        if images:
                            img = images[0].get("src", "")
                            
                        prod_url = f"https://{domain}/products/{handle}"
                        cat, gender = classify_aventus_product(title, prod_url)
                        if cat in ("aventus_men", "aventus_for_her", "aventus_cologne"):
                            results.append({
                                "store": name,
                                "domain": domain,
                                "title": title,
                                "price": price_val,
                                "url": prod_url,
                                "category": cat,
                                "gender": gender,
                                "image_url": img
                            })
        except Exception as e:
            pass

    return results

async def main():
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)
    
    # 1. Fetch DNAs for Creed Aventus, Aventus for Her, Aventus Cologne
    aventus_men_dna = await conn.fetchval("SELECT dna_id FROM fragrance_dna WHERE canonical_name = 'Aventus' LIMIT 1;")
    aventus_her_dna = await conn.fetchval("SELECT dna_id FROM fragrance_dna WHERE canonical_name = 'Aventus for Her' LIMIT 1;")
    aventus_cologne_dna = await conn.fetchval("SELECT dna_id FROM fragrance_dna WHERE canonical_name = 'Aventus Cologne' LIMIT 1;")

    print(f"Creed Aventus (Men) DNA: {aventus_men_dna}")
    print(f"Aventus for Her (Women) DNA: {aventus_her_dna}")
    print(f"Aventus Cologne DNA: {aventus_cologne_dna}")

    # 2. Scrape all 17 target stores
    print("\n=== SCRAPING ALL 17 TARGET DISCOUNTERS FOR CREED AVENTUS ===")
    all_found = []
    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        tasks = [query_store(client, name, domain, base_url) for name, domain, base_url in TARGET_STORES]
        batch_results = await asyncio.gather(*tasks)
        for res_list in batch_results:
            all_found.extend(res_list)

    print(f"\nTotal Aventus offers found across target stores: {len(all_found)}")
    for item in all_found:
        print(f"[{item['category'].upper()}] {item['store']} | ${item['price']} | {item['title']}")
        print(f"   URL: {item['url']}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
