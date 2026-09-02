import os
import sys
import asyncio
import re
import datetime
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, update, insert, or_

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.schema import (
    FragranceDNA, Brand, FragranceLine, FragranceProduct, ProductVariant, 
    Retailer, PriceObservation, FragranceAlert
)

DEFAULT_DATABASE_URL = (
    "postgresql+asyncpg://neondb_owner:npg_iN45StWGXmpK@ep-winter-surf-ay718z8s-pooler.c-5.us-east-2.aws.neon.tech/neondb?ssl=require"
)

def format_async_db_url(raw_url: str | None) -> str:
    url = (raw_url or "").strip() or DEFAULT_DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Handle SSL params for asyncpg
    if "sslmode=" in url:
        url = url.replace("sslmode=require", "ssl=require").replace("sslmode=prefer", "ssl=prefer")
    elif "?" in url and "ssl=" not in url:
        url = f"{url}&ssl=require"
    elif "?" not in url:
        url = f"{url}?ssl=require"
    return url

DATABASE_URL = format_async_db_url(os.getenv("DATABASE_URL"))
engine = create_async_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

RETAILERS = [
    {"name": "PerfumeOnline.com", "normalized": "perfumeonline_com", "url": "https://perfumeonline.com"},
    {"name": "Aura Fragrance", "normalized": "aurafragrance_com", "url": "https://aurafragrance.com"},
    {"name": "ReblScents", "normalized": "reblscents_com", "url": "https://reblscents.com"},
    {"name": "Banadir Fragrance", "normalized": "banadirfragrance_com", "url": "https://banadirfragrance.com"},
    {"name": "Shop Aromatix", "normalized": "shoparomatix_com", "url": "https://shoparomatix.com"}
]

CLONE_DISQUALIFIERS = [
    "inspired by", "our version of", "impression of", "type of", "dupe of",
    "perfume oil", "body oil", "pocket spray", "sample vial", "decant",
    "twist of", "smells like", "fragrance oil"
]

def is_authentic_match(title: str, query_brand: str, query_name: str, is_dupe_target: bool) -> bool:
    title_lower = title.lower()
    
    # If we are scraping for an authentic fragrance, exclude clones and oils
    if not is_dupe_target:
        for disq in CLONE_DISQUALIFIERS:
            if disq in title_lower:
                return False
        
        # Check brand name presence if provided
        if query_brand.lower() not in title_lower:
            # Check known brand variants
            if query_brand.lower() == "parfums de marly" and "pdm" not in title_lower:
                return False
            elif query_brand.lower() == "maison francis kurkdjian" and "mfk" not in title_lower:
                return False
    
    return True

async def scrape_shopify_search(client: httpx.AsyncClient, base_url: str, query: str):
    search_url = f"{base_url}/search/suggest.json?q={query}&resources[type]=product&resources[options][unavailable_products]=hide"
    results = []
    try:
        resp = await client.get(search_url, headers=HEADERS, timeout=8.0)
        if resp.status_code == 200:
            data = resp.json()
            products = data.get("resources", {}).get("results", {}).get("products", [])
            for p in products:
                title = p.get("title", "")
                price = float(p.get("price", 0.0))
                url = p.get("url", "")
                if url.startswith("/"):
                    url = f"{base_url}{url}"
                results.append({"title": title, "price": price, "url": url})
    except Exception:
        # Fallback to HTML search if suggest json is unavailable
        try:
            html_url = f"{base_url}/search?q={query}"
            resp = await client.get(html_url, headers=HEADERS, timeout=8.0)
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, 'html.parser')
                items = soup.select('.grid__item, .product-item, .product-card, .card')
                for item in items[:5]:
                    title_elem = item.select_one('.title, .product-title, .card__heading, h2, h3, a.product-item__title')
                    price_elem = item.select_one('.price-item--sale, .price-item, .money, .price')
                    link_elem = item.select_one('a')
                    if title_elem and price_elem and link_elem:
                        t = title_elem.text.strip()
                        p_match = re.search(r'[\d,\.]+', price_elem.text)
                        if p_match:
                            pr = float(p_match.group().replace(',', ''))
                            u = link_elem.get('href', '')
                            if u.startswith('/'):
                                u = f"{base_url}{u}"
                            results.append({"title": t, "price": pr, "url": u})
        except Exception:
            pass
            
    return results

