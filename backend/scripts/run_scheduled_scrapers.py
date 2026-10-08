import os
import sys
import asyncio
import re
import datetime
import uuid
import urllib.parse
from typing import Any
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, update, insert, or_
from dotenv import load_dotenv

# Ensure backend root is in python path & load environment variables
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")

import httpx

# Try curl_cffi for Cloudflare / TLS fingerprint bypass; fallback to httpx
try:
    from curl_cffi.requests import AsyncSession as ClientSession  # type: ignore
    USING_CURL_CFFI = True
except Exception:
    ClientSession = httpx.AsyncClient  # type: ignore
    USING_CURL_CFFI = False

from models.schema import (
    FragranceDNA, Brand, FragranceLine, FragranceProduct, ProductVariant, 
    Retailer, PriceObservation, FragranceAlert
)
from scrapers.strict_matcher import is_strict_match, clean_source_url
from scripts.verify_fragrance_list import FRAGRANCE_LIST

# Safe UTF-8 configuration without detaching stdout buffer
if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8', errors='replace')

def format_async_db_url(raw_url: str | None) -> str:
    if not raw_url or not raw_url.strip():
        raise ValueError("DATABASE_URL environment variable is required. Please configure it in .env or GitHub Secrets.")
    url = raw_url.strip().strip("'").strip('"')
    if not url.startswith("postgres"):
        raise ValueError("DATABASE_URL must start with 'postgres://' or 'postgresql://'.")
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
}

# Verified high-yield discounters with responsive search endpoints
RETAILERS = [
    {"name": "Aura Fragrance", "normalized": "aurafragrance_com", "url": "https://aurafragrance.com"},
    {"name": "FragFlex", "normalized": "fragflex_com", "url": "https://fragflex.com"},
    {"name": "BeautyHouse", "normalized": "beautyhouse_com", "url": "https://beautyhouse.com"},
    {"name": "PerfumeOnline.com", "normalized": "perfumeonline_com", "url": "https://perfumeonline.com"},
    {"name": "Labelle Perfumes", "normalized": "labelle_com", "url": "https://labelleperfumes.com"},
    {"name": "Triple Traders", "normalized": "tripletraders_com", "url": "https://tripletraders.com"},
    {"name": "ReblScents", "normalized": "reblscents_com", "url": "https://reblscents.com"},
    {"name": "Shop Aromatix", "normalized": "shoparomatix_com", "url": "https://shoparomatix.com"},
    {"name": "Anau Store", "normalized": "anaustore_com", "url": "https://anaustore.com"},
    {"name": "Aroma Concepts", "normalized": "aromaconcepts_com", "url": "https://aromaconcepts.com"},
    {"name": "Banadir Fragrance", "normalized": "banadirfragrance_com", "url": "https://banadirfragrance.com"},
    {"name": "LrLux", "normalized": "lrlux_com", "url": "https://lrlux.com"},
    {"name": "GiftExpress", "normalized": "giftexpress_com", "url": "https://www.giftexpress.com"},
]

