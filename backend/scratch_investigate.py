import asyncio
import os
import sys

from database import async_session_maker
from models.schema import FragranceDNA, FragranceLine, FragranceProduct, ProductVariant, PriceObservation, Retailer
from sqlalchemy import select
from sqlalchemy.orm import selectinload

async def main():
    async with async_session_maker() as s:
        dnas = (await s.execute(select(FragranceDNA).where(FragranceDNA.canonical_name.in_(["Tres Nuit", "Club De Nuit Sillage"])))).scalars().all()
        for dna in dnas:
            print(f"\n--- {dna.canonical_name} ---")
            lines = (await s.execute(select(FragranceLine).where(FragranceLine.dna_id == dna.dna_id))).scalars().all()
            for line in lines:
                prods = (await s.execute(select(FragranceProduct).where(FragranceProduct.line_id == line.line_id))).scalars().all()
                for prod in prods:
                    vars = (await s.execute(select(ProductVariant).where(ProductVariant.product_id == prod.product_id))).scalars().all()
                    for v in vars:
                        obs_list = (await s.execute(
                            select(PriceObservation)
                            .where(PriceObservation.variant_id == v.variant_id)
                        )).scalars().all()
                        for obs in obs_list:
                            ret = (await s.execute(select(Retailer).where(Retailer.retailer_id == obs.retailer_id))).scalar_one_or_none()
                            r_name = ret.name if ret else "Unknown"
                            print(f"Retailer: {r_name} | Price: ${obs.price_amount} | URL: {obs.source_url}")

if __name__ == "__main__":
    asyncio.run(main())
