import asyncio, os, sys
import asyncpg
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8', errors='replace')

load_dotenv('backend/.env')
FALLBACK_URL = 'postgresql://neondb_owner:npg_iN45StWGXmpK@ep-winter-surf-ay718z8s-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require'

SUSPECT_BRANDS = [
    'Aurafragrance.com',
    'Beautyencounter.com',
    'FragFlex',
    'Fragrancebuy.ca',
    'Fragrancenet.com',
    'Fragrancex.com',
    'Jomashop.com',
    'Lrlux.com',
    'Maxaroma.com',
    'Banadirfragrance',
    'Banadir llc',
    'Banadir Fragrance'
]

async def purge():
    db_url = os.getenv("DATABASE_URL") or FALLBACK_URL
    conn = await asyncpg.connect(db_url)
    print("Connected to database.")
    
    # Identify corrupted DNAs
    corrupted_dnas = await conn.fetch('''
        SELECT d.dna_id, d.canonical_name, b.name as brand_name
        FROM fragrance_dna d
        LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
        WHERE b.name = ANY($1::text[])
           OR b.name ILIKE '%.com%' 
           OR b.name ILIKE '%.ca%' 
           OR d.canonical_name LIKE '!%' 
           OR d.canonical_name LIKE '$%' 
           OR d.canonical_name LIKE 'Sale price%' 
           OR d.canonical_name LIKE '%Regular price%' 
           OR d.canonical_name LIKE 'http%'
           OR d.canonical_name ILIKE '%after coupon%'
           OR d.canonical_name ILIKE '%.com%'
           OR d.canonical_name ILIKE 'Decant - %'
           OR d.canonical_name ILIKE 'Special order%'
           OR d.canonical_name ILIKE 'Free Shipping%'
           OR d.canonical_name ILIKE 'Win $500%'
           OR d.canonical_name ILIKE 'Join our Scent%'
           OR d.canonical_name ILIKE 'Gifts Under %'
    ''', SUSPECT_BRANDS)
    
    dna_ids = [r['dna_id'] for r in corrupted_dnas]
    print(f"Identified {len(dna_ids)} corrupted DNAs to purge.")
    
    if not dna_ids:
        print("No corrupted DNAs to purge.")
        await conn.close()
        return

    async with conn.transaction():
        # 1. Fetch lines
        line_ids = [r['line_id'] for r in await conn.fetch('''
            SELECT line_id FROM fragrance_line WHERE dna_id = ANY($1::uuid[])
        ''', dna_ids)]
        print(f"Found {len(line_ids)} associated fragrance_line records.")

        # 2. Fetch products
        product_ids = [r['product_id'] for r in await conn.fetch('''
            SELECT product_id FROM fragrance_product WHERE line_id = ANY($1::uuid[])
        ''', line_ids)]
        print(f"Found {len(product_ids)} associated fragrance_product records.")

        # 3. Fetch variants
        variant_ids = [r['variant_id'] for r in await conn.fetch('''
            SELECT variant_id FROM product_variant WHERE product_id = ANY($1::uuid[])
        ''', product_ids)]
        print(f"Found {len(variant_ids)} associated product_variant records.")

        # 4. Delete price_observation
        p_deleted = await conn.execute('''
            DELETE FROM price_observation WHERE variant_id = ANY($1::uuid[])
        ''', variant_ids)
        print(f"Deleted price observations: {p_deleted}")

        # 5. Delete product_note
        pn_deleted = await conn.execute('''
            DELETE FROM product_note WHERE product_id = ANY($1::uuid[])
        ''', product_ids)
        print(f"Deleted product notes: {pn_deleted}")

        # 6. Delete product_variant
        pv_deleted = await conn.execute('''
            DELETE FROM product_variant WHERE product_id = ANY($1::uuid[])
        ''', product_ids)
        print(f"Deleted product variants: {pv_deleted}")

        # 7. Delete fragrance_product
        fp_deleted = await conn.execute('''
            DELETE FROM fragrance_product WHERE product_id = ANY($1::uuid[])
        ''', product_ids)
        print(f"Deleted fragrance products: {fp_deleted}")

        # 8. Delete fragrance_line
        fl_deleted = await conn.execute('''
            DELETE FROM fragrance_line WHERE line_id = ANY($1::uuid[])
        ''', line_ids)
        print(f"Deleted fragrance lines: {fl_deleted}")

        # 9. Delete dna_relationship
        rel_deleted = await conn.execute('''
            DELETE FROM dna_relationship 
            WHERE source_dna_id = ANY($1::uuid[]) OR target_dna_id = ANY($1::uuid[])
        ''', dna_ids)
        print(f"Deleted dna relationships: {rel_deleted}")

        # 10. Delete fragrance_alert
        alert_deleted = await conn.execute('''
            DELETE FROM fragrance_alert WHERE dna_id = ANY($1::uuid[])
        ''', dna_ids)
        print(f"Deleted fragrance alerts: {alert_deleted}")

        # 11. Delete fragrance_dna
        dna_deleted = await conn.execute('''
            DELETE FROM fragrance_dna WHERE dna_id = ANY($1::uuid[])
        ''', dna_ids)
        print(f"Deleted fragrance DNAs: {dna_deleted}")

        # 12. Delete fake retailer brands if they have no remaining DNAs or lines
        b_deleted = await conn.execute('''
            DELETE FROM brand 
            WHERE (name = ANY($1::text[]) OR name ILIKE '%.com%' OR name ILIKE '%.ca%')
              AND brand_id NOT IN (SELECT origin_brand_id FROM fragrance_dna WHERE origin_brand_id IS NOT NULL)
              AND brand_id NOT IN (SELECT brand_id FROM fragrance_line WHERE brand_id IS NOT NULL)
        ''', SUSPECT_BRANDS)
        print(f"Deleted fake brands: {b_deleted}")

    print("Purge successfully completed and committed!")
    await conn.close()

if __name__ == '__main__':
    asyncio.run(purge())
