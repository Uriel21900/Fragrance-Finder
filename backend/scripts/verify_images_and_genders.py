import asyncio
import os
import sys
import asyncpg
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL missing")
        return

    conn = await asyncpg.connect(db_url)

    print("=== CHECKING GENDER PAIRS AND BOTTLE IMAGES ===")
    pairs_to_check = [
        "Aventus",
        "Light Blue",
        "Acqua di Gi",
        "Eros",
        "Spicebomb",
        "Flowerbomb",
        "Bad Boy",
        "Good Girl",
        "1 Million",
        "Lady Million",
        "Le Male",
        "La Belle",
        "Sauvage",
        "Miss Dior",
        "J'adore",
        "Yara",
        "Oud for Glory",
    ]

    for name_part in pairs_to_check:
        rows = await conn.fetch("""
            SELECT d.dna_id, d.canonical_name, b.name as brand_name, d.gender, d.image_url,
                   COUNT(p.price_observation_id) as price_count,
                   MIN(p.price_amount) as min_price
            FROM fragrance_dna d
            LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
            LEFT JOIN fragrance_line l ON d.dna_id = l.dna_id
            LEFT JOIN fragrance_product fp ON l.line_id = fp.line_id
            LEFT JOIN product_variant pv ON fp.product_id = pv.product_id
            LEFT JOIN price_observation p ON pv.variant_id = p.variant_id
            WHERE d.canonical_name ILIKE $1
            GROUP BY d.dna_id, d.canonical_name, b.name, d.gender, d.image_url
            ORDER BY d.canonical_name;
        """, f"%{name_part}%")

        print(f"\n--- Matches for '{name_part}' ---")
        for r in rows:
            print(f"  [{r['gender'] or 'N/A'}] {r['brand_name']} - {r['canonical_name']}")
            print(f"      Image: {r['image_url']}")
            print(f"      Prices: {r['price_count']} (Min: ${r['min_price'] if r['min_price'] else 'N/A'})")

    print("\n=== TOTAL CATALOG SUMMARY ===")
    stats = await conn.fetchrow("""
        SELECT 
            COUNT(*) as total,
            COUNT(image_url) as with_image,
            COUNT(CASE WHEN image_url LIKE '/images/%' THEN 1 END) as local_images,
            COUNT(CASE WHEN image_url LIKE '%cdn.shopify.com%' THEN 1 END) as shopify_images,
            COUNT(CASE WHEN image_url LIKE '%unsplash%' THEN 1 END) as unsplash_images,
            COUNT(CASE WHEN gender = 'masculine' THEN 1 END) as masculine,
            COUNT(CASE WHEN gender = 'feminine' THEN 1 END) as feminine,
            COUNT(CASE WHEN gender = 'unisex' THEN 1 END) as unisex,
            COUNT(CASE WHEN gender IS NULL THEN 1 END) as null_gender
        FROM fragrance_dna;
    """)
    print(f"Total Fragrances: {stats['total']}")
    print(f"With Image: {stats['with_image']} (Local verified: {stats['local_images']}, Shopify: {stats['shopify_images']}, Unsplash: {stats['unsplash_images']})")
    print(f"Gender breakdown: Masculine={stats['masculine']}, Feminine={stats['feminine']}, Unisex={stats['unisex']}, Undefined={stats['null_gender']}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
