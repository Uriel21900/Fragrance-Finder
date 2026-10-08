import asyncio, os, sys, uuid
from datetime import datetime, timezone
import asyncpg
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8', errors='replace')

load_dotenv("backend/.env")
load_dotenv(".env")

SEED_DATA = [
    # Originals
    {
        "canonical_name": "Apple Brandy on the Rocks",
        "brand_name": "Kilian",
        "segment": "niche",
        "gender": "unisex",
        "year": 2021,
        "is_original": True,
        "is_dupe": False,
        "inspired_by": None,
        "volume_ml": 50,
        "clone_of": None,
        "image_url": "https://www.bykilian.com/media/export/cms/products/1000x1000/kl_sku_N3CM01_1000x1000_0.png"
    },
    {
        "canonical_name": "Torino21",
        "brand_name": "Xerjoff",
        "segment": "niche",
        "gender": "unisex",
        "year": 2021,
        "is_original": True,
        "is_dupe": False,
        "inspired_by": None,
        "volume_ml": 50,
        "clone_of": None,
        "image_url": "https://xerjoff.com/img/cms/Torino21_50ml.png"
    },
    {
        "canonical_name": "MYSLF",
        "brand_name": "Yves Saint Laurent",
        "segment": "designer",
        "gender": "masculine",
        "year": 2023,
        "is_original": True,
        "is_dupe": False,
        "inspired_by": None,
        "volume_ml": 100,
        "clone_of": None,
        "image_url": "https://www.yslbeautyus.com/dw/image/v2/AANG_PRD/on/demandware.static/-/Sites-ysl-master-catalog/default/dwb51a0279/Fragrance/MYSLF/MYSLF_EDP_100ml.jpg"
    },
    {
        "canonical_name": "Le Male Elixir",
        "brand_name": "Jean Paul Gaultier",
        "segment": "designer",
        "gender": "masculine",
        "year": 2023,
        "is_original": True,
        "is_dupe": False,
        "inspired_by": None,
        "volume_ml": 125,
        "clone_of": None,
        "image_url": "https://www.jeanpaulgaultier.com/medias/sys_master/images/images/h80/h9f/9349887754270/le-male-elixir-125ml.png"
    },
    {
        "canonical_name": "Althair",
        "brand_name": "Parfums de Marly",
        "segment": "niche",
        "gender": "masculine",
        "year": 2023,
        "is_original": True,
        "is_dupe": False,
        "inspired_by": None,
        "volume_ml": 125,
        "clone_of": None,
        "image_url": "https://parfums-de-marly.com/cdn/shop/files/ALTHAIR-125ML-PACKSHOT.png"
    },
    {
        "canonical_name": "Stronger With You",
        "brand_name": "Giorgio Armani",
        "segment": "designer",
        "gender": "masculine",
        "year": 2017,
        "is_original": True,
        "is_dupe": False,
        "inspired_by": None,
        "volume_ml": 100,
        "clone_of": None,
        "image_url": "https://www.giorgioarmanibeauty-usa.com/dw/image/v2/AANG_PRD/on/demandware.static/-/Sites-armani-master-catalog/default/dw10d73f1d/Fragrance/Emporio/Stronger-With-You/SWY_100ml.png"
    },
    {
        "canonical_name": "Valentino Uomo Born in Roma",
        "brand_name": "Valentino",
        "segment": "designer",
        "gender": "masculine",
        "year": 2019,
        "is_original": True,
        "is_dupe": False,
        "inspired_by": None,
        "volume_ml": 100,
        "clone_of": None,
        "image_url": "https://www.valentino-beauty.us/dw/image/v2/AANG_PRD/on/demandware.static/-/Sites-valentino-master-catalog/default/dwbe468088/born-in-roma-uomo-100ml.jpg"
    },
    {
        "canonical_name": "Valentino Donna Born in Roma",
        "brand_name": "Valentino",
        "segment": "designer",
        "gender": "feminine",
        "year": 2019,
        "is_original": True,
        "is_dupe": False,
        "inspired_by": None,
        "volume_ml": 100,
        "clone_of": None,
        "image_url": "https://www.valentino-beauty.us/dw/image/v2/AANG_PRD/on/demandware.static/-/Sites-valentino-master-catalog/default/dwcd5f8dbd/born-in-roma-donna-100ml.jpg"
    },
    {
        "canonical_name": "Luna Rossa Ocean",
        "brand_name": "Prada",
        "segment": "designer",
        "gender": "masculine",
        "year": 2021,
        "is_original": True,
        "is_dupe": False,
        "inspired_by": None,
        "volume_ml": 100,
        "clone_of": None,
        "image_url": "https://www.prada-beauty.com/dw/image/v2/BJSQ_PRD/on/demandware.static/-/Sites-prada-master-catalog/default/dwa1f15858/Luna_Rossa_Ocean_100ml.png"
    },
    {
        "canonical_name": "Pacific Chill",
        "brand_name": "Louis Vuitton",
        "segment": "niche",
        "gender": "unisex",
        "year": 2023,
        "is_original": True,
        "is_dupe": False,
        "inspired_by": None,
        "volume_ml": 100,
        "clone_of": None,
        "image_url": "https://us.louisvuitton.com/images/is/image/lv/1/PP_VP_L/louis-vuitton-pacific-chill-perfumes--LP0326_PM2_Front%20view.png"
    },
    {
        "canonical_name": "L'Immensité",
        "brand_name": "Louis Vuitton",
        "segment": "niche",
        "gender": "masculine",
        "year": 2018,
        "is_original": True,
        "is_dupe": False,
        "inspired_by": None,
        "volume_ml": 100,
        "clone_of": None,
        "image_url": "https://us.louisvuitton.com/images/is/image/lv/1/PP_VP_L/louis-vuitton-l-immensite-perfumes--LP0052_PM2_Front%20view.png"
    },
    {
        "canonical_name": "Ani",
        "brand_name": "Nishane",
        "segment": "niche",
        "gender": "unisex",
        "year": 2019,
        "is_original": True,
        "is_dupe": False,
        "inspired_by": None,
        "volume_ml": 100,
        "clone_of": None,
        "image_url": "https://nishane.com/cdn/shop/files/ANI-100ml-Extrait-de-Parfum.png"
    },
    {
        "canonical_name": "Paragon",
        "brand_name": "Initio Parfums Prives",
        "segment": "niche",
        "gender": "unisex",
        "year": 2022,
        "is_original": True,
        "is_dupe": False,
        "inspired_by": None,
        "volume_ml": 90,
        "clone_of": None,
        "image_url": "https://initioparfums.com/cdn/shop/files/PARAGON-90ML.png"
    },
    {
        "canonical_name": "Gris Charnel",
        "brand_name": "BDK Parfums",
        "segment": "niche",
        "gender": "unisex",
        "year": 2019,
        "is_original": True,
        "is_dupe": False,
        "inspired_by": None,
        "volume_ml": 100,
        "clone_of": None,
        "image_url": "https://bdkparfums.com/cdn/shop/products/Gris-Charnel-100ml.png"
    },
    {
        "canonical_name": "Hawas for Men",
        "brand_name": "Rasasi",
        "segment": "designer",
        "gender": "masculine",
        "year": 2015,
        "is_original": True,
        "is_dupe": False,
        "inspired_by": None,
        "volume_ml": 100,
        "clone_of": None,
        "image_url": "https://cdn.shopify.com/s/files/1/0552/4167/0713/files/hawas_men_100ml.png"
    },
    # Famous Clones
    {
        "canonical_name": "Liquid Brun",
        "brand_name": "French Avenue",
        "segment": "clone",
        "gender": "unisex",
        "year": 2024,
        "is_original": False,
        "is_dupe": True,
        "inspired_by": "Parfums de Marly Althair",
        "volume_ml": 100,
        "clone_of": "Althair",
        "image_url": "https://cdn.shopify.com/s/files/1/0552/4167/0713/files/Liquid_Brun_French_Avenue.png"
    },
    {
        "canonical_name": "Spectre Ghost",
        "brand_name": "French Avenue",
        "segment": "clone",
        "gender": "unisex",
        "year": 2023,
        "is_original": False,
        "is_dupe": True,
        "inspired_by": "Nishane Ani",
        "volume_ml": 100,
        "clone_of": "Ani",
        "image_url": "https://cdn.shopify.com/s/files/1/0552/4167/0713/files/Spectre_Ghost.png"
    },
    {
        "canonical_name": "Vintage Radio",
        "brand_name": "Lattafa",
        "segment": "clone",
        "gender": "unisex",
        "year": 2023,
        "is_original": False,
        "is_dupe": True,
        "inspired_by": "Initio Paragon",
        "volume_ml": 100,
        "clone_of": "Paragon",
        "image_url": "https://cdn.shopify.com/s/files/1/0552/4167/0713/files/Vintage_Radio_Lattafa.png"
    },
    {
        "canonical_name": "Liam Grey",
        "brand_name": "Lattafa",
        "segment": "clone",
        "gender": "unisex",
        "year": 2023,
        "is_original": False,
        "is_dupe": True,
        "inspired_by": "BDK Parfums Gris Charnel",
        "volume_ml": 100,
        "clone_of": "Gris Charnel",
        "image_url": "https://cdn.shopify.com/s/files/1/0552/4167/0713/files/Liam_Grey_Lattafa.png"
    }
]

