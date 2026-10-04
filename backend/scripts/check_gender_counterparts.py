import asyncio, os, sys, asyncpg
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")

NAMES = [
    'Aventus', 'Aventus for Her', 'Aventus Cologne',
    'Light Blue', 'Light Blue pour Homme',
    'Acqua di Gio', 'Acqua di Gioia', 'Acqua Di Gio Profondo',
    'Eros', 'Eros Pour Femme', 'Eros Flame',
    'Spicebomb', 'Flowerbomb',
    'Sauvage', 'Sauvage Elixir', 'Miss Dior', "J'adore", 'Hypnotic Poison', 'Fahrenheit',
    'Bleu de Chanel', 'Allure Homme Sport', 'Coco Mademoiselle', 'Chance', 'Sycomore',
    'Layton', 'Herod', 'Pegasus', 'Greenley', 'Delina', 'Delina Exclusif', 'Oriana', 'Valaya',
    'Bad Boy', 'Good Girl',
    '1 Million', 'Lady Million', 'Invictus', 'Olympea',
    'Le Male', 'Le Male Elixir', 'Ultra Male', 'Classique', 'La Belle',
    'Black Opium', 'Opium', 'Libre', 'Y Eau de Parfum',
    'Black Orchid', 'Tobacco Vanille', 'Oud Wood', 'Lost Cherry', 'Noir Extreme',
    'Baccarat Rouge 540', 'Grand Soir',
    "Angels' Share",
    'CK One', 'CK Be', 'Terre d\'Hermes', 'Shalimar',
    'Khamrah', 'Asad', 'Yara', '9pm', 'Detour Noir', 'The Tux',
    'Club De Nuit Intense Man', 'Club De Nuit Intense Woman'
]

async def main():
    sys.stdout.reconfigure(encoding='utf-8')
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    
    rows = await conn.fetch("""
        SELECT d.dna_id, d.canonical_name, b.name as brand, d.image_url, d.gender, l.marketing_gender
        FROM fragrance_dna d
        LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
        LEFT JOIN fragrance_line l ON l.dna_id = d.dna_id
        WHERE d.canonical_name = ANY($1::text[])
        ORDER BY b.name, d.canonical_name;
    """, NAMES)
    
    found_names = set()
    for r in rows:
        found_names.add(r['canonical_name'])
        print(f"FOUND: {r['brand']} - {r['canonical_name']} | Img: {r['image_url'][:50] if r['image_url'] else 'None'} | LineGender: {r['marketing_gender']}")
        
    print("\nMISSING FROM DATABASE:")
    for n in NAMES:
        if n not in found_names:
            print(f"  MISSING: {n}")
            
    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
