import asyncio
import os
import sys
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import FragranceDNA, Brand, FragranceLine, FragranceProduct, ProductVariant, PriceObservation, Retailer, DNARelationship

async def inspect_all_clones():
    print("=== INSPECTING ALL CLONE FRAGRANCES IN THE DATABASE ===")
    async with async_session_maker() as session:
        # Get all distinct clone DNAs
        clones_res = await session.execute(
            select(FragranceDNA, Brand)
            .join(DNARelationship, DNARelationship.source_dna_id == FragranceDNA.dna_id)
            .outerjoin(Brand, FragranceDNA.origin_brand_id == Brand.brand_id)
            .distinct()
        )
        
        clones = clones_res.all()
        print(f"Total unique clone DNAs linked: {len(clones)}")
        
        for dna, brand in clones:
            bname = brand.name if brand else "Unknown"
            
            # Count prices by retailer
            retailers_found = set()
            lines = (await session.execute(select(FragranceLine).where(FragranceLine.dna_id == dna.dna_id))).scalars().all()
            for line in lines:
                prods = (await session.execute(select(FragranceProduct).where(FragranceProduct.line_id == line.line_id))).scalars().all()
                for prod in prods:
                    vars = (await session.execute(select(ProductVariant).where(ProductVariant.product_id == prod.product_id))).scalars().all()
                    for v in vars:
                        obs_list = (await session.execute(
                            select(PriceObservation, Retailer)
                            .join(Retailer, PriceObservation.retailer_id == Retailer.retailer_id)
                            .where(PriceObservation.variant_id == v.variant_id)
                        )).all()
                        for obs, ret in obs_list:
                            retailers_found.add(ret.name)
                            
            print(f"Clone: [{bname}] {dna.canonical_name} (ID: {dna.dna_id})")
            print(f"  Image: {dna.image_url}")
            print(f"  Retailers ({len(retailers_found)}): {list(retailers_found)}")

if __name__ == "__main__":
    asyncio.run(inspect_all_clones())
