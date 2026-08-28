import os
import sys
import asyncio
import re
import datetime
from urllib.parse import urlparse
import httpx
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, update, insert

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.schema import (
    FragranceDNA, Brand, FragranceLine, FragranceProduct, ProductVariant, 
    Retailer, PriceObservation, FragranceAlert
)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://neondb_owner:npg_iN45StWGXmpK@ep-winter-surf-ay718z8s-pooler.c-5.us-east-2.aws.neon.tech/neondb?ssl=require"
)

# Convert postgres:// or postgresql:// to postgresql+asyncpg:// if needed
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+asyncpg" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)

# Handle SSL params for Neon and asyncpg
if "?" in DATABASE_URL:
    base, _ = DATABASE_URL.split("?", 1)
    DATABASE_URL = f"{base}?ssl=require"
elif "neon.tech" in DATABASE_URL:
    DATABASE_URL = f"{DATABASE_URL}?ssl=require"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

RETAILERS = [
    {"name": "perfumeonline.com", "url": "https://perfumeonline.com"},
    {"name": "aurafragrance.com", "url": "https://aurafragrance.com"},
    {"name": "reblscents.com", "url": "https://reblscents.com"},
    {"name": "banadirfragrance.com", "url": "https://banadirfragrance.com"},
    {"name": "shoparomatix.com", "url": "https://shoparomatix.com"}
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
        resp = await client.get(search_url, headers=HEADERS, timeout=10.0)
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
    except Exception as e:
        # Fallback to HTML search if suggest json is unavailable
        try:
            html_url = f"{base_url}/search?q={query}"
            resp = await client.get(html_url, headers=HEADERS, timeout=10.0)
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
        # Ensure retailers exist in DB
        retailer_map = {}
        for ret in RETAILERS:
            r_obj = (await session.execute(select(Retailer).where(Retailer.name == ret["name"]))).scalars().first()
            if not r_obj:
                r_obj = Retailer(
                    name=ret["name"],
                    normalized_name=ret["name"].replace(".", "_"),
                    website_url=ret["url"]
                )
                session.add(r_obj)
                await session.flush()
            retailer_map[ret["name"]] = r_obj.retailer_id
            
        await session.commit()
        
        # Query tracked fragrances
        stmt = select(FragranceDNA, Brand).join(Brand, FragranceDNA.origin_brand_id == Brand.brand_id)
        fragrances = (await session.execute(stmt)).all()
        
        print(f"Found {len(fragrances)} fragrances to track in database.")
        
        async with httpx.AsyncClient(follow_redirects=True) as client:
            updated_count = 0
            
            for dna, brand in fragrances:
                query = f"{brand.name} {dna.canonical_name}".strip()
                
                # Fetch product variant
                var_stmt = (
                    select(ProductVariant)
                    .join(FragranceProduct, ProductVariant.product_id == FragranceProduct.product_id)
                    .join(FragranceLine, FragranceProduct.line_id == FragranceLine.line_id)
                    .where(FragranceLine.dna_id == dna.dna_id)
                )
                variant = (await session.execute(var_stmt)).scalars().first()
                if not variant:
                    continue
                    
                for ret in RETAILERS:
                    try:
                        matches = await scrape_shopify_search(client, ret["url"], query)
                        for match in matches:
                            if is_authentic_match(match["title"], brand.name, dna.canonical_name, dna.is_dupe):
                                if match["price"] and match["price"] > 10.0:
                                    # Insert new price observation
                                    obs = PriceObservation(
                                        variant_id=variant.variant_id,
                                        retailer_id=retailer_map[ret["name"]],
                                        price_amount=match["price"],
                                        currency_code="USD",
                                        source_url=match["url"],
                                        captured_at=datetime.datetime.now(datetime.timezone.utc)
                                    )
                                    session.add(obs)
                                    updated_count += 1
                                    
                                    # Check price drop alerts
                                    alert_stmt = select(FragranceAlert).where(
                                        FragranceAlert.dna_id == dna.dna_id,
                                        FragranceAlert.target_price >= match["price"]
                                    )
                                    alerts = (await session.execute(alert_stmt)).scalars().all()
                                    for al in alerts:
                                        print(f"🚨 PRICE ALERT TRIGGERED: {dna.canonical_name} dropped to ${match['price']:.2f} (Target: ${al.target_price:.2f}) for {al.email}")
                                    
                                    break # Recorded best match for this retailer
                    except Exception as err:
                        pass
                        
                await session.commit()
                
        print("=" * 60)
        print(f"COMPLETED SCRAPER RUN: Updated {updated_count} price observations.")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(run_scraper())
