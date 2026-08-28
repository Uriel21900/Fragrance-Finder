import asyncio
import os
import sys
from sqlalchemy import select, func

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import FragranceDNA, Brand, DNARelationship, FragranceLine, FragranceProduct, ProductVariant, PriceObservation, Retailer

async def audit():
    async with async_session_maker() as session:
        total = (await session.execute(select(func.count(FragranceDNA.dna_id)))).scalar()
        print(f"Total FragranceDNA rows: {total}")
        dnas = (await session.execute(
            select(FragranceDNA, Brand)
            .outerjoin(Brand, FragranceDNA.origin_brand_id == Brand.brand_id)
            .order_by(FragranceDNA.sort_key)
        )).all()

        print(f"\n--- AUDIT OF FRAGRANCES IN DB (Count: {len(dnas)}) ---")
        for i, (dna, b) in enumerate(dnas, 1):
            bname = b.name if b else "Unknown"
            
            # Count observations
            obs_count = 0
            lines = (await session.execute(select(FragranceLine).where(FragranceLine.dna_id == dna.dna_id))).scalars().all()
            for line in lines:
                prods = (await session.execute(select(FragranceProduct).where(FragranceProduct.line_id == line.line_id))).scalars().all()
                for p in prods:
                    vars = (await session.execute(select(ProductVariant).where(ProductVariant.product_id == p.product_id))).scalars().all()
                    for v in vars:
                        c = (await session.execute(select(func.count(PriceObservation.price_observation_id)).where(PriceObservation.variant_id == v.variant_id))).scalar()
                        obs_count += c

            # Count clones
            clones_count = (await session.execute(
                select(func.count(DNARelationship.dna_relationship_id))
                .where(DNARelationship.target_dna_id == dna.dna_id)
            )).scalar()

            img = (dna.image_url or "NONE")[:50]
            print(f"[{i}] ID: {dna.dna_id} | {bname} - {dna.canonical_name} | Dupe? {dna.is_dupe} | Obs: {obs_count} | Clones: {clones_count} | Img: {img}")

if __name__ == "__main__":
    asyncio.run(audit())
