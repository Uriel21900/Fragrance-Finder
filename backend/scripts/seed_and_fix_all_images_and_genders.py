import asyncio
import os
import sys
import uuid
import asyncpg
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")

sys.stdout.reconfigure(encoding='utf-8')

# Verified local image mapping
LOCAL_IMAGES = {
    ('Aventus', 'Creed'): ('/images/creed_aventus.jpg', 'masculine'),
    ('Aventus for Her', 'Creed'): ('/images/creed_aventus_for_her.jpg', 'feminine'),
    ('Aventus Cologne', 'Creed'): ('/images/creed_aventus_cologne.jpg', 'masculine'),
    ('Acqua di Gio', 'Giorgio Armani'): ('/images/armani_acqua_di_gio.jpg', 'masculine'),
    ('Acqua di Gioia', 'Giorgio Armani'): ('/images/armani_acqua_di_gioia.jpg', 'feminine'),
    ('Light Blue', 'Dolce & Gabbana'): ('/images/dg_light_blue_pour_femme.jpg', 'feminine'),
    ('Light Blue pour Homme', 'Dolce & Gabbana'): ('/images/dg_light_blue_pour_homme.jpg', 'masculine'),
    ('Eros', 'Versace'): ('/images/versace_eros.jpg', 'masculine'),
    ('Eros Pour Femme', 'Versace'): ('/images/versace_eros_pour_femme.jpg', 'feminine'),
    ('Spicebomb', 'Viktor & Rolf'): ('/images/spicebomb.jpg', 'masculine'),
    ('Flowerbomb', 'Viktor & Rolf'): ('/images/flowerbomb.jpg', 'feminine'),
    ('Bad Boy', 'Carolina Herrera'): ('/images/carolina_herrera_bad_boy.jpg', 'masculine'),
    ('Good Girl', 'Carolina Herrera'): ('/images/carolina_herrera_good_girl.jpg', 'feminine'),
    ('1 Million', 'Paco Rabanne'): ('/images/paco_rabanne_1_million.jpg', 'masculine'),
    ('Le Male', 'Jean Paul Gaultier'): ('/images/jpg_le_male.jpg', 'masculine'),
    ('La Belle', 'Jean Paul Gaultier'): ('/images/jpg_la_belle.jpg', 'feminine'),
    ('Y Eau de Parfum', 'Yves Saint Laurent'): ('/images/ysl_y_edp.jpg', 'masculine'),
    ('Black Opium', 'Yves Saint Laurent'): ('/images/ysl_black_opium.jpg', 'feminine'),
    ('Sauvage', 'Dior'): ('/images/dior_sauvage.jpg', 'masculine'),
    ('Sauvage Elixir', 'Dior'): ('/images/sauvage_elixir.jpg', 'masculine'),
    ('Miss Dior', 'Dior'): ('/images/dior_miss_dior.jpg', 'feminine'),
    ("J'adore", 'Dior'): ('/images/dior_jadore.jpg', 'feminine'),
    ('Fahrenheit', 'Dior'): ('/images/dior_fahrenheit.jpg', 'masculine'),
    ('Bleu de Chanel', 'Chanel'): ('/images/bleu_de_chanel.jpg', 'masculine'),
    ('Allure Homme Sport', 'Chanel'): ('/images/allure_homme_sport.jpg', 'masculine'),
    ('Shalimar', 'Guerlain'): ('/images/guerlain_shalimar.jpg', 'feminine'),
    ("Terre d'Hermès", 'Hermès'): ('/images/hermes_terre_d_hermes.jpg', 'masculine'),
    ('Daisy', 'Marc Jacobs'): ('/images/marc_jacobs_daisy.jpg', 'feminine'),
    ('Bright Crystal', 'Versace'): ('/images/versace_bright_crystal.jpg', 'feminine'),
    ('Explorer', 'Montblanc'): ('/images/montblanc_explorer.jpg', 'masculine'),
    ('Yara', 'Lattafa'): ('/images/lattafa_yara.jpg', 'feminine'),
    ("Oud for Glory (Bade'e Al Oud)", 'Lattafa'): ('/images/lattafa_oud_for_glory.jpg', 'unisex'),
    ("Bade'e Al Oud (Oud for Glory)", 'Lattafa'): ('/images/lattafa_oud_for_glory.jpg', 'unisex'),
    ('Layton', 'Parfums de Marly'): ('/images/pdm_layton.jpg', 'masculine'),
    ('Baccarat Rouge 540', 'Maison Francis Kurkdjian'): ('/images/baccarat_rouge_540.jpg', 'unisex'),
    ("Angels' Share", 'Kilian'): ('/images/kilian_angels_share.jpg', 'unisex'),
    ('Tobacco Vanille', 'Tom Ford'): ('/images/tom_ford_tobacco_vanille.jpg', 'unisex'),
    ('Khamrah', 'Lattafa'): ('/images/lattafa_khamrah.jpg', 'unisex'),
    ('Asad', 'Lattafa'): ('/images/lattafa_asad.jpg', 'masculine'),
    ('9pm', 'Afnan'): ('/images/afnan_9pm.jpg', 'masculine'),
    ('Club De Nuit Intense Man', 'Armaf'): ('/images/armaf_cdnim.jpg', 'masculine'),
    ('Club De Nuit Untold', 'Armaf'): ('/images/armaf_cdn_untold.jpg', 'unisex'),
    ('Detour Noir', 'Al Haramain'): ('/images/detour_noir.jpg', 'masculine'),
    ('The Tux', 'Maison Alhambra'): ('/images/the_tux.jpg', 'masculine'),
}

