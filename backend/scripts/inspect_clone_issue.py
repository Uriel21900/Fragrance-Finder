import asyncio
import os
import sys
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import FragranceDNA, Brand, FragranceLine, FragranceProduct, ProductVariant, PriceObservation, Retailer, DNARelationship

async def check():
    async with async_session_maker() as session:
        # Check specific ID
        res = await session.execute(
            select(FragranceDNA, Brand)
            .outerjoin(Brand, FragranceDNA.origin_brand_id == Brand.brand_id)
            .where(FragranceDNA.dna_id == "1579e8cd-b1d9-41fe-89d4-eb86a3b25690")
        )
        row = res.first()
        if row:
            dna, brand = row
            print(f"Target DNA: [{brand.name if brand else None}] - {dna.canonical_name}")
            print(f"Image URL: {dna.image_url}")
            lines = (await session.execute(select(FragranceLine).where(FragranceLine.dna_id == dna.dna_id))).scalars().all()
            for line in lines:
                prods = (await session.execute(select(FragranceProduct).where(FragranceProduct.line_id == line.line_id))).scalars().all()
                for prod in prods:
                    vars = (await session.execute(select(ProductVariant).where(ProductVariant.product_id == prod.product_id))).scalars().all()
                    for v in vars:
                        obs_list = (await session.execute(select(PriceObservation, Retailer).join(Retailer, PriceObservation.retailer_id == Retailer.retailer_id).where(PriceObservation.variant_id == v.variant_id))).all()
                        print(f"  Variant {v.volume_ml}ml {v.package_type}: {len(obs_list)} prices")
                        for obs, ret in obs_list:
                            print(f"    [{ret.name}] ${obs.price_amount}: {obs.source_url}")
        return
                            
        print("\n--- ALL CLONES IN RELATIONSHIPS ---")
        clones_res = await session.execute(
            select(DNARelationship, FragranceDNA, Brand)
            .join(FragranceDNA, DNARelationship.source_dna_id == FragranceDNA.dna_id)
            .outerjoin(Brand, FragranceDNA.origin_brand_id == Brand.brand_id)
        )
        for rel, clone_dna, brand in clones_res.all():
            lines = (await session.execute(select(FragranceLine).where(FragranceLine.dna_id == clone_dna.dna_id))).scalars().all()
            total_obs = 0
            for line in lines:
                prods = (await session.execute(select(FragranceProduct).where(FragranceProduct.line_id == line.line_id))).scalars().all()
                for prod in prods:
                    vars = (await session.execute(select(ProductVariant).where(ProductVariant.product_id == prod.product_id))).scalars().all()
                    for v in vars:
                        obs_list = (await session.execute(select(PriceObservation).where(PriceObservation.variant_id == v.variant_id))).scalars().all()
                        total_obs += len(obs_list)
            print(f"Clone: {brand.name if brand else 'N/A'} - {clone_dna.canonical_name} (ID: {clone_dna.dna_id}) | Img: {clone_dna.image_url} | Price Obs: {total_obs}")

if __name__ == "__main__":
    asyncio.run(check())
