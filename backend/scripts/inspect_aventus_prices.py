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

    print("=== AVENTUS FRAGRANCE DNAs ===")
    dnas = await conn.fetch("""
        SELECT d.dna_id, d.canonical_name, d.gender, d.image_url, b.name as brand_name
        FROM fragrance_dna d
        LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
        WHERE d.canonical_name ILIKE '%aventus%'
        ORDER BY d.canonical_name;
    """)
    for d in dnas:
        print(f"DNA ID: {d['dna_id']} | Brand: {d['brand_name']} | Name: {d['canonical_name']} | Gender: {d['gender']}")

    print("\n=== PRICES ATTACHED TO CREED AVENTUS (Masculine) ===")
    aventus_dna = await conn.fetchrow("""
        SELECT dna_id FROM fragrance_dna WHERE canonical_name = 'Aventus' LIMIT 1;
    """)
    if aventus_dna:
        dna_id = aventus_dna['dna_id']
        prices = await conn.fetch("""
            SELECT p.price_amount, p.currency_code, p.source_url, r.name as retailer_name,
                   v.volume_ml, v.package_type, fp.product_id, l.name as line_name
            FROM fragrance_line l
            JOIN fragrance_product fp ON l.line_id = fp.line_id
            JOIN product_variant v ON fp.product_id = v.product_id
            JOIN price_observation p ON v.variant_id = p.variant_id
            LEFT JOIN retailer r ON p.retailer_id = r.retailer_id
            WHERE l.dna_id = $1
            ORDER BY p.price_amount ASC;
        """, dna_id)
        print(f"Total prices for Creed Aventus ({dna_id}): {len(prices)}")
        for p in prices:
            print(f"  ${p['price_amount']} | {p['retailer_name']} | {p['volume_ml']}ml | {p['source_url']}")

    print("\n=== PRICES ATTACHED TO AVENTUS FOR HER ===")
    her_dna = await conn.fetchrow("""
        SELECT dna_id FROM fragrance_dna WHERE canonical_name = 'Aventus for Her' LIMIT 1;
    """)
    if her_dna:
        dna_id = her_dna['dna_id']
        prices = await conn.fetch("""
            SELECT p.price_amount, p.currency_code, p.source_url, r.name as retailer_name,
                   v.volume_ml, v.package_type
            FROM fragrance_line l
            JOIN fragrance_product fp ON l.line_id = fp.line_id
            JOIN product_variant v ON fp.product_id = v.product_id
            JOIN price_observation p ON v.variant_id = p.variant_id
            LEFT JOIN retailer r ON p.retailer_id = r.retailer_id
            WHERE l.dna_id = $1
            ORDER BY p.price_amount ASC;
        """, dna_id)
        print(f"Total prices for Aventus for Her ({dna_id}): {len(prices)}")
        for p in prices:
            print(f"  ${p['price_amount']} | {p['retailer_name']} | {p['source_url']}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
