import asyncio
import os
import sys
import datetime
from urllib.parse import urlparse
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select, delete, func, or_
from sqlalchemy.orm import selectinload

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import (
    FragranceDNA, Brand, FragranceLine, FragranceProduct, ProductVariant,
    Retailer, PriceObservation
)
from scrapers.strict_matcher import is_strict_match, clean_source_url

# 17 Retailer stores requested by the user
TARGET_STORES = [
    {"name": "Jomashop", "url": "https://www.jomashop.com", "normalized": "jomashop"},
    {"name": "FragFlex", "url": "https://fragflex.com", "normalized": "fragflex_com"},
    {"name": "Labelle Perfumes", "url": "https://labelleperfumes.com", "normalized": "labelleperfumes_com"},
    {"name": "BestBrandsPerfume", "url": "https://bestbrandsperfume.com", "normalized": "bestbrandsperfume_com"},
    {"name": "ThePerfumeSpot", "url": "https://theperfumespot.com", "normalized": "theperfumespot_com"},
    {"name": "ReblScents", "url": "https://reblscents.com", "normalized": "reblscents_com"},
    {"name": "Aura Fragrance", "url": "https://aurafragrance.com", "normalized": "aurafragrance_com"},
    {"name": "Banadir Fragrance", "url": "https://banadirfragrance.com", "normalized": "banadirfragrance_com"},
    {"name": "TripleTraders", "url": "https://tripletraders.com", "normalized": "tripletraders_com"},
    {"name": "PerfumeOnline.com", "url": "https://perfumeonline.com", "normalized": "perfumeonline_com"},
    {"name": "Shop Aromatix", "url": "https://shoparomatix.com", "normalized": "shoparomatix_com"},
    {"name": "AromaConcepts", "url": "https://www.aromaconcepts.com", "normalized": "aromaconcepts_com"},
    {"name": "Anau Store", "url": "https://anaustore.com", "normalized": "anaustore_com"},
    {"name": "LRLux", "url": "https://lrlux.com", "normalized": "lrlux_com"},
    {"name": "BeautyHouse", "url": "https://beautyhouse.com", "normalized": "beautyhouse_com"},
    {"name": "GiftExpress", "url": "https://giftexpress.com", "normalized": "giftexpress_com"},
    {"name": "FragranceShop", "url": "https://fragranceshop.com", "normalized": "fragranceshop_com"},
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 FragranceFinder/2.0",
    "Accept": "application/json, text/html"
}

async def scrape_store_products(client: httpx.AsyncClient, store: Dict[str, str], query: str) -> List[Dict[str, Any]]:
    """Scrapes products from a store search endpoint with timeout and error resilience."""
    base_url = store["url"]
    results = []
    
    # 1. Try Shopify suggest API (supported by 15 of the 17 stores)
    suggest_url = f"{base_url}/search/suggest.json?q={query}&resources[type]=product&resources[options][unavailable_products]=hide"
    try:
        resp = await client.get(suggest_url, headers=HEADERS, timeout=7.0)
        if resp.status_code == 200:
            data = resp.json()
            products = data.get("resources", {}).get("results", {}).get("products", [])
            for p in products:
                title = p.get("title", "")
                price = float(p.get("price", 0.0))
                url = p.get("url", "")
                if url.startswith("/"):
                    url = f"{base_url}{url}"
                if title and url:
                    results.append({"title": title, "price": price, "url": url})
            if results:
                return results
    except Exception:
        pass
        
    # 2. Fallback to HTML search
    try:
        html_url = f"{base_url}/search?q={query}"
        resp = await client.get(html_url, headers=HEADERS, timeout=7.0)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            items = soup.select('.grid__item, .product-item, .product-card, .card, .product-item__content')
            for item in items[:6]:
                title_elem = item.select_one('.title, .product-title, .card__heading, h2, h3, a.product-item__title')
                price_elem = item.select_one('.price-item--sale, .price-item, .money, .price')
                link_elem = item.select_one('a[href*="/products/"]') or item.select_one('a')
                if title_elem and link_elem:
                    t = title_elem.text.strip()
                    href_val = link_elem.get('href', '')
                    u = str(href_val) if href_val else ''
                    if u.startswith('/'):
                        u = f"{base_url}{u}"
                    pr = 0.0
                    if price_elem:
                        import re
                        m = re.search(r'[\d,\.]+', price_elem.text)
                        if m:
                            try:
                                pr = float(m.group().replace(',', ''))
                            except ValueError:
                                pass
                    if t and u:
                        results.append({"title": t, "price": pr, "url": u})
    except Exception:
        pass
        
    return results

