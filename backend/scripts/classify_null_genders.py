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
    if not db_url:
        print("DATABASE_URL missing")
        return

    conn = await asyncpg.connect(db_url)

    print("Classifying any NULL genders in fragrance_dna...")
    # 1. Update masculine
    masc_res = await conn.execute("""
        UPDATE fragrance_dna
        SET gender = 'masculine', updated_at = NOW()
        WHERE gender IS NULL
          AND (
            canonical_name ILIKE '%for men%' OR
            canonical_name ILIKE '%pour homme%' OR
            canonical_name ILIKE '%for him%' OR
            canonical_name ILIKE '%for man%' OR
            canonical_name ILIKE '%men edp%' OR
            canonical_name ILIKE '%men edt%' OR
            canonical_name ILIKE '%homme%' OR
            canonical_name ILIKE '%man spray%'
          );
    """)
    print(f"Updated masculine: {masc_res}")

    # 2. Update feminine
    fem_res = await conn.execute("""
        UPDATE fragrance_dna
        SET gender = 'feminine', updated_at = NOW()
        WHERE gender IS NULL
          AND (
            canonical_name ILIKE '%for women%' OR
            canonical_name ILIKE '%pour femme%' OR
            canonical_name ILIKE '%for her%' OR
            canonical_name ILIKE '%for woman%' OR
            canonical_name ILIKE '%women edp%' OR
            canonical_name ILIKE '%women edt%' OR
            canonical_name ILIKE '%femme%' OR
            canonical_name ILIKE '%ladies%'
          );
    """)
    print(f"Updated feminine: {fem_res}")

    # 3. Default remainder to unisex
    uni_res = await conn.execute("""
        UPDATE fragrance_dna
        SET gender = 'unisex', updated_at = NOW()
        WHERE gender IS NULL;
    """)
    print(f"Updated remaining to unisex: {uni_res}")

    # 4. Sync fragrance_line marketing_gender
    sync_res = await conn.execute("""
        UPDATE fragrance_line l
        SET marketing_gender = d.gender::fragrance_gender_marketing, updated_at = NOW()
        FROM fragrance_dna d
        WHERE l.dna_id = d.dna_id
          AND (l.marketing_gender IS NULL OR l.marketing_gender::text != d.gender)
          AND d.gender IN ('masculine', 'feminine', 'unisex');
    """)
    print(f"Synced fragrance_line marketing_gender: {sync_res}")

    # Check stats
    stats = await conn.fetchrow("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN gender = 'masculine' THEN 1 END) as masculine,
            COUNT(CASE WHEN gender = 'feminine' THEN 1 END) as feminine,
            COUNT(CASE WHEN gender = 'unisex' THEN 1 END) as unisex,
            COUNT(CASE WHEN gender IS NULL THEN 1 END) as null_gender
        FROM fragrance_dna;
    """)
    print(f"\nCatalog Gender Breakdown: Total={stats['total']} | Masculine={stats['masculine']} | Feminine={stats['feminine']} | Unisex={stats['unisex']} | Null={stats['null_gender']}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
