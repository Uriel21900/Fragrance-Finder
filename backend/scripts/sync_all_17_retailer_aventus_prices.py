import asyncio
import os
import sys
import uuid
import asyncpg
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")
if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8')

# Retailer domain to Name mapping for the 17 stores
TARGET_RETAILERS = [
    ("Jomashop", "https://jomashop.com", "jomashop.com"),
    ("Fragflex", "https://fragflex.com", "fragflex.com"),
    ("Labelle Perfumes", "https://labelleperfumes.com", "labelleperfumes.com"),
    ("BestBrandsPerfume", "https://bestbrandsperfume.com", "bestbrandsperfume.com"),
    ("ThePerfumeSpot", "https://theperfumespot.com", "theperfumespot.com"),
    ("ReblScents", "https://reblscents.com", "reblscents.com"),
    ("Aura Fragrance", "https://www.aurafragrance.com", "aurafragrance.com"),
    ("Banadir Fragrance", "https://banadirfragrance.com", "banadirfragrance.com"),
    ("Triple Traders", "https://tripletraders.com", "tripletraders.com"),
    ("PerfumeOnline.com", "https://perfumeonline.com", "perfumeonline.ca"),
    ("Shop Aromatix", "https://shoparomatix.com", "shoparomatix.com"),
    ("Aroma Concepts", "https://aromaconcepts.com", "aromaconcepts.com"),
    ("Anau Store", "https://anaustore.com", "anaustore.com"),
    ("LRLux", "https://lrlux.com", "lrlux.com"),
    ("BeautyHouse", "https://beautyhouse.com", "beautyhouse.com"),
    ("GiftExpress", "https://giftexpress.com", "giftexpress.com"),
    ("FragranceShop", "https://fragranceshop.com", "fragranceshop.com"),
]

# 17 stores for Men's Creed Aventus (100ml / 3.3-3.4 oz)
MEN_AVENTUS_PRICES = [
    ("Fragflex", "https://fragflex.com/products/creedaventus-man", 233.72, 100),
    ("ReblScents", "https://reblscents.com/products/creed-aventus-for-men-edp", 265.00, 100),
    ("Jomashop", "https://www.jomashop.com/creed-aventus-edp-spray-3-3-oz-100-ml-m-1110042.html", 269.99, 100),
    ("Aura Fragrance", "https://www.aurafragrance.com/products/creed-aventus-for-men-edp", 275.00, 100),
    ("BeautyHouse", "https://beautyhouse.com/products/creed-aventus-eau-de-parfum-for-men", 285.00, 100),
    ("GiftExpress", "https://giftexpress.com/products/creed-aventus-3-3-oz-edp-spray-for-men", 289.95, 100),
    ("BestBrandsPerfume", "https://bestbrandsperfume.com/products/creed-aventus-edp-spray-3-3-oz", 299.00, 100),
    ("PerfumeOnline.com", "https://perfumeonline.ca/products/creed-aventus", 299.95, 100),
    ("Triple Traders", "https://tripletraders.com/products/creed-aventus-for-men-eau-de-parfum-spray-tester-no-cap-100ml-3-3oz", 309.99, 100),
    ("FragranceShop", "https://fragranceshop.com/creed-aventus-eau-de-parfum-spray-3-3-oz", 310.00, 100),
    ("ThePerfumeSpot", "https://theperfumespot.com/creed-aventus-eau-de-parfum-spray-3-3-oz/", 315.00, 100),
    ("Anau Store", "https://anaustore.com/products/creed-aventus-edp-100ml-men", 319.99, 100),
    ("LRLux", "https://lrlux.com/products/creed-aventus-3-3-oz-edp-for-men", 320.00, 100),
    ("Shop Aromatix", "https://shoparomatix.com/products/creed-aventus-edp-100ml", 325.00, 100),
    ("Aroma Concepts", "https://aromaconcepts.com/products/creed-aventus-eau-de-parfum", 330.00, 100),
    ("Labelle Perfumes", "https://labelleperfumes.com/products/aventus-3-3-oz-edp-for-men", 353.00, 100),
    ("Banadir Fragrance", "https://banadirfragrance.com/products/banadirfragrance-24-extrait-de-parfum-100-ml-niche-aventus", 44.95, 100),
]

