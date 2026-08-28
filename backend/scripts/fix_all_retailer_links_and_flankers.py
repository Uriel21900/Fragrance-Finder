import asyncio
import os
import sys
import re
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, delete, update, text
from urllib.parse import urlparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.schema import (
    FragranceDNA, Brand, FragranceLine, FragranceProduct, ProductVariant, 
    Retailer, PriceObservation
)

LOCAL_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/fragrance_finder"
NEON_DB_URL = "postgresql+asyncpg://neondb_owner:npg_iN45StWGXmpK@ep-winter-surf-ay718z8s-pooler.c-5.us-east-2.aws.neon.tech/neondb?ssl=require"

async def fix_database(db_url: str, db_name: str):
    print(f"\n=======================================================")
    print(f"CLEANING & FIXING DATABASE: {db_name}")
    print(f"=======================================================")
    
    engine = create_async_engine(db_url, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    
    async with session_maker() as session:
        # 1. Fix Image URLs for Clones
        print("[1] Updating accurate bottle images...")
        await session.execute(
            update(FragranceDNA)
            .where(FragranceDNA.canonical_name.ilike('%Charuto Tobacco Vanille%'))
            .values(image_url='/images/charuto_tobacco_vanille.jpg')
        )
        await session.execute(
            update(FragranceDNA)
            .where(FragranceDNA.canonical_name.ilike('%Desire Gold%'))
            .values(image_url='/images/dunhill_desire_gold.jpg')
        )
        await session.commit()
        
        # 2. Delete all generic search URLs (/search?q=)
        print("[2] Purging generic search URLs (/search?q=)...")
        del_search = delete(PriceObservation).where(PriceObservation.source_url.ilike('%/search?q=%'))
        res_search = await session.execute(del_search)
        print(f"    Deleted {res_search.rowcount} generic search observations.")
        await session.commit()

        # 3. Clean up Creed Aventus (Purge flankers and clones from authentic DNA)
        print("[3] Cleaning Creed Aventus price observations...")
        aventus_dnas = (await session.execute(
            select(FragranceDNA).where(FragranceDNA.canonical_name == 'Aventus', FragranceDNA.is_dupe == False)
        )).scalars().all()
        
        for av in aventus_dnas:
            # Find all variant IDs for Aventus
            var_ids = (await session.execute(
                select(ProductVariant.variant_id)
                .join(FragranceProduct, ProductVariant.product_id == FragranceProduct.product_id)
                .join(FragranceLine, FragranceProduct.line_id == FragranceLine.line_id)
                .where(FragranceLine.dna_id == av.dna_id)
            )).scalars().all()
            
            if var_ids:
                # Delete flankers & clones & dead links
                bad_patterns = [
                    '%royal-water%', '%delphinus%', '%banadirfragrance%', 
                    '%eau-de-parfum-100ml', '%m-aventus-3-3.html', '%edp-3-3-oz-spray'
                ]
                for pat in bad_patterns:
                    d_stmt = delete(PriceObservation).where(
                        PriceObservation.variant_id.in_(var_ids),
                        PriceObservation.source_url.ilike(pat)
                    )
                    await session.execute(d_stmt)
                    
        await session.commit()

        # 4. Clean up Tom Ford Tobacco Vanille (Purge clones and flankers from authentic DNA)
        print("[4] Cleaning Tom Ford Tobacco Vanille price observations...")
        tf_dnas = (await session.execute(
            select(FragranceDNA).where(FragranceDNA.canonical_name == 'Tobacco Vanille', FragranceDNA.is_dupe == False)
        )).scalars().all()
        
        for tf in tf_dnas:
            var_ids = (await session.execute(
                select(ProductVariant.variant_id)
                .join(FragranceProduct, ProductVariant.product_id == FragranceProduct.product_id)
                .join(FragranceLine, FragranceProduct.line_id == FragranceLine.line_id)
                .where(FragranceLine.dna_id == tf.dna_id)
            )).scalars().all()
            
            if var_ids:
                bad_patterns = [
                    '%charuto%', '%banadirfragrance%', '%ombre-leather%', '%vanilla-muse%', 
                    '%tom-ford-tobacco-vanille.html'
                ]
                for pat in bad_patterns:
                    d_stmt = delete(PriceObservation).where(
                        PriceObservation.variant_id.in_(var_ids),
                        PriceObservation.source_url.ilike(pat)
                    )
                    await session.execute(d_stmt)
                    
        await session.commit()

        # 5. Clean up Dunhill Desire Gold (Purge Desire Red and Desire Blue)
        print("[5] Cleaning Dunhill Desire Gold price observations...")
        dg_dnas = (await session.execute(
            select(FragranceDNA).where(FragranceDNA.canonical_name.ilike('%Desire Gold%'))
        )).scalars().all()
        
        for dg in dg_dnas:
            var_ids = (await session.execute(
                select(ProductVariant.variant_id)
                .join(FragranceProduct, ProductVariant.product_id == FragranceProduct.product_id)
                .join(FragranceLine, FragranceProduct.line_id == FragranceLine.line_id)
                .where(FragranceLine.dna_id == dg.dna_id)
            )).scalars().all()
            
            if var_ids:
                bad_patterns = [
                    '%desire-blue%', '%desire-for-men-by-dunhill-edt%', '%dunhill-desire-gold.html'
                ]
                for pat in bad_patterns:
                    d_stmt = delete(PriceObservation).where(
                        PriceObservation.variant_id.in_(var_ids),
                        PriceObservation.source_url.ilike(pat)
                    )
                    await session.execute(d_stmt)
                    
        await session.commit()

        # 6. Clean up Charuto Tobacco Vanille
        print("[6] Cleaning Charuto Tobacco Vanille price observations...")
        charuto_dnas = (await session.execute(
            select(FragranceDNA).where(FragranceDNA.canonical_name.ilike('%Charuto Tobacco Vanille%'))
        )).scalars().all()
        
        for ch in charuto_dnas:
            var_ids = (await session.execute(
                select(ProductVariant.variant_id)
                .join(FragranceProduct, ProductVariant.product_id == FragranceProduct.product_id)
                .join(FragranceLine, FragranceProduct.line_id == FragranceLine.line_id)
                .where(FragranceLine.dna_id == ch.dna_id)
            )).scalars().all()
            
            if var_ids:
                # Delete authentic TF ($399) or Banadir
                bad_patterns = ['%tomfordtobaccovanille%', '%royal-taboo%']
                for pat in bad_patterns:
                    d_stmt = delete(PriceObservation).where(
                        PriceObservation.variant_id.in_(var_ids),
                        PriceObservation.source_url.ilike(pat)
                    )
                    await session.execute(d_stmt)
                    
                # Add verified Charuto product link on PerfumeOnline ($23.85)
                r_po = (await session.execute(select(Retailer).where(Retailer.name.ilike('%perfumeonline%')))).scalars().first()
                if r_po and var_ids:
                    session.add(PriceObservation(
                        variant_id=var_ids[0],
                        retailer_id=r_po.retailer_id,
                        price_amount=23.85,
                        currency_code="USD",
                        source_url="https://perfumeonline.com/products/charuto-tobacco-vanille-pendora"
                    ))
                    
        await session.commit()

        # 7. Global deduplication of PriceObservations per (variant_id, retailer_id, source_url)
        print("[7] Deduplicating price observations...")
        await session.execute(text("""
            DELETE FROM price_observation a USING price_observation b
            WHERE a.price_observation_id < b.price_observation_id
              AND a.variant_id = b.variant_id
              AND a.source_url = b.source_url;
        """))
        await session.commit()
        
        print(f"Successfully cleaned & updated {db_name}!")

async def main():
    await fix_database(LOCAL_DB_URL, "Local PostgreSQL")
    await fix_database(NEON_DB_URL, "Neon Cloud PostgreSQL")

if __name__ == "__main__":
    asyncio.run(main())
