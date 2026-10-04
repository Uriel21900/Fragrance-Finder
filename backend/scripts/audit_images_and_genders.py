import asyncio
import os
from dotenv import load_dotenv
import asyncpg

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")

async def main():
    db_url = os.getenv("DATABASE_URL")
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    if "sslmode=" not in db_url and "ssl=" not in db_url:
        db_url += "?sslmode=require"

    conn = await asyncpg.connect(db_url)
    try:
        # Check column existence in fragrance_dna
        cols = await conn.fetch("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = 'fragrance_dna'
        """)
        col_names = [r['column_name'] for r in cols]
        print("fragrance_dna columns:", col_names)
        
        # Check all distinct brand names
        brands = await conn.fetch("SELECT brand_id, name FROM brand ORDER BY name")
        print(f"Total brands: {len(brands)}")

        # Check total DNAs
        total_dnas = await conn.fetchval("SELECT count(*) FROM fragrance_dna")
        print(f"Total DNAs: {total_dnas}")

        # Check fragrances where image_url is unsplash
        unsplash_dnas = await conn.fetch("""
            SELECT d.dna_id, d.canonical_name, b.name as brand_name, d.image_url
            FROM fragrance_dna d
            LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
            WHERE d.image_url ILIKE '%unsplash%'
            ORDER BY b.name, d.canonical_name
            LIMIT 40
        """)
        print(f"\nSample of {len(unsplash_dnas)} Unsplash fragrances:")
        for r in unsplash_dnas[:20]:
            print(f"  {r['brand_name']} - {r['canonical_name']} -> {r['image_url'][:50]}...")

        # Check fragrances where image_url is NULL
        null_dnas = await conn.fetch("""
            SELECT d.dna_id, d.canonical_name, b.name as brand_name
            FROM fragrance_dna d
            LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
            WHERE d.image_url IS NULL OR d.image_url = ''
            ORDER BY b.name, d.canonical_name
        """)
        print(f"\nTotal Null image fragrances: {len(null_dnas)}")
        for r in null_dnas[:30]:
            print(f"  {r['brand_name']} - {r['canonical_name']}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
