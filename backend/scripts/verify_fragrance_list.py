"""
verify_fragrance_list.py
Checks that each fragrance in the canonical list resolves to exactly
the correct DNA record in the database. Simulates the same ILIKE search
used by the frontend /api/search route and reports cross-contamination,
missing entries, and brand mismatches.
"""

import asyncio
import os
import sys
import io

# Safe UTF-8 configuration without detaching stdout buffer
if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8', errors='replace')

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")

try:
    import asyncpg
except ImportError:
    print("asyncpg not installed. Run: pip install asyncpg python-dotenv")
    sys.exit(1)

# ── Canonical ground-truth list ─────────────────────────────────────────────
FRAGRANCE_LIST = [
    ("Acqua di Gio", "Giorgio Armani"),
    ("Light Blue", "Dolce & Gabbana"),
    ("Bleu de Chanel", "Chanel"),
    ("Sauvage", "Dior"),
    ("Neroli Portofino", "Tom Ford"),
    ("CK One", "Calvin Klein"),
    ("Green Irish Tweed", "Creed"),
    ("Wood Sage & Sea Salt", "Jo Malone"),
    ("Millesime Imperial", "Creed"),
    ("Artisan Pure", "John Varvatos"),
    ("J'adore", "Dior"),
    ("Flowerbomb", "Viktor & Rolf"),
    ("Daisy", "Marc Jacobs"),
    ("Bright Crystal", "Versace"),
    ("Miss Dior", "Dior"),
    ("Chloé Eau de Parfum", "Chloé"),
    ("Delina", "Parfums de Marly"),
    ("Carnal Flower", "Frederic Malle"),
    ("Blackberry & Bay", "Jo Malone"),
    ("Lost Cherry", "Tom Ford"),
    ("Shalimar", "Guerlain"),
    ("Opium", "Yves Saint Laurent"),
    ("Black Orchid", "Tom Ford"),
    ("Angels' Share", "Kilian"),
    ("Tobacco Vanille", "Tom Ford"),
    ("Grand Soir", "Maison Francis Kurkdjian"),
    ("Alien", "Mugler"),
    ("Spicebomb", "Viktor & Rolf"),
    ("Ambre Narguilé", "Hermès"),
    ("L'Interdit", "Givenchy"),
    ("Terre d'Hermès", "Hermès"),
    ("Santal 33", "Le Labo"),
    ("Encre Noire", "Lalique"),
    ("Wonderwood", "Comme des Garçons"),
    ("Oud Wood", "Tom Ford"),
    ("Tam Dao", "Diptyque"),
    ("Sycomore", "Chanel"),
    ("Greenley", "Parfums de Marly"),
    ("Bleecker Street", "Bond No. 9"),
    ("Fahrenheit", "Dior"),
    ("Baccarat Rouge 540", "Maison Francis Kurkdjian"),
    ("Angel", "Mugler"),
    ("Black Opium", "Yves Saint Laurent"),
    ("La Vie Est Belle", "Lancôme"),
    ("Hypnotic Poison", "Dior"),
    ("By the Fireplace", "Maison Margiela Replica"),
    ("Chocolate Greedy", "Montale"),
    ("Whiff of Waffle Cone", "Imaginary Authors"),
    ("Lira", "Xerjoff"),
    ("Cheirosa 62", "Sol de Janeiro"),
    # Iconic Modern Classics & Trending Additions
    ("Aventus", "Creed"),
    ("Apple Brandy on the Rocks", "Kilian"),
    ("Torino21", "Xerjoff"),
    ("Naxos", "Xerjoff"),
    ("Erba Pura", "Xerjoff"),
    ("MYSLF", "Yves Saint Laurent"),
    ("Le Male Elixir", "Jean Paul Gaultier"),
    ("Althair", "Parfums de Marly"),
    ("Layton", "Parfums de Marly"),
    ("Stronger With You", "Giorgio Armani"),
    ("Valentino Uomo Born in Roma", "Valentino"),
    ("Valentino Donna Born in Roma", "Valentino"),
    ("Luna Rossa Ocean", "Prada"),
    ("Imagination", "Louis Vuitton"),
    ("Pacific Chill", "Louis Vuitton"),
    ("L'Immensité", "Louis Vuitton"),
    ("Ani", "Nishane"),
    ("Paragon", "Initio Parfums Prives"),
    ("Side Effect", "Initio Parfums Prives"),
    ("Oud for Greatness", "Initio Parfums Prives"),
    ("Gris Charnel", "BDK Parfums"),
    ("Hawas for Men", "Rasasi"),
    # Trending Clones (is_dupe=True)
    ("Liquid Brun", "French Avenue", True),
    ("Spectre Ghost", "French Avenue", True),
    ("Vintage Radio", "Lattafa", True),
    ("Liam Grey", "Lattafa", True),
    ("Khamrah", "Lattafa", True),
    ("Club De Nuit Intense Man", "Armaf", True),
]

# ── Query that mirrors the frontend /api/search route ───────────────────────
# NOTE: We intentionally do NOT search inspired_by here — that's the bug.
SEARCH_SQL = """
SELECT
    d.dna_id,
    d.canonical_name,
    d.normalized_name,
    d.is_dupe,
    d.inspired_by,
    b.name AS brand_name
FROM fragrance_dna d
LEFT JOIN brand b ON d.origin_brand_id = b.brand_id
WHERE d.canonical_name ILIKE $1
   OR b.name           ILIKE $1
ORDER BY
    -- Exact name match scores highest
    CASE WHEN LOWER(d.canonical_name) = LOWER($2) THEN 0
         WHEN d.canonical_name ILIKE $1            THEN 1
         ELSE 2
    END,
    d.canonical_name
LIMIT 10;
"""