async def run_scraper():
    print("=" * 60)
    print(f"STARTING SCHEDULED SCRAPER RUN: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print("=" * 60)
    
    async with async_session() as session:
        # 1. Fetch all existing retailers and build lookup map
        res = await session.execute(select(Retailer))
        existing_retailers = {r.normalized_name: r for r in res.scalars().all()}
        retailer_map = {}
        
        for ret in RETAILERS:
            norm = ret["normalized"]
            r_obj = existing_retailers.get(norm)
            if not r_obj:
                r_obj = existing_retailers.get(norm.replace("_com", ""))
            if not r_obj:
                domain_part = ret["url"].replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
                for r in existing_retailers.values():
                    if r.website_url and domain_part in r.website_url:
                        r_obj = r
                        break
                    if r.name and r.name.lower() == ret["name"].lower():
                        r_obj = r
                        break
                        
            if not r_obj:
                r_obj = Retailer(
                    name=ret["name"],
                    normalized_name=norm,
                    website_url=ret["url"]
                )
                session.add(r_obj)
                await session.flush()
                existing_retailers[norm] = r_obj
                
            retailer_map[ret["name"]] = r_obj.retailer_id
            retailer_map[ret["url"]] = r_obj.retailer_id
            retailer_map[norm] = r_obj.retailer_id
            print(f"Mapped retailer: {ret['name']} -> {r_obj.retailer_id}")
            
        await session.commit()
        
        # 2. Query tracked fragrances joined with primary variant
        stmt = (
            select(FragranceDNA, Brand, ProductVariant)
            .join(Brand, FragranceDNA.origin_brand_id == Brand.brand_id)
            .join(FragranceLine, FragranceLine.dna_id == FragranceDNA.dna_id)
            .join(FragranceProduct, FragranceProduct.line_id == FragranceLine.line_id)
            .join(ProductVariant, ProductVariant.product_id == FragranceProduct.product_id)
            .order_by(FragranceDNA.canonical_name)
        )
        rows = (await session.execute(stmt)).all()
        
        # Deduplicate to primary variant per DNA
        unique_fragrances = {}
        for dna, brand, variant in rows:
            if dna.dna_id not in unique_fragrances:
                unique_fragrances[dna.dna_id] = (dna, brand, variant)
                
        fragrance_list = list(unique_fragrances.values())
        print(f"Found {len(fragrance_list)} unique fragrances with variants to track.")
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            updated_count = 0
            
            for idx, (dna, brand, variant) in enumerate(fragrance_list, 1):
                query = f"{brand.name} {dna.canonical_name}".strip()
                
                for ret in RETAILERS:
                    try:
                        matches = await scrape_shopify_search(client, ret["url"], query)
                        for match in matches:
                            if is_authentic_match(match["title"], brand.name, dna.canonical_name, dna.is_dupe):
                                if match["price"] and match["price"] > 10.0:
                                    now = datetime.datetime.now(datetime.timezone.utc)
                                    obs = PriceObservation(
                                        variant_id=variant.variant_id,
                                        retailer_id=retailer_map.get(ret["name"]) or retailer_map.get(ret["url"]),
                                        observed_at=now,
                                        captured_at=now,
                                        price_amount=match["price"],
                                        currency_code="USD",
                                        source_url=match["url"],
                                        availability="in_stock"
                                    )
                                    session.add(obs)
                                    updated_count += 1
                                    print(f"  [{idx}/{len(fragrance_list)}] [+] {ret['name']}: {dna.canonical_name} -> ${match['price']:.2f}", flush=True)
                                    
                                    # Check price drop alerts
                                    alert_stmt = select(FragranceAlert).where(
                                        FragranceAlert.dna_id == dna.dna_id,
                                        FragranceAlert.target_price >= match["price"]
                                    )
                                    alerts = (await session.execute(alert_stmt)).scalars().all()
                                    for al in alerts:
                                        print(f"🚨 PRICE ALERT: {dna.canonical_name} dropped to ${match['price']:.2f} for {al.email}", flush=True)
                                    
                                    break # Recorded best match for this retailer
                    except Exception as err:
                        pass
                        
                if updated_count > 0 and updated_count % 10 == 0:
                    await session.commit()
            
            # Final commit for remaining updates
            await session.commit()
                
        print("=" * 60)
        print(f"COMPLETED SCRAPER RUN: Recorded {updated_count} new price observations.")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_scraper())

