import asyncio
import os
import sys
import uuid
import re
from typing import List, Tuple
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")
import asyncpg
from scripts.verify_fragrance_list import FRAGRANCE_LIST

RETAILER_BRANDS_TO_PURGE = [
    "Shop Aromatix", "ANAU STORE", "Lrlux.com", "Fragrancebuy.ca",
    "Aroma Concepts", "Aroma Concepts LLC", "Beautyencounter.com",
    "Jomashop.com", "Fragrancex.com", "Maxaroma.com",
    "Fragrancenet.com", "Perfumania.com", "Aurafragrance.com", "Reblscents.com"
]

def normalize_key(text_val: str) -> str:
    if not text_val:
        return "unknown"
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text_val.strip().lower()).strip("_")
    return cleaned if cleaned else "unknown"

async def run_repair():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set!")
        sys.exit(1)
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    if "sslmode=" not in db_url and "ssl=" not in db_url:
        db_url += "?sslmode=require"

    conn = await asyncpg.connect(db_url)
    try:
        print("=" * 70)
        print("STEP 1: PURGING JUNK RETAILER BRAND RECORDS & CORRUPTED DNAS")
        print("=" * 70)

        # 1. Identify retailer brands
        r_brands = await conn.fetch("""
            SELECT brand_id, name, normalized_name FROM brand
            WHERE name = ANY($1::text[])
               OR name ILIKE '%.com%'
               OR name ILIKE '%.ca%'
        """, RETAILER_BRANDS_TO_PURGE)
        
        r_brand_ids = [b["brand_id"] for b in r_brands]
        print(f"Found {len(r_brand_ids)} retailer brands to purge: {[b['name'] for b in r_brands]}")

        # 2. Identify junk DNAs (under retailer brands OR starting with !, $, Sale price, etc.)
        junk_dnas = await conn.fetch("""
            SELECT dna_id, canonical_name FROM fragrance_dna
            WHERE origin_brand_id = ANY($1::uuid[])
               OR canonical_name ILIKE '!%'
               OR canonical_name ILIKE '$%'
               OR canonical_name ILIKE 'Sale price%'
               OR canonical_name ILIKE '%Regular price%'
               OR canonical_name ILIKE '%Price range%'
               OR canonical_name ILIKE '%CAD%'
               OR canonical_name ILIKE '%USD%'
               OR canonical_name ILIKE '%http%'
               OR canonical_name ILIKE '%[%'
               OR canonical_name ILIKE '%Free Shipping%'
        """, r_brand_ids)
        junk_dna_ids = [d["dna_id"] for d in junk_dnas]
        print(f"Found {len(junk_dna_ids)} junk FragranceDNA records to remove.")

        if junk_dna_ids:
            # Delete PriceObservations for these DNAs
            del_obs = await conn.execute("""
                DELETE FROM price_observation
                WHERE variant_id IN (
                    SELECT v.variant_id FROM product_variant v
                    JOIN fragrance_product p ON v.product_id = p.product_id
                    JOIN fragrance_line l ON p.line_id = l.line_id
                    WHERE l.dna_id = ANY($1::uuid[])
                )
            """, junk_dna_ids)
            print(f"  Deleted price observations for junk DNAs: {del_obs}")

            # Delete relationships where source or target is junk
            del_rels = await conn.execute("""
                DELETE FROM dna_relationship
                WHERE source_dna_id = ANY($1::uuid[]) OR target_dna_id = ANY($1::uuid[])
            """, junk_dna_ids)
            print(f"  Deleted relationships for junk DNAs: {del_rels}")

            # Delete product variants
            del_vars = await conn.execute("""
                DELETE FROM product_variant
                WHERE product_id IN (
                    SELECT p.product_id FROM fragrance_product p
                    JOIN fragrance_line l ON p.line_id = l.line_id
                    WHERE l.dna_id = ANY($1::uuid[])
                )
            """, junk_dna_ids)
            print(f"  Deleted product variants for junk DNAs: {del_vars}")

            # Delete products
            del_prods = await conn.execute("""
                DELETE FROM fragrance_product
                WHERE line_id IN (
                    SELECT l.line_id FROM fragrance_line l
                    WHERE l.dna_id = ANY($1::uuid[])
                )
            """, junk_dna_ids)
            print(f"  Deleted fragrance products for junk DNAs: {del_prods}")

            # Delete lines
            del_lines = await conn.execute("""
                DELETE FROM fragrance_line
                WHERE dna_id = ANY($1::uuid[])
            """, junk_dna_ids)
            print(f"  Deleted fragrance lines for junk DNAs: {del_lines}")

            # Delete DNAs
            del_dnas = await conn.execute("""
                DELETE FROM fragrance_dna
                WHERE dna_id = ANY($1::uuid[])
            """, junk_dna_ids)
            print(f"  Deleted junk fragrance DNAs: {del_dnas}")

        # Delete any remaining retailer brand lines/products
        if r_brand_ids:
            await conn.execute("""
                DELETE FROM fragrance_line WHERE brand_id = ANY($1::uuid[])
            """, r_brand_ids)
            del_b = await conn.execute("""
                DELETE FROM brand WHERE brand_id = ANY($1::uuid[])
            """, r_brand_ids)
            print(f"  Deleted retailer brands from brand table: {del_b}")

        print("\n" + "=" * 70)
        print("STEP 2: ENSURING ALL 50 CANONICAL FRAGRANCES EXIST WITH REAL BRANDS")
        print("=" * 70)

        for idx, (fname, bname) in enumerate(FRAGRANCE_LIST, 1):
            b_norm = normalize_key(bname)
            f_norm = normalize_key(fname)

            # 1. Upsert Brand
            brand_id = await conn.fetchval("""
                INSERT INTO brand (brand_id, name, normalized_name, created_at, updated_at)
                VALUES ($1, $2, $3, NOW(), NOW())
                ON CONFLICT (normalized_name) DO UPDATE SET name = EXCLUDED.name, updated_at = NOW()
                RETURNING brand_id;
            """, uuid.uuid4(), bname, b_norm)

            # 2. Check if DNA already exists under this brand or generally
            existing_dna = await conn.fetchrow("""
                SELECT dna_id, origin_brand_id FROM fragrance_dna
                WHERE origin_brand_id = $1 AND (normalized_name = $2 OR canonical_name ILIKE $3)
                LIMIT 1;
            """, brand_id, f_norm, fname)

            if not existing_dna:
                # Check if exists with different brand or name match
                existing_dna = await conn.fetchrow("""
                    SELECT dna_id, origin_brand_id FROM fragrance_dna
                    WHERE normalized_name = $1 OR canonical_name ILIKE $2
                    LIMIT 1;
                """, f_norm, fname)

            if existing_dna:
                dna_id = existing_dna["dna_id"]
                # Ensure it points to the genuine brand and is marked original
                await conn.execute("""
                    UPDATE fragrance_dna
                    SET origin_brand_id = $1, canonical_name = $2, is_dupe = false, updated_at = NOW()
                    WHERE dna_id = $3;
                """, brand_id, fname, dna_id)
                print(f"  [{idx:02d}] Updated DNA: {bname} - {fname}")
            else:
                dna_id = await conn.fetchval("""
                    INSERT INTO fragrance_dna (
                        dna_id, canonical_name, normalized_name, sort_key, origin_brand_id,
                        market_segment, is_original_dna, is_dupe, created_at, updated_at
                    )
                    VALUES ($1, $2, $3, $2, $4, 'designer', true, false, NOW(), NOW())
                    RETURNING dna_id;
                """, uuid.uuid4(), fname, f_norm, brand_id)
                print(f"  [{idx:02d}] Inserted new DNA: {bname} - {fname}")

            # 3. Ensure Line
            line_id = await conn.fetchval("""
                SELECT line_id FROM fragrance_line
                WHERE dna_id = $1 LIMIT 1;
            """, dna_id)
            if not line_id:
                line_norm = f"{b_norm}_{f_norm}_line"
                line_id = await conn.fetchval("""
                    INSERT INTO fragrance_line (line_id, brand_id, dna_id, name, normalized_name, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                    ON CONFLICT (brand_id, normalized_name) DO UPDATE SET dna_id = EXCLUDED.dna_id
                    RETURNING line_id;
                """, uuid.uuid4(), brand_id, dna_id, fname, line_norm)

            # 4. Ensure Product
            product_id = await conn.fetchval("""
                SELECT product_id FROM fragrance_product
                WHERE line_id = $1 LIMIT 1;
            """, line_id)
            if not product_id:
                product_id = await conn.fetchval("""
                    INSERT INTO fragrance_product (product_id, line_id, formulation_version, is_limited_edition, is_active, created_at, updated_at)
                    VALUES ($1, $2, 'original', false, true, NOW(), NOW())
                    RETURNING product_id;
                """, uuid.uuid4(), line_id)

            # 5. Ensure ProductVariant (100ml spray)
            variant_id = await conn.fetchval("""
                SELECT variant_id FROM product_variant
                WHERE product_id = $1 LIMIT 1;
            """, product_id)
            if not variant_id:
                await conn.execute("""
                    INSERT INTO product_variant (variant_id, product_id, volume_ml, package_type, is_refill, is_active)
                    VALUES ($1, $2, 100.0, 'spray', false, true);
                """, uuid.uuid4(), product_id)

        print("\n" + "=" * 70)
        print("STEP 3: ENSURING ALL CATALOG FRAGRANCES HAVE A PRODUCT & VARIANT")
        print("=" * 70)
        # Find all DNAs without a line/product/variant
        orphan_dnas = await conn.fetch("""
            SELECT d.dna_id, d.canonical_name, d.normalized_name, d.origin_brand_id
            FROM fragrance_dna d
            WHERE NOT EXISTS (
                SELECT 1 FROM fragrance_line l
                JOIN fragrance_product p ON p.line_id = l.line_id
                JOIN product_variant v ON v.product_id = p.product_id
                WHERE l.dna_id = d.dna_id
            )
        """)
        print(f"Found {len(orphan_dnas)} fragrances without variants. Creating lines, products & 100ml variants...")

        for d in orphan_dnas:
            d_id = d["dna_id"]
            d_name = d["canonical_name"]
            d_norm = d["normalized_name"]
            b_id = d["origin_brand_id"]
            if not b_id:
                # Assign default brand
                b_id = await conn.fetchval("SELECT brand_id FROM brand LIMIT 1")
                await conn.execute("UPDATE fragrance_dna SET origin_brand_id = $1 WHERE dna_id = $2", b_id, d_id)

            # Check line
            l_id = await conn.fetchval("SELECT line_id FROM fragrance_line WHERE dna_id = $1 LIMIT 1", d_id)
            if not l_id:
                l_norm = f"{d_norm}_{uuid.uuid4().hex[:6]}"
                l_id = await conn.fetchval("""
                    INSERT INTO fragrance_line (line_id, brand_id, dna_id, name, normalized_name, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, NOW(), NOW())
                    RETURNING line_id;
                """, uuid.uuid4(), b_id, d_id, d_name, l_norm)

            # Check product
            p_id = await conn.fetchval("SELECT product_id FROM fragrance_product WHERE line_id = $1 LIMIT 1", l_id)
            if not p_id:
                p_id = await conn.fetchval("""
                    INSERT INTO fragrance_product (product_id, line_id, formulation_version, is_limited_edition, is_active, created_at, updated_at)
                    VALUES ($1, $2, 'original', false, true, NOW(), NOW())
                    RETURNING product_id;
                """, uuid.uuid4(), l_id)

            # Check variant
            v_id = await conn.fetchval("SELECT variant_id FROM product_variant WHERE product_id = $1 LIMIT 1", p_id)
            if not v_id:
                await conn.execute("""
                    INSERT INTO product_variant (variant_id, product_id, volume_ml, package_type, is_refill, is_active)
                    VALUES ($1, $2, 100.0, 'spray', false, true);
                """, uuid.uuid4(), p_id)

        print(f"All {len(orphan_dnas)} fragrances now have complete Line -> Product -> Variant hierarchies!")

        print("\n" + "=" * 70)
        print("DATABASE CATALOG CLEANUP & SEEDING COMPLETED SUCCESSFULLY")
        print("=" * 70)

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_repair())
