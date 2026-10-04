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
        rows = await conn.fetch("""
            SELECT d.dna_id, d.canonical_name, b.name as brand, d.image_url, l.marketing_gender
            FROM fragrance_dna d
            LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
            LEFT JOIN fragrance_line l ON l.dna_id = d.dna_id
            WHERE d.canonical_name ILIKE '%homme%' 
               OR d.canonical_name ILIKE '%femme%'
               OR d.canonical_name ILIKE '% men%'
               OR d.canonical_name ILIKE '%man%'
               OR d.canonical_name ILIKE '%women%'
               OR d.canonical_name ILIKE '%her%'
               OR d.canonical_name ILIKE '%him%'
               OR d.canonical_name ILIKE '%aventus%'
               OR d.canonical_name ILIKE '%sauvage%'
               OR d.canonical_name ILIKE '%light blue%'
               OR d.canonical_name ILIKE '%acqua di gio%'
               OR d.canonical_name ILIKE '%eros%'
               OR d.canonical_name ILIKE '%spicebomb%'
               OR d.canonical_name ILIKE '%flowerbomb%'
               OR d.canonical_name ILIKE '%dior%'
               OR d.canonical_name ILIKE '%chanel%'
               OR d.canonical_name ILIKE '%ysl%'
               OR d.canonical_name ILIKE '%saint laurent%'
            ORDER BY b.name, d.canonical_name
        """)
        print(f"Total matched: {len(rows)}")
        for r in rows:
            img = (r['image_url'][:55] + '...') if r['image_url'] else 'None'
            print(f"{r['brand']} | {r['canonical_name']} | Gender: {r['marketing_gender']} | Img: {img}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
