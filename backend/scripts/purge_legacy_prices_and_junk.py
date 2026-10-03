import asyncio
import os
import sys
from sqlalchemy import select, delete, func, or_, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import (
    FragranceDNA, Brand, FragranceLine, FragranceProduct, ProductVariant,
    PriceObservation, DNARelationship, FragranceAlert
)

async def purge_legacy_and_junk():
    print("=" * 60)
    print("STARTING DATABASE CLEANUP: PURGING LEGACY UNVERIFIED PRICES & JUNK DNAS")
    print("=" * 60)
    
    async with async_session_maker() as session:
        # 1. Count before
        price_count_before = (await session.execute(select(func.count(PriceObservation.price_observation_id)))).scalar()
        dna_count_before = (await session.execute(select(func.count(FragranceDNA.dna_id)))).scalar()
        print(f"Initial State: {price_count_before:,} Price Observations, {dna_count_before:,} DNAs")
        
        # 2. Delete legacy unverified price observations
        print("Purging legacy unverified price observations...")
        await session.execute(delete(PriceObservation))
        await session.commit()
        print("Purged all legacy unverified price observations.")
        
        # 3. Identify junk DNAs (banners, prices, promo text accidentally inserted by old scrapers)
        junk_patterns = [
            FragranceDNA.canonical_name.ilike("%$%"),
            FragranceDNA.canonical_name.ilike("%http%"),
            FragranceDNA.canonical_name.ilike("%.com%"),
            FragranceDNA.canonical_name.ilike("%save up to%"),
            FragranceDNA.canonical_name.ilike("%price range%"),
            FragranceDNA.canonical_name.ilike("%regular price%"),
            FragranceDNA.canonical_name.ilike("%sale price%"),
            FragranceDNA.canonical_name.ilike("%gift set%"),
            FragranceDNA.canonical_name.ilike("%collections/%"),
            FragranceDNA.canonical_name.ilike("%products/%"),
            FragranceDNA.canonical_name.ilike("%off %")
        ]
        
        junk_dnas_stmt = select(FragranceDNA.dna_id).where(or_(*junk_patterns))
        junk_dna_ids = (await session.execute(junk_dnas_stmt)).scalars().all()
        print(f"Identified {len(junk_dna_ids)} junk scraper artifacts in FragranceDNA.")
        
        if junk_dna_ids:
            # Delete relationships referencing junk DNAs
            await session.execute(
                delete(DNARelationship).where(
                    or_(
                        DNARelationship.source_dna_id.in_(junk_dna_ids),
                        DNARelationship.target_dna_id.in_(junk_dna_ids)
                    )
                )
            )
            
            # Delete alerts
            await session.execute(
                delete(FragranceAlert).where(FragranceAlert.dna_id.in_(junk_dna_ids))
            )
            
            # Find and delete lines, products, variants
            lines_stmt = select(FragranceLine.line_id).where(FragranceLine.dna_id.in_(junk_dna_ids))
            junk_line_ids = (await session.execute(lines_stmt)).scalars().all()
            
            if junk_line_ids:
                prods_stmt = select(FragranceProduct.product_id).where(FragranceProduct.line_id.in_(junk_line_ids))
                junk_prod_ids = (await session.execute(prods_stmt)).scalars().all()
                
                if junk_prod_ids:
                    await session.execute(
                        delete(ProductVariant).where(ProductVariant.product_id.in_(junk_prod_ids))
                    )
                    await session.execute(
                        delete(FragranceProduct).where(FragranceProduct.product_id.in_(junk_prod_ids))
                    )
                
                await session.execute(
                    delete(FragranceLine).where(FragranceLine.line_id.in_(junk_line_ids))
                )
                
            # Finally delete junk DNAs
            await session.execute(
                delete(FragranceDNA).where(FragranceDNA.dna_id.in_(junk_dna_ids))
            )
            await session.commit()
            print(f"Successfully deleted {len(junk_dna_ids)} junk DNAs and their cascading records.")

        # 4. Count after
        dna_count_after = (await session.execute(select(func.count(FragranceDNA.dna_id)))).scalar()
        print(f"Final State: Database cleanly contains {dna_count_after:,} authentic, verified Fragrance DNAs.")

if __name__ == "__main__":
    asyncio.run(purge_legacy_and_junk())
