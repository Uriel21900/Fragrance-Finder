import asyncio
import os
import sys
import csv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import async_session_maker
from models.schema import (
    Brand, FragranceDNA, FragranceLine, FragranceProduct, ProductVariant,
    FragranceMarketSegment, FragranceGenderMarketing
)
from sqlalchemy import select

async def ingest():
    print("Ingesting Parfumo 35k Fragrance Dataset...")
    
    csv_file = os.path.join(os.path.dirname(__file__), "..", "parfumo.csv")
    if not os.path.exists(csv_file):
        print(f"File {csv_file} not found!")
        return

    # We will bulk insert to save time, but we need to handle brands first.
    # To keep it memory efficient and fast, we'll collect unique brands, insert them,
    # then map their IDs to DNAs.
    brands_set = set()
    dna_data = []
    
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            brand_name = row.get("Brand", "").strip()
            name = row.get("Name", "").strip()
            if not brand_name or not name:
                continue
                
            brands_set.add(brand_name)
            dna_data.append({
                "brand": brand_name,
                "name": name,
            })
            if i >= 10000: # Limit to 10k to prevent locking the database for too long on prototype
                break
                
    print(f"Extracted {len(brands_set)} unique brands and {len(dna_data)} fragrances.")

    async with async_session_maker() as session:
        # Get existing brands
        result = await session.execute(select(Brand.normalized_name, Brand.brand_id))
        brand_map = {norm: str(id) for norm, id in result.all()}
        
        # Insert missing brands
        new_brands = []
        for b_name in brands_set:
            norm = b_name.lower().replace(" ", "_")
            if norm not in brand_map:
                b = Brand(name=b_name, normalized_name=norm)
                new_brands.append(b)
                # update brand map immediately so we don't try to insert same normalized name twice
                # if there are multiple variations of the same name in brands_set
                brand_map[norm] = 'pending'
                
        if new_brands:
            session.add_all(new_brands)
            await session.commit()
            
            # Re-fetch map
            result = await session.execute(select(Brand.normalized_name, Brand.brand_id))
            brand_map = {norm: str(id) for norm, id in result.all()}
            
        print(f"Brands synced. Inserting DNAs...")
        
        # Insert DNAs
        # Instead of raw bulk_insert which bypasses ORM mapping, we will batch add
        batch_size = 1000
        
        # Track inserted DNAs to prevent duplicate errors from the CSV
        result = await session.execute(select(FragranceDNA.origin_brand_id, FragranceDNA.normalized_name))
        added_dnas = {(str(b_id), n_name) for b_id, n_name in result.all()}
        
        for i in range(0, len(dna_data), batch_size):
            batch = dna_data[i:i+batch_size]
            
            for item in batch:
                brand_norm = item["brand"].lower().replace(" ", "_")
                brand_id = brand_map.get(brand_norm)
                if not brand_id or brand_id == 'pending': continue
                
                norm = item["name"].lower().replace(" ", "_")
                
                # Check for duplicates
                if (brand_id, norm) in added_dnas:
                    continue
                
                sort_k = item["name"]
                for article in ['The ', 'Le ', 'La ', 'L\'', 'L ']:
                    if sort_k.lower().startswith(article.lower()):
                        sort_k = f"{sort_k[len(article):]}, {article.strip()}"
                        break
                        
                dna = FragranceDNA(
                    canonical_name=item["name"],
                    normalized_name=norm,
                    sort_key=sort_k,
                    origin_brand_id=brand_id,
                    market_segment=FragranceMarketSegment.designer, # Default assumption for mass import
                    is_original_dna=True
                )
                session.add(dna)
                added_dnas.add((brand_id, norm))
            
            await session.commit()
            print(f"Inserted batch {i//batch_size + 1}")
            
    print("Ingestion complete!")

if __name__ == "__main__":
    asyncio.run(ingest())
