import asyncio
import os
import sys
from urllib.parse import urlparse
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import FragranceDNA, Brand
from scripts.review_50_fragrances import is_url_valid_for_fragrance, clean_source_url
from scripts.run_scheduled_scrapers import RETAILERS, scrape_shopify_search, is_authentic_match

async def test_10():
    print("Selecting 10 random fragrances to test live scraping and link matching...")
    async with async_session_maker() as session:
        # Pick 10 fragrances from verified brands
        stmt = (
            select(FragranceDNA)
            .options(selectinload(FragranceDNA.origin_brand))
            .where(
                FragranceDNA.is_dupe == False,
                FragranceDNA.origin_brand_id != None,
                ~FragranceDNA.canonical_name.ilike("%price range%"),
                ~FragranceDNA.canonical_name.ilike("%regular price%"),
                ~FragranceDNA.canonical_name.ilike("%sale price%")
            )
            .order_by(func.random())
            .limit(10)
        )
        res = await session.execute(stmt)
        dnas = res.scalars().all()
        
        async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
            for idx, dna in enumerate(dnas, 1):
                brand_name = str(dna.origin_brand.name) if dna.origin_brand and dna.origin_brand.name else "Unknown"
                frag_name = str(dna.canonical_name)
                query = f"{brand_name} {frag_name}".strip()
                print(f"\n[{idx}/10] Testing: {brand_name} — {frag_name}")
                print(f"Query: '{query}'")
                
                matched_offers = []
                for ret in RETAILERS:
                    results = await scrape_shopify_search(client, ret["url"], query)
                    for r in results:
                        title = str(r.get("title") or "")
                        url = str(r.get("url") or "")
                        price = float(r.get("price") or 0.0)
                        
                        # Test if authentic match
                        title_valid = is_authentic_match(title, brand_name, frag_name, False)
                        url_valid = is_url_valid_for_fragrance(url, frag_name, brand_name, False)
                        
                        if title_valid and url_valid and price > 10:
                            clean_u = clean_source_url(url)
                            matched_offers.append({
                                "retailer": ret["name"],
                                "price": price,
                                "title": title,
                                "url": clean_u
                            })
                        elif not title_valid or not url_valid:
                            # If it was returned by search but rejected, print why!
                            slug = urlparse(url).path
                            # print(f"  [REJECTED MISMATCH from {ret['name']}]: '{title}' (URL: {slug})")
                
                print(f"  Total Verified Matching Offers Found: {len(matched_offers)}")
                for o in matched_offers:
                    print(f"    [+] {o['retailer']}: ${o['price']:.2f} -> {o['url']}")

if __name__ == "__main__":
    asyncio.run(test_10())
