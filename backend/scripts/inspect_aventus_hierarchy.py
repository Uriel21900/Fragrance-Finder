import asyncio
import os
import sys
import asyncpg
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")
if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8')

async def main():
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)

    # 1. Inspect lines and variants for Aventus (Men) and Aventus for Her (Women)
    rows = await conn.fetch("""
        SELECT d.dna_id, d.canonical_name, d.gender, l.line_id, fp.product_id, pv.variant_id
        FROM fragrance_dna d
        LEFT JOIN fragrance_line l ON d.dna_id = l.dna_id
        LEFT JOIN fragrance_product fp ON l.line_id = fp.line_id
        LEFT JOIN product_variant pv ON fp.product_id = pv.product_id
        WHERE d.canonical_name IN ('Aventus', 'Aventus for Her');
    """)
    print("=== LINES & VARIANTS ===")
    for r in rows:
        print(f"DNA: {r['canonical_name']} ({r['dna_id']}) | Line: {r['line_id']} | Product: {r['product_id']} | Variant: {r['variant_id']}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
