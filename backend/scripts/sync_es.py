import asyncio
import os
import sys

# Add parent dir to path so we can import from backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import async_session_maker
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from models.schema import FragranceDNA
from es_client import es_client, init_es_index

async def sync_fragrances():
    await init_es_index()
    
    async with async_session_maker() as session:
        stmt = select(FragranceDNA).options(selectinload(FragranceDNA.origin_brand))
        result = await session.execute(stmt)
        dnas = result.scalars().all()
        
        if not dnas:
            print("No fragrances found in database to sync.")
            return

        operations = []
        for dna in dnas:
            brand_name = dna.origin_brand.name if dna.origin_brand else "Unknown Brand"
            
            # Action line
            operations.append({"index": {"_index": "fragrances", "_id": str(dna.dna_id)}})
            # Document line
            operations.append({
                "dna_id": str(dna.dna_id), # type: ignore
                "brand_name": brand_name, # type: ignore
                "canonical_name": str(dna.canonical_name), # type: ignore
                "market_segment": str(dna.market_segment.value if hasattr(dna.market_segment, 'value') else dna.market_segment), # type: ignore
                "is_dupe": dna.is_dupe,
                "inspired_by": dna.inspired_by
            })
            
        print(f"Syncing {len(dnas)} fragrances to Elasticsearch...")
        response = await es_client.bulk(operations=operations)
        if response.get("errors"):
            print("Errors occurred during bulk index.")
        else:
            print("Successfully synced all fragrances!")

    await es_client.close()

if __name__ == "__main__":
    asyncio.run(sync_fragrances())
