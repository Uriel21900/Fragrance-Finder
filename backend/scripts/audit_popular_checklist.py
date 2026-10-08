import asyncio, os, sys
import asyncpg
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8', errors='replace')

load_dotenv("backend/.env")
load_dotenv(".env")

POPULAR_CHECKLIST = [
    # (Fragrance Name, Brand, Clone target / notes)
    ("Apple Brandy on the Rocks", "Kilian"),
    ("Torino21", "Xerjoff"),
    ("MYSLF", "Yves Saint Laurent"),
    ("Le Male Elixir", "Jean Paul Gaultier"),
    ("Liquid Brun", "French Avenue"),
    ("Althair", "Parfums de Marly"),
    ("Stronger With You", "Giorgio Armani"),
    ("Valentino Uomo Born in Roma", "Valentino"),
    ("Valentino Donna Born in Roma", "Valentino"),
    ("Luna Rossa Ocean", "Prada"),
    ("Tobacco Vanille", "Tom Ford"),
    ("Lost Cherry", "Tom Ford"),
    ("Angels' Share", "Kilian"),
    ("Khamrah", "Lattafa"),
    ("Club de Nuit Intense Man", "Armaf"),
    ("Bleu de Chanel", "Chanel"),
    ("Sauvage", "Dior"),
    ("Acqua di Gio", "Giorgio Armani"),
    ("Y Eau de Parfum", "Yves Saint Laurent"),
    ("Grand Soir", "Maison Francis Kurkdjian"),
    ("Oud Wood", "Tom Ford"),
    ("Layton", "Parfums de Marly"),
    ("Naxos", "Xerjoff"),
    ("Erba Pura", "Xerjoff"),
    ("Side Effect", "Initio Parfums Prives"),
    ("Oud for Greatness", "Initio Parfums Prives"),
    ("Afternoon Swim", "Louis Vuitton"),
    ("Imagination", "Louis Vuitton"),
    ("Pacific Chill", "Louis Vuitton"),
    ("L'Immensité", "Louis Vuitton"),
    ("Spectre Ghost", "French Avenue"),
    ("Vintage Radio", "Lattafa"),
    ("Liam Grey", "Lattafa"),
    ("Artisan Pure", "John Varvatos"),
    ("Hawas", "Rasasi")
]

async def main():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is required.")
    conn = await asyncpg.connect(db_url)
    missing = []
    found = []
    
    for name, brand in POPULAR_CHECKLIST:
        row = await conn.fetchrow("""
            SELECT d.dna_id, d.canonical_name, b.name as brand_name
            FROM fragrance_dna d
            JOIN brand b ON d.origin_brand_id = b.brand_id
            WHERE d.canonical_name ILIKE $1 AND b.name ILIKE $2
            LIMIT 1;
        """, f"%{name}%", f"%{brand}%")
        
        if row:
            # check price count
            p_count = await conn.fetchval("""
                SELECT count(*)
                FROM fragrance_line l
                JOIN fragrance_product fp ON l.line_id = fp.line_id
                JOIN product_variant pv ON fp.product_id = pv.product_id
                JOIN price_observation p ON pv.variant_id = p.variant_id
                WHERE l.dna_id = $1
            """, row['dna_id'])
            found.append((name, brand, row['canonical_name'], p_count))
        else:
            missing.append((name, brand))
            
    print(f"=== CHECKLIST RESULTS ({len(found)} found, {len(missing)} missing) ===")
    print("\nMISSING FROM DATABASE:")
    for m in missing:
        print(f"  ❌ {m[1]} - {m[0]}")
        
    print("\nFOUND IN DATABASE:")
    for f in found:
        print(f"  ✅ {f[1]} - {f[2]} ({f[3]} prices)")
        
    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