def clean_query(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    return re.sub(r"\s+", " ", cleaned).strip()

async def scrape_shopify_search(client: Any, base_url: str, query: str):
    cleaned = clean_query(query)
    encoded = urllib.parse.quote_plus(cleaned)
    search_url = f"{base_url}/search/suggest.json?q={encoded}&resources[type]=product&resources[options][unavailable_products]=hide"
    results = []
    
    # 1. Try suggest.json endpoint
    try:
        resp = await client.get(search_url, timeout=7.0)
        if resp.status_code == 200:
            ctype = resp.headers.get("content-type", "").lower()
            if "application/json" in ctype or resp.text.strip().startswith("{"):
                data = resp.json()
                products = data.get("resources", {}).get("results", {}).get("products", [])
                for p in products:
                    title = p.get("title", "")
                    price = float(p.get("price", 0.0))
                    url = p.get("url", "")
                    if url.startswith("/"):
                        url = f"{base_url}{url}"
                    results.append({"title": title, "price": price, "url": url})
                if results:
                    return results
    except Exception:
        pass

    # 2. Fallback to HTML search
    try:
        html_url = f"{base_url}/search?q={encoded}"
        resp = await client.get(html_url, timeout=7.0)
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            items = soup.select('.grid__item, .product-item, .product-card, .card, .product-grid-item')
            for item in items[:6]:
                title_elem = item.select_one('.title, .product-title, .card__heading, h2, h3, a.product-item__title')
                price_elem = item.select_one('.price-item--sale, .price-item, .money, .price')
                link_elem = item.select_one('a')
                if title_elem and price_elem and link_elem:
                    t = title_elem.text.strip()
                    p_match = re.search(r'[\d,\.]+', price_elem.text)
                    if p_match:
                        try:
                            pr = float(p_match.group().replace(',', ''))
                            href_val = link_elem.get('href', '')
                            u = str(href_val) if href_val else ''
                            if u.startswith('/'):
                                u = f"{base_url}{u}"
                            results.append({"title": t, "price": pr, "url": u})
                        except ValueError:
                            pass
    except Exception:
        pass
            
    return results

async def check_fragrance(
    client: Any,
    retailers: list[dict],
    retailer_map: dict[str, Any],
    brand_name: str,
    dna_name: str,
    is_dupe: bool,
    variant_id: Any,
    dna_id: Any,
) -> list[dict]:
    clean_brand = "Initio" if "initio" in brand_name.lower() else ("Maison Margiela" if "margiela" in brand_name.lower() else brand_name)
    query = f"{clean_brand} {dna_name}".strip()
    matches_found = []
    
    for ret in retailers:
        ret_id = retailer_map.get(ret["name"]) or retailer_map.get(ret["url"])
        try:
            matches = await scrape_shopify_search(client, ret["url"], query)
            for match in matches:
                is_match, reason = is_strict_match(
                    candidate_title=str(match["title"]),
                    candidate_url=str(match["url"]),
                    candidate_price=float(match["price"]) if match["price"] else None,
                    target_brand=brand_name,
                    target_fragrance=dna_name,
                    is_dupe_target=is_dupe,
                    require_full_bottle=True
                )
                if not is_match:
                    continue
                if match["price"] and match["price"] > 10.0:
                    clean_u = clean_source_url(str(match["url"]))
                    matches_found.append({
                        "retailer_name": ret["name"],
                        "retailer_id": ret_id,
                        "variant_id": variant_id,
                        "dna_id": dna_id,
                        "dna_name": dna_name,
                        "brand_name": brand_name,
                        "price": match["price"],
                        "url": clean_u,
                    })
                    break # Recorded best match for this retailer
            await asyncio.sleep(0.15)
        except Exception:
            pass

    return matches_found

async def run_scraper():
    print("=" * 70)
    print(f"STARTING SCHEDULED SCRAPER RUN: {datetime.datetime.now(datetime.timezone.utc).isoformat()}")
    print(f"Engine: {'curl_cffi (Chrome TLS Impersonation)' if USING_CURL_CFFI else 'httpx'}")
    print("=" * 70)

    db_url = format_async_db_url(os.getenv("DATABASE_URL"))
    if not db_url:
        print("[!] ERROR: DATABASE_URL environment variable is not set.")
        print("[!] For GitHub Actions, add it to repository secrets as DATABASE_URL.")
        print("[!] For local runs, ensure DATABASE_URL is set in backend/.env.")
        sys.exit(0)

    engine = create_async_engine(db_url, echo=False, pool_pre_ping=True)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    async with async_session() as session:
        # 1. Fetch all existing retailers and build lookup map
        res = await session.execute(select(Retailer))
        existing_retailers: dict[str, Any] = {str(r.normalized_name): r for r in res.scalars().all()}
        retailer_map = {}
        
        for ret in RETAILERS:
            norm = ret["normalized"]
            r_obj = existing_retailers.get(norm)
            if not r_obj:
                r_obj = existing_retailers.get(norm.replace("_com", ""))
            if not r_obj:
                domain_part = ret["url"].replace("https://", "").replace("http://", "").replace("www.", "").rstrip("/")
                for r in existing_retailers.values():
                    if r.website_url and domain_part in str(r.website_url):
                        r_obj = r
                        break
                    if r.name and str(r.name).lower() == ret["name"].lower():
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
            
        await session.commit()
        print(f"Loaded {len(retailer_map)} retailer mappings across {len(RETAILERS)} discounters.")
        
        # 2. Query clean fragrances joined with primary variant
        stmt = (
            select(FragranceDNA, Brand, ProductVariant)
            .join(Brand, FragranceDNA.origin_brand_id == Brand.brand_id)
            .join(FragranceLine, FragranceLine.dna_id == FragranceDNA.dna_id)
            .join(FragranceProduct, FragranceProduct.line_id == FragranceLine.line_id)
            .join(ProductVariant, ProductVariant.product_id == FragranceProduct.product_id)
            .where(
                FragranceDNA.canonical_name.not_ilike("!%"),
                FragranceDNA.canonical_name.not_ilike("$%"),
                FragranceDNA.canonical_name.not_ilike("Sale price%"),
                FragranceDNA.canonical_name.not_ilike("%Regular price%"),
                FragranceDNA.canonical_name.not_ilike("%Price range%"),
                FragranceDNA.canonical_name.not_ilike("%CAD%"),
                FragranceDNA.canonical_name.not_ilike("%USD%"),
                FragranceDNA.canonical_name.not_ilike("%http%"),
                Brand.name.not_ilike("%.com%"),
                Brand.name.not_ilike("%.ca%"),
            )
        )
        rows = (await session.execute(stmt)).all()
        
        # Deduplicate to primary variant per DNA
        unique_fragrances = {}
        for dna, brand, variant in rows:
            if dna.dna_id not in unique_fragrances:
                unique_fragrances[dna.dna_id] = (dna, brand, variant)
                
        fragrance_list = list(unique_fragrances.values())

        # Sort priority: 50 canonical fragrances FIRST, then genuine originals, then clones
        def sort_priority(item):
            dna, brand, variant = item
            c_name = str(dna.canonical_name).strip().lower()
            b_name = str(brand.name).strip().lower()
            for idx, f_item in enumerate(FRAGRANCE_LIST):
                canon_f, canon_b = f_item[0], f_item[1]
                if canon_f.lower() == c_name and (canon_b.lower() in b_name or b_name in canon_b.lower()):
                    return (0, idx)
            if dna.is_original_dna:
                return (1, str(dna.canonical_name).lower())
            return (2, str(dna.canonical_name).lower())

        fragrance_list.sort(key=sort_priority)
        print(f"Found {len(fragrance_list)} clean catalog fragrances with variants to track.")
        print(f"Prioritizing the {len(FRAGRANCE_LIST)} canonical fragrances first.")
        
        total_observations = 0

        # Initialize client session
        if USING_CURL_CFFI:
            client_ctx = ClientSession(impersonate="chrome")  # type: ignore
        else:
            client_ctx = httpx.AsyncClient(headers=HEADERS, follow_redirects=True)

        async with client_ctx as client:
            for idx, (dna, brand, variant) in enumerate(fragrance_list, 1):
                matches = await check_fragrance(
                    client=client,
                    retailers=RETAILERS,
                    retailer_map=retailer_map,
                    brand_name=str(brand.name),
                    dna_name=str(dna.canonical_name),
                    is_dupe=bool(dna.is_dupe),
                    variant_id=variant.variant_id,
                    dna_id=dna.dna_id,
                )

                for m in matches:
                    now = datetime.datetime.now(datetime.timezone.utc)
                    obs = PriceObservation(
                        price_observation_id=uuid.uuid4(),
                        variant_id=m["variant_id"],
                        retailer_id=m["retailer_id"],
                        observed_at=now,
                        captured_at=now,
                        price_amount=m["price"],
                        currency_code="USD",
                        condition="new",
                        source_url=m["url"],
                        availability="in_stock"
                    )
                    session.add(obs)
                    total_observations += 1
                    print(f"  [{idx:03d}/{len(fragrance_list)}] [+] {m['retailer_name']}: {m['brand_name']} - {m['dna_name']} -> ${m['price']:.2f}", flush=True)

                    # Check price alerts
                    alert_stmt = select(FragranceAlert).where(
                        FragranceAlert.dna_id == m["dna_id"],
                        FragranceAlert.target_price >= m["price"]
                    )
                    alerts = (await session.execute(alert_stmt)).scalars().all()
                    for al in alerts:
                        print(f"    🚨 PRICE ALERT: {m['dna_name']} dropped to ${m['price']:.2f} for {al.email}", flush=True)

                if not matches and (idx <= 50 or idx % 10 == 0):
                    print(f"  [{idx:03d}/{len(fragrance_list)}] Searched: {brand.name} - {dna.canonical_name} (0 in-stock discounter offers)", flush=True)

                # Commit batch after each fragrance that found matches or every 3 fragrances
                if matches or idx % 3 == 0:
                    await session.commit()

            # Final commit
            await session.commit()

        print("=" * 70)
        print(f"COMPLETED SCRAPER RUN: Recorded {total_observations} new price observations.")
        print("=" * 70)

    await engine.dispose()

if __name__ == "__main__":
    try:
        asyncio.run(run_scraper())
    except Exception as e:
        import traceback
        tb = traceback.format_exc()
        print(f"[!] FATAL ERROR in run_scraper: {e}", file=sys.stderr)
        traceback.print_exc()
        escaped_tb = tb.replace("\r", "").replace("\n", "%0A")
        print(f"::error title=Fatal Scraper Error::{escaped_tb}")
        sys.exit(1)