def fmt_status(ok: bool) -> str:
    return "✅" if ok else "❌"

async def verify_all():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set in environment or .env")
        sys.exit(1)

    # Normalise URL for asyncpg
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    if "sslmode=" not in db_url and "ssl=" not in db_url:
        sep = "&" if "?" in db_url else "?"
        db_url += f"{sep}sslmode=require"

    conn = await asyncpg.connect(db_url)
    try:
        print("\n" + "=" * 72)
        print("  FRAGRANCE DATABASE VERIFICATION REPORT")
        print("=" * 72)
        print(f"{'#':<4} {'Status':<8} {'Fragrance':<35} {'Expected Brand':<28} {'DB Brand':<28} {'Notes'}")
        print("-" * 130)

        exact_ok       = 0
        wrong_result   = 0
        missing        = 0
        dupe_leak      = 0
        wrong_brand    = 0
        issues         = []

        for idx, item in enumerate(FRAGRANCE_LIST, 1):
            name, brand = item[0], item[1]
            pattern = f"%{name}%"
            rows = await conn.fetch(SEARCH_SQL, pattern, name)

            if not rows:
                status = "MISSING"
                note   = "No record found in DB"
                missing += 1
                print(f"{idx:<4} {fmt_status(False):<8} {name:<35} {brand:<28} {'—':<28} {note}")
                issues.append((idx, name, brand, status, note))
                continue

            # Best candidate = first row after ordering
            best = rows[0]
            db_name   = best["canonical_name"]
            db_brand  = best["brand_name"] or "?"
            is_dupe   = best["is_dupe"]
            insp      = best["inspired_by"] or ""

            # ── Check 1: Name match ────────────────────────────────────────
            name_ok = name.lower() in db_name.lower() or db_name.lower() in name.lower()

            # ── Check 2: Brand match (fuzzy — handle MFK, PDM aliases) ───
            brand_aliases = {
                "Maison Francis Kurkdjian": ["mfk", "maison francis"],
                "Parfums de Marly":          ["pdm"],
                "Maison Margiela Replica":   ["margiela", "replica"],
                "Dolce & Gabbana":           ["d&g"],
                "Yves Saint Laurent":        ["ysl"],
            }
            def brands_match(expected: str, actual: str) -> bool:
                e = expected.lower()
                a = actual.lower()
                if e in a or a in e:
                    return True
                for canon, aliases in brand_aliases.items():
                    if canon.lower() == e:
                        return any(al in a for al in aliases)
                return False

            brand_ok = brands_match(brand, db_brand)

            # ── Check 3: Not a dupe/clone when we want originals ──────────
            # (Some originals like Sauvage should NOT be marked is_dupe)
            dupe_ok = not is_dupe  # originals should not be dupes

            # ── Check 4: Cross-contamination — did we get the WRONG name? ─
            cross_contaminated = not name_ok

            expect_dupe = item[2] if len(item) > 2 else False
            if cross_contaminated:
                status = "WRONG RESULT"
                note   = f"Got '{db_name}' instead of '{name}'"
                wrong_result += 1
                issues.append((idx, name, brand, status, note))
            elif not brand_ok:
                status = "WRONG BRAND"
                note   = f"Brand is '{db_brand}', expected '{brand}'"
                wrong_brand += 1
                issues.append((idx, name, brand, status, note))
            elif is_dupe and not expect_dupe:
                status = "DUPE LEAK"
                note   = f"Marked is_dupe=True, inspired_by='{insp}' — should be original"
                dupe_leak += 1
                issues.append((idx, name, brand, status, note))
            elif not is_dupe and expect_dupe:
                status = "ORIGINAL LEAK"
                note   = f"Marked is_dupe=False — expected clone"
                issues.append((idx, name, brand, status, note))
            else:
                status = "OK"
                note   = ""
                exact_ok += 1

            ok_flag = status == "OK"
            db_brand_display = db_brand[:27] if db_brand else "—"
            print(f"{idx:<4} {fmt_status(ok_flag):<8} {name:<35} {brand:<28} {db_brand_display:<28} {note}")

        # ── Summary ───────────────────────────────────────────────────────
        total = len(FRAGRANCE_LIST)
        print("\n" + "=" * 72)
        print("  SUMMARY")
        print("=" * 72)
        print(f"  Total checked    : {total}")
        print(f"  ✅ Correct        : {exact_ok}")
        print(f"  ❌ Wrong result  : {wrong_result}")
        print(f"  ❌ Wrong brand   : {wrong_brand}")
        print(f"  ❌ Dupe leak     : {dupe_leak}")
        print(f"  ❌ Missing       : {missing}")
        print()

        if issues:
            print("  ISSUES TO FIX:")
            print("  " + "-" * 68)
            for i, n, b, s, note in issues:
                print(f"  [{i:>2}] {s:<16} {n} by {b}")
                print(f"        → {note}")
        else:
            print("  🎉 All fragrances verified correctly!")

        print("=" * 72 + "\n")

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(verify_all())