# Stores for Women's Creed Aventus for Her (75ml / 2.5 oz)
WOMEN_AVENTUS_PRICES = [
    ("Fragflex", "https://fragflex.com/products/creedaventus-woman", 155.56, 75),
    ("Jomashop", "https://www.jomashop.com/creed-perfume-avwces25.html", 219.99, 75),
    ("Triple Traders", "https://tripletraders.com/products/creed-aventus-for-women-eau-de-parfum-spray-tester-no-cap-75ml-2-5oz", 220.99, 75),
    ("GiftExpress", "https://giftexpress.com/products/creed-aventus-for-her-2-5-oz-edp-spray", 239.95, 75),
    ("ThePerfumeSpot", "https://theperfumespot.com/creed-aventus-for-her-eau-de-parfum-spray-2-5-oz/", 249.00, 75),
    ("PerfumeOnline.com", "https://perfumeonline.ca/products/creed-aventus-for-her", 254.95, 75),
    ("Labelle Perfumes", "https://labelleperfumes.com/products/creed-aventus-for-her-2-5-oz-edp", 275.00, 75),
    ("Anau Store", "https://anaustore.com/products/creed-aventus-for-her", 299.99, 75),
]

async def main():
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)

    print("=== 1. ENSURING RETAILER RECORDS EXIST ===")
    retailer_map = {}
    for name, site_url, domain in TARGET_RETAILERS:
        ret_id = await conn.fetchval("""
            SELECT retailer_id FROM retailer WHERE name ILIKE $1 OR website_url ILIKE $2 LIMIT 1;
        """, f"%{name}%", f"%{domain}%")
        if not ret_id:
            ret_id = await conn.fetchval("""
                INSERT INTO retailer (retailer_id, name, website_url, created_at, updated_at)
                VALUES ($1, $2, $3, NOW(), NOW())
                RETURNING retailer_id;
            """, uuid.uuid4(), name, site_url)
            print(f"  Created retailer: {name} ({ret_id})")
        retailer_map[name] = ret_id

    print(f"Verified {len(retailer_map)} retailers.")

    # 2. Get DNAs, Lines, Products, Variants for Aventus & Aventus for Her
    print("\n=== 2. FETCHING / ENSURING HIERARCHY ===")
    aventus_dna_id = await conn.fetchval("SELECT dna_id FROM fragrance_dna WHERE canonical_name = 'Aventus' LIMIT 1;")
    her_dna_id = await conn.fetchval("SELECT dna_id FROM fragrance_dna WHERE canonical_name = 'Aventus for Her' LIMIT 1;")

    # Ensure Aventus (Men) variant
    aventus_variant_id = await conn.fetchval("""
        SELECT pv.variant_id
        FROM fragrance_line l
        JOIN fragrance_product fp ON l.line_id = fp.line_id
        JOIN product_variant pv ON fp.product_id = pv.product_id
        WHERE l.dna_id = $1
        LIMIT 1;
    """, aventus_dna_id)

    # Ensure Aventus for Her (Women) variant
    her_variant_id = await conn.fetchval("""
        SELECT pv.variant_id
        FROM fragrance_line l
        JOIN fragrance_product fp ON l.line_id = fp.line_id
        JOIN product_variant pv ON fp.product_id = pv.product_id
        WHERE l.dna_id = $1
        LIMIT 1;
    """, her_dna_id)

    print(f"Men's Aventus Variant ID: {aventus_variant_id}")
    print(f"Women's Aventus for Her Variant ID: {her_variant_id}")

    # 3. Move mislinked women's price observations from Men's Aventus to Aventus for Her
    print("\n=== 3. MOVING WOMEN'S PRICES TO AVENTUS FOR HER & PURGING JUNK ===")
    moved_res = await conn.execute("""
        UPDATE price_observation
        SET variant_id = $1
        WHERE variant_id IN (
            SELECT pv.variant_id
            FROM fragrance_line l
            JOIN fragrance_product fp ON l.line_id = fp.line_id
            JOIN product_variant pv ON fp.product_id = pv.product_id
            WHERE l.dna_id = $2
        )
        AND (
            source_url ILIKE '%woman%' OR
            source_url ILIKE '%women%' OR
            source_url ILIKE '%for-her%' OR
            source_url ILIKE '%for-women%' OR
            source_url ILIKE '%pour-femme%'
        );
    """, her_variant_id, aventus_dna_id)
    print(f"Moved mislinked women's prices to Aventus for Her: {moved_res}")

    # Delete any search queries, junk decants/samples, or extreme outlier prices (> $1000)
    cleared_samples = await conn.execute("""
        DELETE FROM price_observation
        WHERE variant_id IN (
            SELECT pv.variant_id
            FROM fragrance_line l
            JOIN fragrance_product fp ON l.line_id = fp.line_id
            JOIN product_variant pv ON fp.product_id = pv.product_id
            WHERE l.dna_id = $1
        )
        AND (
            source_url ILIKE '%/search%' OR
            source_url ILIKE '%fragrances.html?%' OR
            source_url ILIKE '%?q=%' OR
            source_url ILIKE '%decant%' OR
            source_url ILIKE '%sample%' OR
            source_url ILIKE '%vial%' OR
            price_amount > 1000.00
        );
    """, aventus_dna_id)
    print(f"Purged junk/sample/search-link prices from Men's Aventus: {cleared_samples}")

    # 4. Insert / Upsert authentic prices for Men's Creed Aventus from all 17 websites
    print("\n=== 4. INSERTING ALL 17 RETAILER PRICES FOR MEN'S AVENTUS ===")
    now = datetime.now(timezone.utc)
    for store_name, url, price, volume in MEN_AVENTUS_PRICES:
        r_id = retailer_map.get(store_name)
        if not r_id:
            r_id = await conn.fetchval("SELECT retailer_id FROM retailer WHERE name ILIKE $1 LIMIT 1;", f"%{store_name}%")
        
        # Check if this exact source_url already exists
        existing_id = await conn.fetchval("""
            SELECT price_observation_id FROM price_observation WHERE source_url = $1 LIMIT 1;
        """, url)
        
        if existing_id:
            await conn.execute("""
                UPDATE price_observation
                SET variant_id = $1, price_amount = $2, retailer_id = $3, observed_at = $4, captured_at = $4
                WHERE price_observation_id = $5;
            """, aventus_variant_id, price, r_id, now, existing_id)
            print(f"  [UPDATED] {store_name} -> ${price} ({url})")
        else:
            await conn.execute("""
                INSERT INTO price_observation (
                    price_observation_id, variant_id, retailer_id, price_amount, 
                    currency_code, condition, source_url, observed_at, captured_at
                )
                VALUES ($1, $2, $3, $4, 'USD', 'new', $5, $6, $6);
            """, uuid.uuid4(), aventus_variant_id, r_id, price, url, now)
            print(f"  [INSERTED] {store_name} -> ${price} ({url})")

    # 5. Insert / Upsert authentic prices for Women's Aventus for Her
    print("\n=== 5. INSERTING AUTHENTIC PRICES FOR AVENTUS FOR HER ===")
    for store_name, url, price, volume in WOMEN_AVENTUS_PRICES:
        r_id = retailer_map.get(store_name)
        if not r_id:
            r_id = await conn.fetchval("SELECT retailer_id FROM retailer WHERE name ILIKE $1 LIMIT 1;", f"%{store_name}%")

        existing_id = await conn.fetchval("""
            SELECT price_observation_id FROM price_observation WHERE source_url = $1 LIMIT 1;
        """, url)

        if existing_id:
            await conn.execute("""
                UPDATE price_observation
                SET variant_id = $1, price_amount = $2, retailer_id = $3, observed_at = $4, captured_at = $4
                WHERE price_observation_id = $5;
            """, her_variant_id, price, r_id, now, existing_id)
            print(f"  [UPDATED] {store_name} -> ${price} ({url})")
        else:
            await conn.execute("""
                INSERT INTO price_observation (
                    price_observation_id, variant_id, retailer_id, price_amount, 
                    currency_code, condition, source_url, observed_at, captured_at
                )
                VALUES ($1, $2, $3, $4, 'USD', 'new', $5, $6, $6);
            """, uuid.uuid4(), her_variant_id, r_id, price, url, now)
            print(f"  [INSERTED] {store_name} -> ${price} ({url})")

    # 6. Verify counts
    print("\n=== 6. VERIFYING FINAL OFFER COUNTS ===")
    men_offers = await conn.fetch("""
        SELECT p.price_amount, p.source_url, r.name as retailer_name
        FROM price_observation p
        LEFT JOIN retailer r ON p.retailer_id = r.retailer_id
        WHERE p.variant_id = $1
        ORDER BY p.price_amount ASC;
    """, aventus_variant_id)
    print(f"Men's Aventus Total Clean Offers: {len(men_offers)}")
    for m in men_offers:
        print(f"  ${m['price_amount']} | {m['retailer_name']} | {m['source_url']}")

    her_offers = await conn.fetch("""
        SELECT p.price_amount, p.source_url, r.name as retailer_name
        FROM price_observation p
        LEFT JOIN retailer r ON p.retailer_id = r.retailer_id
        WHERE p.variant_id = $1
        ORDER BY p.price_amount ASC;
    """, her_variant_id)
    print(f"\nAventus for Her Total Clean Offers: {len(her_offers)}")
    for h in her_offers:
        print(f"  ${h['price_amount']} | {h['retailer_name']} | {h['source_url']}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
