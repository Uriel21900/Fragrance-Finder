import asyncio, os, sys
import asyncpg
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")
if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8')

async def main():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    dna_id = "9d5c1869-8bb3-48a3-9527-1e0563794520"
    rows = await conn.fetch("""
        SELECT 
          p.price_observation_id,
          p.price_amount,
          p.currency_code,
          p.source_url,
          p.captured_at,
          r.name as retailer_name,
          v.volume_ml,
          v.package_type
        FROM fragrance_line l
        JOIN fragrance_product fp ON l.line_id = fp.line_id
        JOIN product_variant v ON fp.product_id = v.product_id
        JOIN price_observation p ON v.variant_id = p.variant_id
        LEFT JOIN retailer r ON p.retailer_id = r.retailer_id
        WHERE l.dna_id = $1
        ORDER BY p.price_amount ASC;
    """, dna_id)

    print(f"Total Men's Aventus price rows in DB: {len(rows)}")
    for r in rows:
        print(f"  ${r['price_amount']} | {r['retailer_name']} | {r['source_url']}")

    her_id = "0e5b7c7b-3bf1-424a-9775-65476a6cfd74" # Or by canonical name
    her_rows = await conn.fetch("""
        SELECT 
          p.price_observation_id,
          p.price_amount,
          p.currency_code,
          p.source_url,
          r.name as retailer_name
        FROM fragrance_dna d
        JOIN fragrance_line l ON d.dna_id = l.dna_id
        JOIN fragrance_product fp ON l.line_id = fp.line_id
        JOIN product_variant v ON fp.product_id = v.product_id
        JOIN price_observation p ON v.variant_id = p.variant_id
        LEFT JOIN retailer r ON p.retailer_id = r.retailer_id
        WHERE d.canonical_name = 'Aventus for Her'
        ORDER BY p.price_amount ASC;
    """)
    print(f"\nTotal Women's Aventus for Her price rows in DB: {len(her_rows)}")
    for r in her_rows:
        print(f"  ${r['price_amount']} | {r['retailer_name']} | {r['source_url']}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
