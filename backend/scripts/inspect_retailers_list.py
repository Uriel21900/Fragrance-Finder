import asyncio
import os
import sys
import asyncpg
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")
if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8')

async def main():
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)

    print("=== CURRENT RETAILERS IN DB ===")
    retailers = await conn.fetch("SELECT * FROM retailer ORDER BY name;")
    for r in retailers:
        print(f"  {r['name']} | website_url: {r.get('website_url')} | base_url: {r.get('base_url')} | active: {r.get('is_active')}")

    target_websites = [
        "jomashop.com",
        "fragflex.com",
        "labelleperfumes.com",
        "labelle.com",
        "bestbrandsperfume.com",
        "theperfumespot.com",
        "reblscents.com",
        "aurafragrance.com",
        "banadirfragrance.com",
        "tripletraders.com",
        "perfumeonline.ca",
        "perfumeonline.com",
        "shoparomatix.com",
        "aromaconcepts.com",
        "anaustore.com",
        "lrlux.com",
        "beautyhouse.com",
        "giftexpress.com",
        "fragranceshop.com",
    ]

    print("\n=== MATCHING TARGET WEBSITES AGAINST PRICE OBSERVATIONS FOR AVENTUS ===")
    price_sources = await conn.fetch("""
        SELECT p.source_url, r.name as retailer_name
        FROM fragrance_line l
        JOIN fragrance_product fp ON l.line_id = fp.line_id
        JOIN product_variant v ON fp.product_id = v.product_id
        JOIN price_observation p ON v.variant_id = p.variant_id
        LEFT JOIN retailer r ON p.retailer_id = r.retailer_id
        WHERE l.dna_id IN (
            SELECT dna_id FROM fragrance_dna WHERE canonical_name IN ('Aventus', 'Aventus for Her')
        );
    """)
    print(f"Total price observations found: {len(price_sources)}")
    found_domains = set()
    for ps in price_sources:
        s = ps['source_url'] or ''
        for t in target_websites:
            if t in s:
                found_domains.add(t)
    
    print(f"Domains represented in Aventus prices ({len(found_domains)}): {found_domains}")
    missing = set(target_websites) - found_domains
    print(f"Missing domains: {missing}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
