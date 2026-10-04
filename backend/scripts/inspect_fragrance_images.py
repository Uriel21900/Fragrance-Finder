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
        # Check Aventus records specifically
        aventus_rows = await conn.fetch("""
            SELECT d.dna_id, d.canonical_name, b.name as brand_name, d.image_url, l.marketing_gender, d.is_dupe
            FROM fragrance_dna d
            JOIN brand b ON d.origin_brand_id = b.brand_id
            LEFT JOIN fragrance_line l ON l.dna_id = d.dna_id
            WHERE d.canonical_name ILIKE '%Aventus%'
            ORDER BY d.canonical_name
        """)
        print("=== AVENTUS ENTRIES ===")
        for r in aventus_rows:
            print(f"{r['brand_name']} | {r['canonical_name']} | Gender: {r['marketing_gender']} | Dupe: {r['is_dupe']} | Img: {r['image_url']}")

        # Check the 50 canonical fragrances
        CANONICAL_NAMES = [
            'Acqua di Gio', 'Light Blue', 'Bleu de Chanel', 'Sauvage', 'Neroli Portofino',
            'CK One', 'Green Irish Tweed', 'Wood Sage & Sea Salt', 'Millesime Imperial',
            'Artisan Pure', "J'adore", 'Flowerbomb', 'Daisy', 'Bright Crystal',
            'Miss Dior', 'Chloé Eau de Parfum', 'Delina', 'Carnal Flower', 'Blackberry & Bay',
            'Lost Cherry', 'Shalimar', 'Opium', 'Black Orchid', "Angels' Share",
            'Tobacco Vanille', 'Grand Soir', 'Alien', 'Spicebomb', 'Ambre Narguilé',
            "L'Interdit", "Terre d'Hermès", 'Santal 33', 'Encre Noire', 'Wonderwood',
            'Oud Wood', 'Tam Dao', 'Sycomore', 'Greenley', 'Bleecker Street',
            'Fahrenheit', 'Baccarat Rouge 540', 'Angel', 'Black Opium', 'La Vie Est Belle',
            'Hypnotic Poison', 'By the Fireplace', 'Chocolate Greedy', 'Whiff of Waffle Cone',
            'Lira', 'Cheirosa 62', 'Aventus'
        ]
        canonical_rows = await conn.fetch("""
            SELECT d.dna_id, d.canonical_name, b.name as brand_name, d.image_url, l.marketing_gender
            FROM fragrance_dna d
            JOIN brand b ON d.origin_brand_id = b.brand_id
            LEFT JOIN fragrance_line l ON l.dna_id = d.dna_id
            WHERE d.canonical_name = ANY($1::text[])
            ORDER BY b.name, d.canonical_name
        """, CANONICAL_NAMES)
        print("\n=== CANONICAL FRAGRANCES IMAGES & GENDERS ===")
        for r in canonical_rows:
            print(f"{r['brand_name']} | {r['canonical_name']} | Gender: {r['marketing_gender']} | Img: {r['image_url']}")

        # Summary of image types across the DB
        img_stats = await conn.fetch("""
            SELECT 
                COUNT(*) as total,
                COUNT(image_url) as with_img,
                COUNT(CASE WHEN image_url ILIKE '%unsplash%' THEN 1 END) as unsplash_cnt,
                COUNT(CASE WHEN image_url ILIKE '%shopify%' THEN 1 END) as shopify_cnt,
                COUNT(CASE WHEN image_url ILIKE '/images/%' THEN 1 END) as local_cnt,
                COUNT(CASE WHEN image_url IS NULL OR image_url = '' THEN 1 END) as missing_cnt
            FROM fragrance_dna
        """)
        print("\n=== OVERALL IMAGE STATS ===")
        for s in img_stats:
            print(f"Total: {s['total']} | With Image: {s['with_img']} | Unsplash: {s['unsplash_cnt']} | Shopify: {s['shopify_cnt']} | Local /images/: {s['local_cnt']} | Missing: {s['missing_cnt']}")

        # Gender stats
        gender_stats = await conn.fetch("SELECT marketing_gender, count(*) FROM fragrance_line GROUP BY marketing_gender")
        print("\n=== GENDER DISTRIBUTION IN FRAGRANCE_LINE ===")
        for g in gender_stats:
            print(f"  {g['marketing_gender']}: {g['count']}")

        # Check Creed fragrances specifically
        creed_rows = await conn.fetch("""
            SELECT d.dna_id, d.canonical_name, d.image_url, l.marketing_gender
            FROM fragrance_dna d
            JOIN brand b ON d.origin_brand_id = b.brand_id
            LEFT JOIN fragrance_line l ON l.dna_id = d.dna_id
            WHERE b.name ILIKE '%Creed%'
            ORDER BY d.canonical_name
        """)
        print("\n=== ALL CREED FRAGRANCES ===")
        for c in creed_rows:
            print(f"  Creed | {c['canonical_name']} | Gender: {c['marketing_gender']} | Img: {c['image_url']}")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check())
