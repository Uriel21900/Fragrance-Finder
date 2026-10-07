import asyncio, os, sys
import asyncpg
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")
if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8')

async def main():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    
    total_dna = await conn.fetchval("SELECT count(*) FROM fragrance_dna;")
    original_dna = await conn.fetchval("SELECT count(*) FROM fragrance_dna WHERE is_original_dna = true;")
    clone_dna = await conn.fetchval("SELECT count(*) FROM fragrance_dna WHERE is_dupe = true;")
    total_prices = await conn.fetchval("SELECT count(*) FROM price_observation;")
    
    dna_with_prices = await conn.fetchval("""
        SELECT count(DISTINCT l.dna_id)
        FROM fragrance_line l
        JOIN fragrance_product fp ON l.line_id = fp.line_id
        JOIN product_variant pv ON fp.product_id = pv.product_id
        JOIN price_observation p ON pv.variant_id = p.variant_id;
    """)
    
    print("=== CATALOG AUDIT ===")
    print(f"Total Fragrance DNA in database: {total_dna}")
    print(f"  Original/Designer/Niche DNA: {original_dna}")
    print(f"  Clone/Dupe DNA: {clone_dna}")
    print(f"Total price observations: {total_prices}")
    print(f"Total Fragrances with AT LEAST 1 price: {dna_with_prices}")
    print(f"Total Fragrances with 0 prices: {total_dna - dna_with_prices}")
    
    # Check 50 Canonical Fragrances
    from verify_fragrance_list import FRAGRANCE_LIST
    print(f"\nChecking {len(FRAGRANCE_LIST)} Canonical Fragrances:")
    missing_canonical = []
    canonical_without_prices = []
    canonical_with_prices = []
    
    for item in FRAGRANCE_LIST:
        name, brand = item[0], item[1]
        dna = await conn.fetchrow("""
            SELECT d.dna_id, d.canonical_name, b.name as brand_name
            FROM fragrance_dna d
            LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
            WHERE d.canonical_name ILIKE $1
            LIMIT 1
        """, f"%{name}%")
        
        if not dna:
            missing_canonical.append((name, brand))
        else:
            p_count = await conn.fetchval("""
                SELECT count(*)
                FROM fragrance_line l
                JOIN fragrance_product fp ON l.line_id = fp.line_id
                JOIN product_variant pv ON fp.product_id = pv.product_id
                JOIN price_observation p ON pv.variant_id = p.variant_id
                WHERE l.dna_id = $1
            """, dna['dna_id'])
            
            if p_count == 0:
                canonical_without_prices.append((name, brand, dna['canonical_name']))
            else:
                canonical_with_prices.append((name, brand, p_count))
                
    print(f"  Canonical found with prices: {len(canonical_with_prices)} / {len(FRAGRANCE_LIST)}")
    print(f"  Canonical found with 0 prices: {len(canonical_without_prices)} / {len(FRAGRANCE_LIST)}")
    print(f"  Canonical completely MISSING from DB: {len(missing_canonical)} / {len(FRAGRANCE_LIST)}")
    
    if missing_canonical:
        print("\nMissing Canonical Fragrances:")
        for m in missing_canonical:
            print("    [MISSING]", m)
            
    if canonical_without_prices:
        print("\nCanonical Fragrances with ZERO prices:")
        for c in canonical_without_prices:
            print("    [0 PRICES]", c)

    # Search endpoint audit - check how many fragrances show up on search
    searchable_count = await conn.fetchval("""
        SELECT count(*)
        FROM fragrance_dna d
        LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
        WHERE d.canonical_name IS NOT NULL AND b.name IS NOT NULL;
    """)
    print(f"\nSearchable Fragrance DNAs with Valid Brand: {searchable_count}")

    # Check top fragrances by price counts
    top_fragrances = await conn.fetch("""
        SELECT d.canonical_name, b.name as brand_name, count(p.price_observation_id) as price_count
        FROM fragrance_dna d
        LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
        JOIN fragrance_line l ON d.dna_id = l.dna_id
        JOIN fragrance_product fp ON l.line_id = fp.line_id
        JOIN product_variant pv ON fp.product_id = pv.product_id
        JOIN price_observation p ON pv.variant_id = p.variant_id
        GROUP BY d.canonical_name, b.name
        ORDER BY price_count DESC
        LIMIT 15;
    """)
    print("\nTop 15 Fragrances by Price Observations:")
    for t in top_fragrances:
        print(f"  {t['price_count']:3d} prices | {t['brand_name']} - {t['canonical_name']}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
