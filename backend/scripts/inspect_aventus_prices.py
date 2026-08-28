import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import FragranceDNA, FragranceLine, FragranceProduct, ProductVariant, PriceObservation, Retailer
from sqlalchemy import select

async def inspect():
    async with async_session_maker() as session:
        dna = (await session.execute(select(FragranceDNA).where(FragranceDNA.canonical_name == "Aventus"))).scalar_one_or_none()
        print(f"Aventus DNA: {dna.dna_id} | Image: {dna.image_url}")
        lines = (await session.execute(select(FragranceLine).where(FragranceLine.dna_id == dna.dna_id))).scalars().all()
        for line in lines:
            prods = (await session.execute(select(FragranceProduct).where(FragranceProduct.line_id == line.line_id))).scalars().all()
            for prod in prods:
                vars = (await session.execute(select(ProductVariant).where(ProductVariant.product_id == prod.product_id))).scalars().all()
                for v in vars:
                    print(f"Variant: {v.variant_id} | {v.volume_ml}ml {v.package_type}")
                    obs_list = (await session.execute(
                        select(PriceObservation, Retailer)
                        .outerjoin(Retailer, PriceObservation.retailer_id == Retailer.retailer_id)
                        .where(PriceObservation.variant_id == v.variant_id)
                    )).all()
                    for obs, r in obs_list:
                        rname = r.name if r else "None"
                        print(f"  Obs {obs.price_observation_id}: ${obs.price_amount} | {rname} | {obs.source_url}")

if __name__ == "__main__":
    asyncio.run(inspect())
