import asyncio
import os
import sys
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import FragranceDNA, FragranceProduct, FragranceLine, ProductVariant, PriceObservation, Brand

async def global_purge():
    async with async_session_maker() as session:
        # Find all price observations with banadir
        obs_res = await session.execute(
            select(PriceObservation, ProductVariant, FragranceProduct, FragranceLine, FragranceDNA, Brand)
            .join(ProductVariant, PriceObservation.variant_id == ProductVariant.variant_id)
            .join(FragranceProduct, ProductVariant.product_id == FragranceProduct.product_id)
            .join(FragranceLine, FragranceProduct.line_id == FragranceLine.line_id)
            .join(FragranceDNA, FragranceLine.dna_id == FragranceDNA.dna_id)
            .outerjoin(Brand, FragranceDNA.origin_brand_id == Brand.brand_id)
        )
        
        purged = 0
        for obs, v, prod, line, dna, brand in obs_res.all():
            u_low = (obs.source_url or "").lower()
            b_norm = brand.normalized_name if brand else ""
            if "banadirfragrance" in u_low and b_norm != "banadir_fragrance":
                print(f"Purging Banadir observation from [{brand.name if brand else 'Unknown'} - {dna.canonical_name}]: {obs.source_url}")
                await session.delete(obs)
                purged += 1
                
        await session.commit()
        print(f"Purged {purged} remaining Banadir observations from authentic fragrances.")

if __name__ == "__main__":
    asyncio.run(global_purge())
