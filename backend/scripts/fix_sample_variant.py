import asyncio
import os
import sys
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import FragranceDNA, FragranceProduct, FragranceLine, ProductVariant, PriceObservation

async def fix_sample_variant():
    async with async_session_maker() as session:
        dna_res = await session.execute(select(FragranceDNA).where(FragranceDNA.canonical_name == "Aventus"))
        aventus = dna_res.scalar_one_or_none()
        
        prod_res = await session.execute(
            select(FragranceProduct)
            .join(FragranceLine, FragranceProduct.line_id == FragranceLine.line_id)
            .where(FragranceLine.dna_id == aventus.dna_id)
        )
        prod = prod_res.scalars().first()
        
        # Get or create 2.0ml sample variant
        var_res = await session.execute(select(ProductVariant).filter_by(product_id=prod.product_id, volume_ml=2.0))
        var_sample = var_res.scalars().first()
        if not var_sample:
            var_sample = ProductVariant(
                product_id=prod.product_id,
                volume_ml=2.0,
                package_type="sample vial"
            )
            session.add(var_sample)
            await session.flush()
            
        # Update any 19.95 price observation to point to var_sample
        obs_res = await session.execute(select(PriceObservation).where(PriceObservation.price_amount == 19.95))
        for obs in obs_res.scalars().all():
            obs.variant_id = var_sample.variant_id
            
        await session.commit()
        print("Updated 19.95 sample observations to 2.0ml sample vial variant.")

if __name__ == "__main__":
    asyncio.run(fix_sample_variant())
