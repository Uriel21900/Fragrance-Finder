import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")
import asyncpg

async def check():
    db_url = os.getenv("DATABASE_URL")
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    if "sslmode=" not in db_url and "ssl=" not in db_url:
        db_url += "?sslmode=require"

    conn = await asyncpg.connect(db_url)
    try:
        count = await conn.fetchval("SELECT count(*) FROM price_observation WHERE observed_at > NOW() - INTERVAL '30 minutes'")
        recent = await conn.fetch("""
            SELECT d.canonical_name, b.name as brand_name, r.name as retailer_name, p.price_amount, p.source_url
            FROM price_observation p
            JOIN product_variant v ON p.variant_id = v.variant_id
            JOIN fragrance_product fp ON v.product_id = fp.product_id
            JOIN fragrance_line fl ON fp.line_id = fl.line_id
            JOIN fragrance_dna d ON fl.dna_id = d.dna_id
            JOIN brand b ON d.origin_brand_id = b.brand_id
            JOIN retailer r ON p.retailer_id = r.retailer_id
            WHERE p.observed_at > NOW() - INTERVAL '30 minutes'
            ORDER BY p.captured_at DESC
            LIMIT 15
        """)
        total_obs = await conn.fetchval("SELECT count(*) FROM price_observation")
        unique_fragrances = await conn.fetchval("""
            SELECT count(DISTINCT fl.dna_id)
            FROM price_observation p
            JOIN product_variant v ON p.variant_id = v.variant_id
            JOIN fragrance_product fp ON v.product_id = fp.product_id
            JOIN fragrance_line fl ON fp.line_id = fl.line_id
        """)
        print(f"Total price observations in table: {total_obs}")
        print(f"Unique fragrances with discounter prices: {unique_fragrances}")
        print(f"Observations recorded in last 30 minutes: {count}")
        for row in recent:
            print(f"  {row['brand_name']} - {row['canonical_name']} -> {row['retailer_name']}: ${row['price_amount']}")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check())