async def seed():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is required.")
    conn = await asyncpg.connect(db_url)
    print("Connected to database.")

    dna_cache = {}

    for item in SEED_DATA:
        # 1. Resolve brand
        brand_row = await conn.fetchrow("SELECT brand_id, name FROM brand WHERE name ILIKE $1", item["brand_name"])
        if not brand_row:
            print(f"Brand not found for {item['brand_name']}, creating...")
            brand_id = uuid.uuid4()
            norm_b = item["brand_name"].lower().replace(" ", "_")
            await conn.execute("""
                INSERT INTO brand (brand_id, name, normalized_name, created_at, updated_at)
                VALUES ($1, $2, $3, NOW(), NOW())
            """, brand_id, item["brand_name"], norm_b)
        else:
            brand_id = brand_row["brand_id"]

        # 2. Check if DNA already exists
        dna_row = await conn.fetchrow("""
            SELECT dna_id, canonical_name FROM fragrance_dna 
            WHERE canonical_name ILIKE $1 AND origin_brand_id = $2
        """, item["canonical_name"], brand_id)

        if not dna_row:
            dna_id = uuid.uuid4()
            norm_name = item["canonical_name"].lower().replace(" ", "_")
            await conn.execute("""
                INSERT INTO fragrance_dna (
                    dna_id, canonical_name, normalized_name, origin_brand_id,
                    market_segment, first_release_year, is_original_dna, is_dupe,
                    inspired_by, image_url, gender, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5::fragrance_market_segment, $6, $7, $8, $9, $10, $11, NOW(), NOW())
            """, dna_id, item["canonical_name"], norm_name, brand_id,
                 item["segment"], item["year"], item["is_original"], item["is_dupe"],
                 item["inspired_by"], item["image_url"], item["gender"])
            print(f"Created DNA: {item['brand_name']} - {item['canonical_name']} ({dna_id})")
        else:
            dna_id = dna_row["dna_id"]
            # update image_url or gender if null
            await conn.execute("""
                UPDATE fragrance_dna 
                SET image_url = COALESCE(image_url, $1),
                    gender = COALESCE(gender, $2),
                    is_original_dna = $3,
                    is_dupe = $4,
                    inspired_by = COALESCE(inspired_by, $5)
                WHERE dna_id = $6
            """, item["image_url"], item["gender"], item["is_original"], item["is_dupe"], item["inspired_by"], dna_id)
            print(f"Updated existing DNA: {item['brand_name']} - {item['canonical_name']} ({dna_id})")

        dna_cache[item["canonical_name"]] = dna_id

        # 3. Ensure Line exists
        line_row = await conn.fetchrow("""
            SELECT line_id FROM fragrance_line WHERE dna_id = $1
        """, dna_id)
        if not line_row:
            line_id = uuid.uuid4()
            await conn.execute("""
                INSERT INTO fragrance_line (
                    line_id, brand_id, dna_id, name, normalized_name,
                    release_year, marketing_gender, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7::fragrance_gender_marketing, NOW(), NOW())
            """, line_id, brand_id, dna_id, item["canonical_name"], item["canonical_name"].lower().replace(" ", "_"),
                 item["year"], item["gender"])
        else:
            line_id = line_row["line_id"]

        # 4. Ensure Product exists
        prod_row = await conn.fetchrow("""
            SELECT product_id FROM fragrance_product WHERE line_id = $1
        """, line_id)
        if not prod_row:
            prod_id = uuid.uuid4()
            await conn.execute("""
                INSERT INTO fragrance_product (
                    product_id, line_id, formulation_version, release_year,
                    is_limited_edition, is_active, created_at, updated_at
                ) VALUES ($1, $2, 'original', $3, false, true, NOW(), NOW())
            """, prod_id, line_id, item["year"])
        else:
            prod_id = prod_row["product_id"]

        # 5. Ensure Variant exists
        var_row = await conn.fetchrow("""
            SELECT variant_id FROM product_variant WHERE product_id = $1
        """, prod_id)
        if not var_row:
            var_id = uuid.uuid4()
            await conn.execute("""
                INSERT INTO product_variant (
                    variant_id, product_id, volume_ml, package_type, is_refill, is_active
                ) VALUES ($1, $2, $3, 'bottle', false, true)
            """, var_id, prod_id, item["volume_ml"])
            print(f"  Created variant {item['volume_ml']}ml for {item['canonical_name']}")

    # 6. Wire Clone relationships
    print("\nWiring Clone Relationships...")
    for item in SEED_DATA:
        if item.get("clone_of"):
            target_name = item["clone_of"]
            target_dna_id = dna_cache.get(target_name)
            source_dna_id = dna_cache.get(item["canonical_name"])

            if not target_dna_id:
                # Query target from DB
                t_row = await conn.fetchrow("SELECT dna_id FROM fragrance_dna WHERE canonical_name ILIKE $1", f"%{target_name}%")
                if t_row:
                    target_dna_id = t_row["dna_id"]

            if source_dna_id and target_dna_id:
                rel_exists = await conn.fetchval("""
                    SELECT count(*) FROM dna_relationship 
                    WHERE source_dna_id = $1 AND target_dna_id = $2
                """, source_dna_id, target_dna_id)
                if not rel_exists:
                    await conn.execute("""
                        INSERT INTO dna_relationship (
                            dna_relationship_id, source_dna_id, target_dna_id,
                            relationship_type, similarity_score, confidence_score,
                            created_at, updated_at
                        ) VALUES ($1, $2, $3, 'clone_of'::relation_type, 0.95, 0.95, NOW(), NOW())
                    """, uuid.uuid4(), source_dna_id, target_dna_id)
                    print(f"  Linked: {item['canonical_name']} -> clone_of -> {target_name}")

    print("\nSeeding finished successfully!")
    await conn.close()

if __name__ == '__main__':
    asyncio.run(seed())
