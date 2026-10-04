import asyncio, os, sys, asyncpg
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")

async def main():
    sys.stdout.reconfigure(encoding='utf-8')
    db_url = os.getenv("DATABASE_URL")
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    if "sslmode=" not in db_url and "ssl=" not in db_url:
        db_url += "?sslmode=require"

    conn = await asyncpg.connect(db_url)

    # 1. Total breakdown of image sources
    stats = await conn.fetch("""
        SELECT 
            CASE 
                WHEN image_url ILIKE '%unsplash%' THEN 'Unsplash'
                WHEN image_url ILIKE '/images/%' THEN 'Local /images/'
                WHEN image_url ILIKE '%cdn.shopify.com%' THEN 'Shopify CDN'
                WHEN image_url IS NULL OR image_url = '' THEN 'Null/Empty'
                ELSE 'Other CDN/URL'
            END as img_source,
            COUNT(*) as cnt
        FROM fragrance_dna
        GROUP BY 1
        ORDER BY cnt DESC;
    """)
    print("=== IMAGE SOURCES BREAKDOWN ===")
    for s in stats:
        print(f"  {s['img_source']}: {s['cnt']}")

    # 2. Gender breakdown in fragrance_line
    line_genders = await conn.fetch("""
        SELECT marketing_gender, COUNT(*) as cnt
        FROM fragrance_line
        GROUP BY 1
        ORDER BY cnt DESC;
    """)
    print("\n=== FRAGRANCE_LINE GENDER BREAKDOWN ===")
    for g in line_genders:
        print(f"  {g['marketing_gender']}: {g['cnt']}")

    # 3. Check popular fragrances (those with price observations)
    popular_dnas = await conn.fetch("""
        SELECT d.dna_id, d.canonical_name, b.name as brand, d.image_url, l.marketing_gender, COUNT(po.price_observation_id) as prices
        FROM fragrance_dna d
        LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
        LEFT JOIN fragrance_line l ON l.dna_id = d.dna_id
        LEFT JOIN fragrance_product fp ON fp.line_id = l.line_id
        LEFT JOIN product_variant pv ON pv.product_id = fp.product_id
        LEFT JOIN price_observation po ON po.variant_id = pv.variant_id
        GROUP BY d.dna_id, d.canonical_name, b.name, d.image_url, l.marketing_gender
        HAVING COUNT(po.price_observation_id) > 0
        ORDER BY prices DESC
        LIMIT 50;
    """)
    print(f"\n=== TOP 50 FRAGRANCES BY PRICE COUNT ===")
    unsplash_in_top = 0
    null_in_top = 0
    for p in popular_dnas:
        img_type = "Local" if (p['image_url'] or '').startswith('/images') else ("Unsplash" if 'unsplash' in (p['image_url'] or '') else ("Shopify" if 'shopify' in (p['image_url'] or '') else "None"))
        if img_type == "Unsplash": unsplash_in_top += 1
        if img_type == "None": null_in_top += 1
        print(f"  [{img_type}] {p['brand']} - {p['canonical_name']} | Gender: {p['marketing_gender']} | Prices: {p['prices']}")
    print(f"Top 50 stats: Unsplash={unsplash_in_top}, Null={null_in_top}")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