async def run_scrape_and_verify():
    print("=" * 70)
    print("STARTING SCRAPE & VERIFICATION FOR 10 TARGET FRAGRANCES")
    print("=" * 70)

    # 10 fragrances to test (including Layton and Aventus as specified by user)
    TEST_TARGETS = [
        ("Parfums de Marly", "Layton"),
        ("Creed", "Aventus"),
        ("Maison Francis Kurkdjian", "Baccarat Rouge 540"),
        ("Kilian", "Angels' Share"),
        ("Tom Ford", "Tobacco Vanille"),
        ("Dior", "Sauvage Elixir"),
        ("Xerjoff", "Naxos"),
        ("Yves Saint Laurent", "Y Eau de Parfum"),
        ("Parfums de Marly", "Herod"),
        ("Creed", "Green Irish Tweed")
    ]

    async with async_session_maker() as session:
        # Step 1: Ensure all 17 retailers exist in DB
        retailer_db_map = {}
        for s in TARGET_STORES:
            res = await session.execute(select(Retailer).filter_by(normalized_name=s["normalized"]))
            ret_obj = res.scalar_one_or_none()
            if not ret_obj:
                ret_obj = Retailer(name=s["name"], normalized_name=s["normalized"], website_url=s["url"])
                session.add(ret_obj)
                await session.flush()
            retailer_db_map[s["name"]] = ret_obj.retailer_id

        # Step 2: Scrape and strictly verify links for each of the 10 fragrances
        verification_summary = []
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            for idx, (brand_name, frag_name) in enumerate(TEST_TARGETS, 1):
                print(f"\n[{idx}/10] SCRAPING & VERIFYING: {brand_name} — {frag_name}")
                
                # Find DNA in DB
                dna_res = await session.execute(
                    select(FragranceDNA)
                    .options(selectinload(FragranceDNA.origin_brand))
                    .where(FragranceDNA.canonical_name.ilike(frag_name), FragranceDNA.is_dupe == False)
                )
                dna = dna_res.scalars().first()
                if not dna:
                    print(f"  [!] Fragrance '{frag_name}' not found in database. Skipping.")
                    continue

                # Find Primary Variant
                var_stmt = (
                    select(ProductVariant)
                    .join(FragranceProduct, ProductVariant.product_id == FragranceProduct.product_id)
                    .join(FragranceLine, FragranceProduct.line_id == FragranceLine.line_id)
                    .where(FragranceLine.dna_id == dna.dna_id)
                    .order_by(ProductVariant.volume_ml.desc())
                )
                variant = (await session.execute(var_stmt)).scalars().first()

                search_query = f"{brand_name} {frag_name}".strip()
                print(f"  Query: '{search_query}'")
                
                verified_links = []
                rejected_count = 0
                
                for store in TARGET_STORES:
                    store_name = store["name"]
                    raw_items = await scrape_store_products(client, store, search_query)
                    
                    for item in raw_items:
                        candidate_title = item["title"]
                        candidate_url = item["url"]
                        candidate_price = item["price"]
                        
                        is_valid, reason = is_strict_match(
                            candidate_title=candidate_title,
                            candidate_url=candidate_url,
                            candidate_price=candidate_price,
                            target_brand=brand_name,
                            target_fragrance=frag_name,
                            is_dupe_target=False,
                            require_full_bottle=True
                        )
                        
                        if is_valid and candidate_price > 20.0:
                            clean_url = clean_source_url(candidate_url)
                            verified_links.append({
                                "retailer": store_name,
                                "retailer_id": retailer_db_map[store_name],
                                "price": candidate_price,
                                "title": candidate_title,
                                "url": clean_url
                            })
                            print(f"    [MATCHED] {store_name}: ${candidate_price:.2f} -> {clean_url}")
                        else:
                            rejected_count += 1
                            # Debug rejected flanker/sibling match
                            if any(k in candidate_title.lower() for k in ["delina", "viking", "byerley", "pegasus", "silver mountain"]):
                                print(f"    [PREVENTED MISMATCH from {store_name}]: '{candidate_title}' (Reason: {reason})")

                print(f"  Results: {len(verified_links)} verified links matched, {rejected_count} irrelevant/sibling items rejected.")

                # Deduplicate store links (keep lowest price offer per retailer)
                unique_store_links = {}
                for l in verified_links:
                    r_id = l["retailer_id"]
                    if r_id not in unique_store_links or l["price"] < unique_store_links[r_id]["price"]:
                        unique_store_links[r_id] = l

                # Update in DB: If variant exists, remove previous price observations for this variant and insert freshly verified ones
                if variant and unique_store_links:
                    await session.execute(
                        delete(PriceObservation).where(PriceObservation.variant_id == variant.variant_id)
                    )
                    now = datetime.datetime.now(datetime.timezone.utc)
                    for l in unique_store_links.values():
                        new_obs = PriceObservation(
                            variant_id=variant.variant_id,
                            retailer_id=l["retailer_id"],
                            observed_at=now,
                            captured_at=now,
                            price_amount=l["price"],
                            currency_code="USD",
                            source_url=l["url"],
                            availability="in_stock"
                        )
                        session.add(new_obs)
                    await session.commit()
                    print(f"  [SAVED] Stored {len(unique_store_links)} verified price observations in Neon DB.")

                verification_summary.append({
                    "brand": brand_name,
                    "fragrance": frag_name,
                    "image": dna.image_url,
                    "verified_links": list(unique_store_links.values())
                })

        print("\n" + "=" * 70)
        print("SCRAPE & VERIFICATION COMPLETE FOR ALL 10 FRAGRANCES")
        print("=" * 70)
        return verification_summary

if __name__ == "__main__":
    asyncio.run(run_scrape_and_verify())
