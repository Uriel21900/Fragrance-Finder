import asyncio
import os
import sys
from sqlalchemy import select, delete

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import FragranceDNA, FragranceProduct, FragranceLine, ProductVariant, PriceObservation, Retailer

async def purge_banadir_from_aventus():
    async with async_session_maker() as session:
        # Get Banadir retailer
        b_res = await session.execute(select(Retailer).where(Retailer.normalized_name.ilike("%banadir%")))
        banadir_retailers = b_res.scalars().all()
        banadir_ids = [r.retailer_id for r in banadir_retailers]
        print(f"Banadir retailer IDs: {banadir_ids}")

        # Get Aventus DNA
        dna_res = await session.execute(select(FragranceDNA).where(FragranceDNA.canonical_name == "Aventus"))
        aventus = dna_res.scalar_one_or_none()

        # Find all variants of Aventus
        lines = (await session.execute(select(FragranceLine).where(FragranceLine.dna_id == aventus.dna_id))).scalars().all()
        for line in lines:
            prods = (await session.execute(select(FragranceProduct).where(FragranceProduct.line_id == line.line_id))).scalars().all()
            for prod in prods:
                vars = (await session.execute(select(ProductVariant).where(ProductVariant.product_id == prod.product_id))).scalars().all()
                for v in vars:
                    # Delete any observation with banadir retailer or banadir in source_url
                    obs_list = (await session.execute(select(PriceObservation).where(PriceObservation.variant_id == v.variant_id))).scalars().all()
                    for obs in obs_list:
                        if obs.retailer_id in banadir_ids or "banadir" in (obs.source_url or "").lower():
                            print(f"Purging Banadir observation: {obs.price_observation_id} (${obs.price_amount})")
                            await session.delete(obs)
                            
        await session.commit()
        print("Purge complete.")

if __name__ == "__main__":
    asyncio.run(purge_banadir_from_aventus())