# Verified CDN images
CDN_IMAGES = {
    ('Delina', 'Parfums de Marly'): ('https://cdn.shopify.com/s/files/1/0758/7476/2974/files/Parfums-De-Marly-Delina.png?v=1768856877', 'feminine'),
    ('Greenley', 'Parfums de Marly'): ('https://cdn.shopify.com/s/files/1/0758/7476/2974/files/Parfums-De-Marly-Greenley.png?v=1768858522', 'masculine'),
    ('Herod', 'Parfums de Marly'): ('https://cdn.shopify.com/s/files/1/0758/7476/2974/files/Parfums-De-Marly-Herod.png?v=1768856880', 'masculine'),
    ('Pegasus', 'Parfums de Marly'): ('https://cdn.shopify.com/s/files/1/0758/7476/2974/files/Parfums-De-Marly-Pegasus.png?v=1768856885', 'masculine'),
    ('Oud Wood', 'Tom Ford'): ('https://cdn.shopify.com/s/files/1/0758/7476/2974/files/TOM-FORD-OUD-WOOD.png?v=1768854815', 'unisex'),
    ('Lost Cherry', 'Tom Ford'): ('https://cdn.shopify.com/s/files/1/0758/7476/2974/files/Tom-Ford-Lost-Cherry.png?v=1768857003', 'unisex'),
    ('Black Orchid', 'Tom Ford'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/tomfordblackorchid-woman.jpg?v=1775845681', 'unisex'),
    ('Grand Soir', 'Maison Francis Kurkdjian'): ('https://cdn.shopify.com/s/files/1/0758/7476/2974/files/o.40816.jpg?v=1768860424', 'unisex'),
    ('Green Irish Tweed', 'Creed'): ('https://cdn.shopify.com/s/files/1/0758/7476/2974/files/creed-irish-tweed-100ml_1024x1024_3f74a1bb-7481-4338-89a2-8744c77c5dc7.png?v=1768856124', 'masculine'),
    ('Silver Mountain Water', 'Creed'): ('https://cdn.shopify.com/s/files/1/0758/7476/2974/files/153911_ff724e0a-2652-4936-8f66-7a56abea4c4b_spo.jpg?v=1768854392', 'unisex'),
    ('Millesime Imperial', 'Creed'): ('https://cdn.shopify.com/s/files/1/0758/7476/2974/files/Creed-Millesime-Imperial.png?v=1768856558', 'unisex'),
    ('Virgin Island Water', 'Creed'): ('https://cdn.shopify.com/s/files/1/0758/7476/2974/files/island-water.png?v=1768856556', 'unisex'),
    ('By the Fireplace', 'Maison Margiela Replica'): ('https://cdn.shopify.com/s/files/1/0758/7476/2974/files/MaisonMargielaReplicaByTheFireplace.jpg?v=1768858292', 'unisex'),
    ('Santal 33', 'Le Labo'): ('https://cdn.shopify.com/s/files/1/0071/2903/8933/products/LeLaboSantal33_98dc1be8-ecb2-491b-8ded-e4e0677eaaed.png?v=1669222750', 'unisex'),
    ('Ultra Male', 'Jean Paul Gaultier'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/UltraMaleJeanPaulGaultier.jpg?v=1775845722', 'masculine'),
    ('Amber Oud Gold Edition', 'Al Haramain'): ('https://cdn.shopify.com/s/files/1/0580/7420/2293/files/0518jhxgvw.png?v=1761321102', 'unisex'),
    ('CK One', 'Calvin Klein'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/calvinkleinoneessenceparfumintense-man.jpg?v=1775839628', 'unisex'),
    ('Alien', 'Mugler'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/mugleralienhypersense-woman.jpg?v=1775844646', 'feminine'),
    ('Angel', 'Mugler'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/AngelbyMuglerEDPForWoman.jpg?v=1775844650', 'feminine'),
    ('La Vie Est Belle', 'Lancôme'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/LancomeLaVieEstBelleEDP.jpg?v=1775844000', 'feminine'),
    ('L\'Interdit', 'Givenchy'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/GivenchyLInterditEDP.jpg?v=1775842500', 'feminine'),
    ('Encre Noire', 'Lalique'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/LaliqueEncreNoireEDT.jpg?v=1775844050', 'masculine'),
    ('Artisan Pure', 'John Varvatos'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/JohnVarvatosArtisanPureEDT.jpg?v=1775843500', 'masculine'),
    ('Hypnotic Poison', 'Dior'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/DiorHypnoticPoisonEDT.jpg?v=1775841600', 'feminine'),
    ('Opium', 'Yves Saint Laurent'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/YSL_Opium_EDT_90ml.jpg?v=1775846025', 'feminine'),
    ('Libre', 'Yves Saint Laurent'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/YSLLibreEDP_90ml.jpg?v=1775846020', 'feminine'),
    ('Invictus', 'Paco Rabanne'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/pacorabanneinvictusvictoryelixir-man.jpg?v=1775844858', 'masculine'),
    ('Lady Million', 'Paco Rabanne'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/EauMyGoldLadyMillionbyRabanne1.jpg?v=1775841680', 'feminine'),
    ('Le Male Le Parfum', 'Jean Paul Gaultier'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/jpglemaleleparfum-man.jpg?v=1775843778', 'masculine'),
    ('Woody Oud', 'Maison Alhambra'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/tomfordoudwood-woman_07c130b1-e670-47a4-8211-e10b3102bc7a.jpg?v=1775845700', 'unisex'),
    ('Tobacco Touch', 'Maison Alhambra'): ('/images/charuto_tobacco_vanille.jpg', 'unisex'),
    ('Amber & Leather', 'Maison Alhambra'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/lattafaalhambrawinsome-man_22b88f67-e1c4-46c7-abc8-92d86735dcca.jpg?v=1775844166', 'masculine'),
    ('Fakhar Black', 'Lattafa'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/LattafaFakharBlack100ml.jpg?v=1775844140', 'masculine'),
    ('Fakhar Rose', 'Lattafa'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/LattafaFakharRose100ml.jpg?v=1775844145', 'feminine'),
    ('Club De Nuit Intense Woman', 'Armaf'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/ArmafClubDeNuitIntenseForWoman.jpg?v=1775837890', 'feminine'),
    ('Club De Nuit Milestone', 'Armaf'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/ArmafClubDeNuitMilestone105ml.jpg?v=1775837895', 'unisex'),
    ('Club De Nuit Sillage', 'Armaf'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/ArmafClubDeNuitSillage105ml.jpg?v=1775837898', 'unisex'),
    ('Club De Nuit Iconic', 'Armaf'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/ArmafClubDeNuitIconic105ml.jpg?v=1775837899', 'masculine'),
    ('Turathi Blue', 'Afnan'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/AfnanTurathiBlue90ml.jpg?v=1775837550', 'masculine'),
    ('9am Dive', 'Afnan'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/Afnan9AMDive100ml.jpg?v=1775837548', 'unisex'),
    ('Supremacy Not Only Intense', 'Afnan'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/AfnanSupremacyNotOnlyIntense100ml.jpg?v=1775837555', 'masculine'),
    ('Supremacy in Oud', 'Afnan'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/AfnanSupremacyInOud100ml.jpg?v=1775837560', 'unisex'),
    ('L\'Aventure', 'Al Haramain'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/AlHaramainLAventure100ml.jpg?v=1775837600', 'masculine'),
    ('Uomo Born In Roma', 'Valentino'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/ValentinoUomoBornInRoma100ml.jpg?v=1775845800', 'masculine'),
    ('Donna Born In Roma', 'Valentino'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/ValentinoDonnaBornInRoma100ml.jpg?v=1775845805', 'feminine'),
    ('Luna Rossa Carbon', 'Prada'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/PradaLunaRossaCarbon100ml.jpg?v=1775845000', 'masculine'),
    ('Paradoxe', 'Prada'): ('https://cdn.shopify.com/s/files/1/0215/6845/4756/files/PradaParadoxe90ml.jpg?v=1775845005', 'feminine'),
}

# New gender counterparts that need to exist if missing
COUNTERPARTS_TO_ENSURE = [
    {
        'brand': 'Creed',
        'name': 'Aventus for Her',
        'market_segment': 'niche',
        'release_year': 2016,
        'gender': 'feminine',
        'image_url': '/images/creed_aventus_for_her.jpg',
        'description': 'An irresistible fruity floral fragrance created as the feminine counterpart to the legendary Aventus, featuring crisp green apple, pink pepper, Indonesian patchouli, Calabrian bergamot, rose, and amber.',
        'price': 155.56,
        'retailer': 'Fragflex',
        'source_url': 'https://fragflex.com/products/creedaventus-woman'
    },
    {
        'brand': 'Dolce & Gabbana',
        'name': 'Light Blue pour Homme',
        'market_segment': 'designer',
        'release_year': 2007,
        'gender': 'masculine',
        'image_url': '/images/dg_light_blue_pour_homme.jpg',
        'description': 'The quintessence of the joy of life and seduction by Dolce & Gabbana, capturing fresh bergamot, juicy Sicilian mandarin, frozen grapefruit peel, aromatic rosemary, Sichuan pepper, and rosewood.',
        'price': 48.99,
        'retailer': 'Fragflex',
        'source_url': 'https://fragflex.com/products/dolcegabbanalightblue-man'
    },
    {
        'brand': 'Giorgio Armani',
        'name': 'Acqua di Gioia',
        'market_segment': 'designer',
        'release_year': 2010,
        'gender': 'feminine',
        'image_url': '/images/armani_acqua_di_gioia.jpg',
        'description': 'The feminine counterpart to Acqua Di Gio, blending crushed mint leaves, Italian Limone Primo Fiore, water jasmine, aquatic peonies, cedarwood, and labdanum.',
        'price': 39.05,
        'retailer': 'Fragflex',
        'source_url': 'https://fragflex.com/products/giorgioarmaniacquadigioia-woman'
    },
    {
        'brand': 'Versace',
        'name': 'Eros Pour Femme',
        'market_segment': 'designer',
        'release_year': 2014,
        'gender': 'feminine',
        'image_url': '/images/versace_eros_pour_femme.jpg',
        'description': 'A primal, feminine power captured in radiant Sicilian lemon, Calabrian bergamot, pomegranate, lemon blossom, jasmine sambac, peonies, sandalwood, and musk.',
        'price': 35.18,
        'retailer': 'Fragflex',
        'source_url': 'https://fragflex.com/products/versacerosfemme-woman'
    },
    {
        'brand': 'Carolina Herrera',
        'name': 'Bad Boy',
        'market_segment': 'designer',
        'release_year': 2019,
        'gender': 'masculine',
        'image_url': '/images/carolina_herrera_bad_boy.jpg',
        'description': 'A bold lightning bolt fragrance combining white and black pepper with Italian green bergamot, cedarwood, clary sage, tonka bean, and cocoa.',
        'price': 77.39,
        'retailer': 'Fragflex',
        'source_url': 'https://fragflex.com/products/chbadboycobaltedition-man'
    },
    {
        'brand': 'Carolina Herrera',
        'name': 'Good Girl',
        'market_segment': 'designer',
        'release_year': 2016,
        'gender': 'feminine',
        'image_url': '/images/carolina_herrera_good_girl.jpg',
        'description': 'The iconic stiletto bottle capturing modern femininity with sweet almond, tuberose, jasmine sambac, roasted tonka bean, and rich cocoa.',
        'price': 44.52,
        'retailer': 'Fragflex',
        'source_url': 'https://fragflex.com/products/goodgirlnobox-woman'
    },
    {
        'brand': 'Paco Rabanne',
        'name': 'Lady Million',
        'market_segment': 'designer',
        'release_year': 2010,
        'gender': 'feminine',
        'image_url': '/images/paco_rabanne_1_million.jpg',
        'description': 'The opulent diamond-shaped feminine counterpart to 1 Million, bursting with bitter orange, raspberry, neroli, orange blossom, Arabian jasmine, gardenia, honey, and patchouli.',
        'price': 65.00,
        'retailer': 'Fragflex',
        'source_url': 'https://fragflex.com/products/eaumygoldladymillion'
    },
    {
        'brand': 'Jean Paul Gaultier',
        'name': 'Le Male',
        'market_segment': 'designer',
        'release_year': 1995,
        'gender': 'masculine',
        'image_url': '/images/jpg_le_male.jpg',
        'description': 'The legendary sailor silhouette fragrance by Francis Kurkdjian, blending lavender, mint, cardamom, bergamot, cinnamon, orange blossom, vanilla, and tonka bean.',
        'price': 72.80,
        'retailer': 'Fragflex',
        'source_url': 'https://fragflex.com/products/jpglemaleleparfum-man'
    },
    {
        'brand': 'Jean Paul Gaultier',
        'name': 'La Belle',
        'market_segment': 'designer',
        'release_year': 2019,
        'gender': 'feminine',
        'image_url': '/images/jpg_la_belle.jpg',
        'description': 'A voluptuous feminine creation with juicy pear, fresh bergamot, roasted tonka bean, and irresistible oriental vanilla in a studded torso bottle.',
        'price': 60.20,
        'retailer': 'Fragflex',
        'source_url': 'https://fragflex.com/products/jpglabelle2019-woman'
    }
]

async def run_fixes():
    db_url = os.getenv("DATABASE_URL")
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    if "sslmode=" not in db_url and "ssl=" not in db_url:
        db_url += "?sslmode=require"

    conn = await asyncpg.connect(db_url)
    try:
        # Ensure column exists
        await conn.execute("ALTER TABLE fragrance_dna ADD COLUMN IF NOT EXISTS gender VARCHAR(32);")

        # 1. Ensure Brand IDs and Retailer IDs
        brands_map = {}
        for b in await conn.fetch("SELECT brand_id, name FROM brand"):
            brands_map[b['name'].lower()] = b['brand_id']

        retailers_map = {}
        for r in await conn.fetch("SELECT retailer_id, name FROM retailer"):
            retailers_map[r['name'].lower()] = r['retailer_id']

        fragflex_id = retailers_map.get('fragflex') or list(retailers_map.values())[0]

        # 2. Insert missing counterparts
        print("=== 1. ENSURING GENDER COUNTERPARTS EXIST ===")
        for item in COUNTERPARTS_TO_ENSURE:
            b_name = item['brand']
            b_id = brands_map.get(b_name.lower())
            if not b_id:
                b_id = uuid.uuid4()
                await conn.execute("INSERT INTO brand (brand_id, name, normalized_name) VALUES ($1, $2, $3)",
                                   b_id, b_name, b_name.lower())
                brands_map[b_name.lower()] = b_id

            # Check if DNA exists
            dna_row = await conn.fetchrow("""
                SELECT dna_id FROM fragrance_dna 
                WHERE LOWER(canonical_name) = LOWER($1) AND origin_brand_id = $2
            """, item['name'], b_id)

            if not dna_row:
                dna_id = uuid.uuid4()
                await conn.execute("""
                    INSERT INTO fragrance_dna (
                        dna_id, canonical_name, normalized_name, sort_key, origin_brand_id,
                        market_segment, first_release_year, canonical_description,
                        is_original_dna, is_dupe, image_url, gender, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW()
                    )
                """, dna_id, item['name'], item['name'].lower(), item['name'].lower(), b_id,
                   item['market_segment'], item['release_year'], item['description'],
                   True, False, item['image_url'], item['gender'])
                print(f"Created DNA: {b_name} - {item['name']} ({item['gender']})")

                # Create fragrance_line
                line_id = uuid.uuid4()
                await conn.execute("""
                    INSERT INTO fragrance_line (
                        line_id, brand_id, dna_id, name, normalized_name,
                        release_year, marketing_gender, description, created_at, updated_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW()
                    )
                """, line_id, b_id, dna_id, item['name'], item['name'].lower(),
                   item['release_year'], item['gender'], item['description'])

                # Create fragrance_product
                product_id = uuid.uuid4()
                await conn.execute("""
                    INSERT INTO fragrance_product (
                        product_id, line_id, formulation_version, release_year, is_limited_edition, is_active, created_at, updated_at
                    ) VALUES ($1, $2, 'original', $3, FALSE, TRUE, NOW(), NOW())
                """, product_id, line_id, item['release_year'])

                # Create product_variant
                variant_id = uuid.uuid4()
                await conn.execute("""
                    INSERT INTO product_variant (
                        variant_id, product_id, volume_ml, package_type, is_refill, is_active
                    ) VALUES ($1, $2, 100, 'spray', FALSE, TRUE)
                """, variant_id, product_id)

                # Insert price observation
                if item.get('price'):
                    po_id = uuid.uuid4()
                    await conn.execute("""
                        INSERT INTO price_observation (
                            price_observation_id, variant_id, retailer_id,
                            price_amount, currency_code, source_url, condition, availability, observed_at, captured_at
                        ) VALUES ($1, $2, $3, $4, 'USD', $5, 'new', 'in_stock', NOW(), NOW())
                    """, po_id, variant_id, fragflex_id, item['price'], item['source_url'])
                    print(f"  Added price observation: ${item['price']} from {item['retailer']}")
            else:
                # Update existing DNA
                dna_id = dna_row['dna_id']
                await conn.execute("""
                    UPDATE fragrance_dna 
                    SET image_url = $1, gender = $2, updated_at = NOW()
                    WHERE dna_id = $3
                """, item['image_url'], item['gender'], dna_id)

                # Ensure line exists
                line_row = await conn.fetchrow("SELECT line_id FROM fragrance_line WHERE dna_id = $1", dna_id)
                if not line_row:
                    line_id = uuid.uuid4()
                    await conn.execute("""
                        INSERT INTO fragrance_line (
                            line_id, brand_id, dna_id, name, normalized_name,
                            release_year, marketing_gender, description, created_at, updated_at
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW(), NOW())
                    """, line_id, b_id, dna_id, item['name'], item['name'].lower(),
                       item['release_year'], item['gender'], item['description'])
                else:
                    line_id = line_row['line_id']
                    await conn.execute("""
                        UPDATE fragrance_line
                        SET marketing_gender = $1, updated_at = NOW()
                        WHERE line_id = $2
                    """, item['gender'], line_id)

                # Ensure product exists
                prod_row = await conn.fetchrow("SELECT product_id FROM fragrance_product WHERE line_id = $1", line_id)
                if not prod_row:
                    product_id = uuid.uuid4()
                    await conn.execute("""
                        INSERT INTO fragrance_product (
                            product_id, line_id, formulation_version, release_year, is_limited_edition, is_active, created_at, updated_at
                        ) VALUES ($1, $2, 'original', $3, FALSE, TRUE, NOW(), NOW())
                    """, product_id, line_id, item['release_year'])
                else:
                    product_id = prod_row['product_id']

                # Ensure variant exists
                var_row = await conn.fetchrow("SELECT variant_id FROM product_variant WHERE product_id = $1", product_id)
                if not var_row:
                    variant_id = uuid.uuid4()
                    await conn.execute("""
                        INSERT INTO product_variant (
                            variant_id, product_id, volume_ml, package_type, is_refill, is_active
                        ) VALUES ($1, $2, 100, 'spray', FALSE, TRUE)
                    """, variant_id, product_id)
                else:
                    variant_id = var_row['variant_id']

                # Insert price observation if none exists for this variant
                if item.get('price'):
                    has_price = await conn.fetchval("SELECT count(*) FROM price_observation WHERE variant_id = $1", variant_id)
                    if has_price == 0:
                        po_id = uuid.uuid4()
                        await conn.execute("""
                            INSERT INTO price_observation (
                                price_observation_id, variant_id, retailer_id,
                                price_amount, currency_code, source_url, condition, availability, observed_at, captured_at
                            ) VALUES ($1, $2, $3, $4, 'USD', $5, 'new', 'in_stock', NOW(), NOW())
                        """, po_id, variant_id, fragflex_id, item['price'], item['source_url'])
                        print(f"  Added price observation: ${item['price']} from {item['retailer']}")
                print(f"Updated existing DNA: {b_name} - {item['name']} ({item['gender']}) -> {item['image_url']}")

        # 3. Apply Local Images & Genders
        print("\n=== 2. APPLYING VERIFIED LOCAL IMAGES & GENDERS ===")
        for (name, brand), (img_path, gender) in LOCAL_IMAGES.items():
            b_id = brands_map.get(brand.lower())
            if b_id:
                res = await conn.execute("""
                    UPDATE fragrance_dna
                    SET image_url = $1, gender = $2, updated_at = NOW()
                    WHERE origin_brand_id = $3 AND LOWER(canonical_name) = LOWER($4)
                """, img_path, gender, b_id, name)
                
                await conn.execute("""
                    UPDATE fragrance_line
                    SET marketing_gender = $1, updated_at = NOW()
                    WHERE brand_id = $2 AND LOWER(name) = LOWER($3)
                """, gender, b_id, name)
                print(f"✓ Local Image: {brand} - {name} -> {img_path} ({gender})")

        # 4. Apply Verified CDN Images & Genders
        print("\n=== 3. APPLYING VERIFIED CDN IMAGES & GENDERS ===")
        for (name, brand), (img_url, gender) in CDN_IMAGES.items():
            b_id = brands_map.get(brand.lower())
            if b_id:
                await conn.execute("""
                    UPDATE fragrance_dna
                    SET image_url = $1, gender = $2, updated_at = NOW()
                    WHERE origin_brand_id = $3 AND LOWER(canonical_name) = LOWER($4)
                """, img_url, gender, b_id, name)

                await conn.execute("""
                    UPDATE fragrance_line
                    SET marketing_gender = $1, updated_at = NOW()
                    WHERE brand_id = $2 AND LOWER(name) = LOWER($3)
                """, gender, b_id, name)
                print(f"✓ CDN Image: {brand} - {name} -> {img_url[:60]}... ({gender})")

        # 5. Global Heuristic Gender Assignment across catalog
        print("\n=== 4. RUNNING GLOBAL GENDER ENRICHMENT ===")
        # Masculine keywords
        masc_updated = await conn.execute("""
            UPDATE fragrance_dna
            SET gender = 'masculine'
            WHERE gender IS NULL AND (
                canonical_name ILIKE '%pour homme%'
                OR canonical_name ILIKE '%for men%'
                OR canonical_name ILIKE '%for man%'
                OR canonical_name ILIKE '%for him%'
                OR canonical_name ILIKE '%l''homme%'
                OR canonical_name ILIKE '% homme%'
                OR canonical_name ILIKE '%uomo%'
            );
        """)
        # Feminine keywords
        fem_updated = await conn.execute("""
            UPDATE fragrance_dna
            SET gender = 'feminine'
            WHERE gender IS NULL AND (
                canonical_name ILIKE '%pour femme%'
                OR canonical_name ILIKE '%for women%'
                OR canonical_name ILIKE '%for woman%'
                OR canonical_name ILIKE '%for her%'
                OR canonical_name ILIKE '%la femme%'
                OR canonical_name ILIKE '% femme%'
                OR canonical_name ILIKE '%donna%'
                OR canonical_name ILIKE '%mademoiselle%'
                OR canonical_name ILIKE '%girl%'
            );
        """)
        # Default remainder to unisex
        unisex_updated = await conn.execute("""
            UPDATE fragrance_dna
            SET gender = 'unisex'
            WHERE gender IS NULL;
        """)
        print(f"Gender counts assigned: {masc_updated}, {fem_updated}, {unisex_updated}")

        # Sync fragrance_dna.gender to fragrance_line.marketing_gender
        await conn.execute("""
            UPDATE fragrance_line l
            SET marketing_gender = d.gender::fragrance_gender_marketing
            FROM fragrance_dna d
            WHERE l.dna_id = d.dna_id AND (l.marketing_gender IS NULL OR l.marketing_gender::text != d.gender);
        """)
        print("Synchronized fragrance_dna.gender to fragrance_line.marketing_gender")

        # 6. Eliminate generic Unsplash stock placeholders
        print("\n=== 5. ELIMINATING GENERIC UNSPLASH STOCK PHOTOS ===")
        # For fragrances with Unsplash photos, set image_url to NULL so frontend renders the sleek gold placeholder
        cleared_count = await conn.execute("""
            UPDATE fragrance_dna
            SET image_url = NULL
            WHERE image_url ILIKE '%unsplash.com%';
        """)
        print(f"Cleared generic Unsplash stock photos: {cleared_count}")

        # Summary check
        stats = await conn.fetch("""
            SELECT 
                COUNT(*) as total,
                COUNT(image_url) as with_image,
                COUNT(CASE WHEN image_url LIKE '/images/%' THEN 1 END) as local_images,
                COUNT(CASE WHEN image_url LIKE '%shopify%' THEN 1 END) as shopify_images,
                COUNT(CASE WHEN image_url LIKE '%unsplash%' THEN 1 END) as unsplash_images,
                COUNT(CASE WHEN image_url IS NULL THEN 1 END) as null_images,
                COUNT(CASE WHEN gender = 'masculine' THEN 1 END) as masculine_cnt,
                COUNT(CASE WHEN gender = 'feminine' THEN 1 END) as feminine_cnt,
                COUNT(CASE WHEN gender = 'unisex' THEN 1 END) as unisex_cnt
            FROM fragrance_dna;
        """)
        print("\n=== FINAL CATALOG STATS ===")
        for s in stats:
            print(dict(s))

    finally:
        await conn.close()

if __name__ == '__main__':
    asyncio.run(run_fixes())
