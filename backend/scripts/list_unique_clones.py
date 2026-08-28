import asyncio
import os
import sys
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import FragranceDNA, Brand, DNARelationship

async def list_unique_clones():
    async with async_session_maker() as session:
        clones_res = await session.execute(
            select(DNARelationship, FragranceDNA, Brand)
            .join(FragranceDNA, DNARelationship.source_dna_id == FragranceDNA.dna_id)
            .outerjoin(Brand, FragranceDNA.origin_brand_id == Brand.brand_id)
        )
        
        unique = {}
        for rel, clone_dna, brand in clones_res.all():
            bname = brand.name if brand else "Unknown"
            cname = clone_dna.canonical_name
            key = f"{bname} - {cname}"
            if key not in unique:
                # get target fragrance
                target_dna = (await session.execute(
                    select(FragranceDNA, Brand)
                    .outerjoin(Brand, FragranceDNA.origin_brand_id == Brand.brand_id)
                    .where(FragranceDNA.dna_id == rel.target_dna_id)
                )).first()
                t_name = f"{target_dna[1].name} {target_dna[0].canonical_name}" if target_dna else "Unknown"
                unique[key] = {
                    "dna_id": str(clone_dna.dna_id),
                    "brand": bname,
                    "name": cname,
                    "target": t_name,
                    "current_img": clone_dna.image_url
                }
                
        print(f"Total Unique Clones: {len(unique)}")
        for idx, (k, v) in enumerate(unique.items(), 1):
            print(f"{idx}. [{v['brand']}] {v['name']} (Clone of: {v['target']}) -> ID: {v['dna_id']}")

if __name__ == "__main__":
    asyncio.run(list_unique_clones())
