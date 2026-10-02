"""
purge_mismatched_prices.py
Removes price_observation rows whose source_url clearly points to the
wrong product (e.g. Layton variant linked to a Delina La Rosee URL).

Strategy: for each (dna, variant) pair, fetch all price observations and
check if the source_url contains the fragrance name tokens. Any row where
the URL cannot be matched to the expected fragrance is deleted.

Run:
    cd backend
    python scripts/purge_mismatched_prices.py [--dry-run]
"""

import asyncio
import os
import re
import sys
import argparse
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")

try:
    import asyncpg
except ImportError:
    print("asyncpg not installed. Run: pip install asyncpg")
    sys.exit(1)

# ── Same stop-words and tokeniser as run_scheduled_scrapers.py ──────────────
_NAME_STOP_WORDS = {"de", "la", "le", "les", "du", "the", "by", "for", "and",
                    "eau", "parfum", "extrait", "cologne", "toilette"}

def _significant_tokens(text: str) -> list[str]:
    return [
        t for t in re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()
        if len(t) > 2 and t not in _NAME_STOP_WORDS
    ]

def url_matches_fragrance(url: str, canonical_name: str) -> bool:
    """
    Returns True if the source_url is plausibly for the right product.
    We check that at least one significant token from the fragrance name
    appears in the URL path (Shopify product handles are slug-ified names).
    """
    if not url:
        return False
    url_slug = url.lower().replace("-", " ").replace("_", " ").replace("/", " ")
    name_tokens = _significant_tokens(canonical_name)
    if not name_tokens:
        return True  # Can't determine — keep it
    matched = sum(1 for t in name_tokens if t in url_slug)
    required = max(1, len(name_tokens) // 2 + len(name_tokens) % 2)
    return matched >= required

async def purge(dry_run: bool = True):
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set.")
        sys.exit(1)
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    if "sslmode=" not in db_url and "ssl=" not in db_url:
        sep = "&" if "?" in db_url else "?"
        db_url += f"{sep}sslmode=require"

    conn = await asyncpg.connect(db_url)
    mode = "[DRY RUN] " if dry_run else ""
    print(f"\n{'='*70}")
    print(f"  {mode}PURGING MISMATCHED PRICE OBSERVATIONS")
    print(f"{'='*70}\n")

    try:
        # Fetch all price observations joined with their DNA name
        rows = await conn.fetch("""
            SELECT
                po.price_observation_id,
                po.variant_id,
                po.source_url,
                po.price_amount,
                po.observed_at,
                d.canonical_name,
                d.dna_id,
                b.name AS brand_name
            FROM price_observation po
            JOIN product_variant pv   ON po.variant_id      = pv.variant_id
            JOIN fragrance_product fp ON pv.product_id      = fp.product_id
            JOIN fragrance_line fl    ON fp.line_id         = fl.line_id
            JOIN fragrance_dna d      ON fl.dna_id          = d.dna_id
            JOIN brand b              ON d.origin_brand_id  = b.brand_id
            ORDER BY d.canonical_name, po.observed_at DESC
        """)

        bad_ids = []
        for row in rows:
            name = row["canonical_name"]
            url  = row["source_url"] or ""
            if not url_matches_fragrance(url, name):
                bad_ids.append(row["price_observation_id"])
                print(f"  BAD  [{name}]")
                print(f"       URL: {url}")
                print(f"       Price: ${row['price_amount']}  Observed: {row['observed_at']}")
                print()

        print(f"{'='*70}")
        print(f"  Total observations checked : {len(rows)}")
        print(f"  Mismatched (to delete)     : {len(bad_ids)}")

        if bad_ids:
            if dry_run:
                print(f"\n  [DRY RUN] Would delete {len(bad_ids)} rows. Run without --dry-run to apply.")
            else:
                deleted = await conn.execute(
                    "DELETE FROM price_observation WHERE price_observation_id = ANY($1::uuid[])",
                    bad_ids
                )
                print(f"\n  DELETED {deleted} mismatched price observation rows.")
        else:
            print("\n  No mismatched rows found. Database is clean!")

        print(f"{'='*70}\n")

    finally:
        await conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Purge price observations whose source_url doesn't match the fragrance.")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Preview deletions without committing (default: True)")
    parser.add_argument("--apply", action="store_true", default=False,
                        help="Actually delete the bad rows (overrides --dry-run)")
    args = parser.parse_args()
    dry = not args.apply
    asyncio.run(purge(dry_run=dry))
