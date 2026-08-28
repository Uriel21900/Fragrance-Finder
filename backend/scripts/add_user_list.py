import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import async_session_maker
from models.schema import (
    Brand, FragranceDNA, FragranceLine, FragranceProduct, ProductVariant,
    FragranceMarketSegment, FragranceGenderMarketing, DNARelationship, RelationType
)
from sqlalchemy import select

FRAGRANCES = [
    # Middle Eastern / High-Value (Many are clones)
    {"brand": "French Avenue", "name": "Liquid Brun", "segment": FragranceMarketSegment.clone, "inspired_by": ("Parfums de Marly", "Althaïr")},
    {"brand": "French Avenue", "name": "Francique 63.55", "segment": FragranceMarketSegment.clone, "inspired_by": ("BDK Parfums", "Gris Charnel")},
    {"brand": "Lattafa", "name": "Khamrah", "segment": FragranceMarketSegment.clone, "inspired_by": ("By Kilian", "Angels' Share")},
    {"brand": "Lattafa", "name": "Asad", "segment": FragranceMarketSegment.clone, "inspired_by": ("Dior", "Sauvage Elixir")},
    {"brand": "Lattafa", "name": "Vintage Radio", "segment": FragranceMarketSegment.clone, "inspired_by": ("Initio Parfums Prives", "Paragon")},
    {"brand": "Lattafa", "name": "Liam Grey", "segment": FragranceMarketSegment.clone, "inspired_by": ("BDK Parfums", "Gris Charnel")},
    {"brand": "Lattafa", "name": "Yara", "segment": FragranceMarketSegment.clone}, # Very popular standalone clone
    {"brand": "Armaf", "name": "Club de Nuit Intense Man", "segment": FragranceMarketSegment.clone, "inspired_by": ("Creed", "Aventus")},
    {"brand": "Armaf", "name": "Club de Nuit Untold", "segment": FragranceMarketSegment.clone, "inspired_by": ("Maison Francis Kurkdjian", "Baccarat Rouge 540")},
    {"brand": "Maison Alhambra", "name": "Kismet Magic", "segment": FragranceMarketSegment.clone, "inspired_by": ("By Kilian", "Angels' Share")},
    {"brand": "Maison Alhambra", "name": "Woody Oud", "segment": FragranceMarketSegment.clone, "inspired_by": ("Tom Ford", "Oud Wood")},
    {"brand": "Maison Alhambra", "name": "Toscano Leather", "segment": FragranceMarketSegment.clone, "inspired_by": ("Tom Ford", "Tuscan Leather")},
    {"brand": "Bujairami", "name": "Power", "segment": FragranceMarketSegment.clone, "inspired_by": ("Creed", "Aventus")},
    {"brand": "Rasasi", "name": "Hawas", "segment": FragranceMarketSegment.designer, "inspired_by": ("Paco Rabanne", "Invictus Aqua")},
    {"brand": "Afnan", "name": "9pm", "segment": FragranceMarketSegment.clone, "inspired_by": ("Jean Paul Gaultier", "Ultra Male")},
    {"brand": "Afnan", "name": "Turathi Blue", "segment": FragranceMarketSegment.clone, "inspired_by": ("Bvlgari", "Tygar")},
    {"brand": "Zimaya", "name": "Sharaf Blend", "segment": FragranceMarketSegment.clone, "inspired_by": ("By Kilian", "Angels' Share")},

    # Designer Heavyweights
    {"brand": "Versace", "name": "Eros", "segment": FragranceMarketSegment.designer},
    {"brand": "Versace", "name": "Eros Flame", "segment": FragranceMarketSegment.designer},
    {"brand": "Dior", "name": "Sauvage Elixir", "segment": FragranceMarketSegment.designer},
    {"brand": "Chanel", "name": "Bleu de Chanel", "segment": FragranceMarketSegment.designer},
    {"brand": "Yves Saint Laurent", "name": "Y Eau de Parfum", "segment": FragranceMarketSegment.designer},
    {"brand": "Yves Saint Laurent", "name": "MYSLF", "segment": FragranceMarketSegment.designer},
    {"brand": "Jean Paul Gaultier", "name": "Le Male Le Parfum", "segment": FragranceMarketSegment.designer},
    {"brand": "Jean Paul Gaultier", "name": "Le Beau Le Parfum", "segment": FragranceMarketSegment.designer},
    {"brand": "Jean Paul Gaultier", "name": "Ultra Male", "segment": FragranceMarketSegment.designer},
    {"brand": "Viktor&Rolf", "name": "Spicebomb Extreme", "segment": FragranceMarketSegment.designer},
    {"brand": "Azzaro", "name": "The Most Wanted", "segment": FragranceMarketSegment.designer},
    {"brand": "Emporio Armani", "name": "Stronger With You Intensely", "segment": FragranceMarketSegment.designer},
    {"brand": "Giorgio Armani", "name": "Acqua di Giò Profumo", "segment": FragranceMarketSegment.designer},
    {"brand": "Hugo Boss", "name": "Boss Bottled Elixir", "segment": FragranceMarketSegment.designer},
    {"brand": "Paco Rabanne", "name": "1 Million Royal", "segment": FragranceMarketSegment.designer},
    {"brand": "Paco Rabanne", "name": "Invictus Aqua", "segment": FragranceMarketSegment.designer},
    {"brand": "Tom Ford", "name": "Ombré Leather", "segment": FragranceMarketSegment.designer},
    {"brand": "Tom Ford", "name": "Tobacco Vanille", "segment": FragranceMarketSegment.designer},
    {"brand": "Tom Ford", "name": "Tuscan Leather", "segment": FragranceMarketSegment.designer},
    {"brand": "Tom Ford", "name": "Oud Wood", "segment": FragranceMarketSegment.designer},
    {"brand": "Hermès", "name": "Terre d'Hermès", "segment": FragranceMarketSegment.designer},
    {"brand": "Bvlgari", "name": "Tygar", "segment": FragranceMarketSegment.designer},

    # Niche & Luxury Icons
    {"brand": "By Kilian", "name": "Angels' Share", "segment": FragranceMarketSegment.niche},
    {"brand": "Maison Francis Kurkdjian", "name": "Baccarat Rouge 540", "segment": FragranceMarketSegment.niche},
    {"brand": "Maison Francis Kurkdjian", "name": "Grand Soir", "segment": FragranceMarketSegment.niche},
    {"brand": "Creed", "name": "Aventus", "segment": FragranceMarketSegment.niche},
    {"brand": "Creed", "name": "Silver Mountain Water", "segment": FragranceMarketSegment.niche},
    {"brand": "Parfums de Marly", "name": "Layton", "segment": FragranceMarketSegment.niche},
    {"brand": "Parfums de Marly", "name": "Althaïr", "segment": FragranceMarketSegment.niche},
    {"brand": "Parfums de Marly", "name": "Delina", "segment": FragranceMarketSegment.niche},
    {"brand": "Xerjoff", "name": "Naxos", "segment": FragranceMarketSegment.niche},
    {"brand": "Xerjoff", "name": "Erba Pura", "segment": FragranceMarketSegment.niche},
    {"brand": "Xerjoff", "name": "Torino21", "segment": FragranceMarketSegment.niche},
    {"brand": "Maison Crivelli", "name": "Oud Maracujá", "segment": FragranceMarketSegment.niche},
    {"brand": "Nishane", "name": "Hacivat", "segment": FragranceMarketSegment.niche},
    {"brand": "Nishane", "name": "Ani", "segment": FragranceMarketSegment.niche},
    {"brand": "Initio Parfums Prives", "name": "Oud for Greatness", "segment": FragranceMarketSegment.niche},
    {"brand": "Initio Parfums Prives", "name": "Side Effect", "segment": FragranceMarketSegment.niche},
    {"brand": "Initio Parfums Prives", "name": "Paragon", "segment": FragranceMarketSegment.niche},
    {"brand": "Mancera", "name": "Red Tobacco", "segment": FragranceMarketSegment.niche},
    {"brand": "Mancera", "name": "Intense Cedrat Boise", "segment": FragranceMarketSegment.niche},
    {"brand": "Giardini Di Toscana", "name": "Bianco Latte", "segment": FragranceMarketSegment.niche},
    {"brand": "BDK Parfums", "name": "Gris Charnel", "segment": FragranceMarketSegment.niche},
]

async def get_or_create_brand(session, brand_name):
    norm = brand_name.lower().replace(" ", "_")
    result = await session.execute(select(Brand).filter_by(normalized_name=norm))
    brand = result.scalar_one_or_none()
    if not brand:
        brand = Brand(name=brand_name, normalized_name=norm)
        session.add(brand)
        await session.flush()
    return brand

async def create_dna(session, brand, item):
    norm = item["name"].lower().replace(" ", "_")
    result = await session.execute(select(FragranceDNA).filter_by(normalized_name=norm, origin_brand_id=brand.brand_id))
    dna = result.scalar_one_or_none()
    
    if not dna:
        sort_k = item["name"]
        for article in ['The ', 'Le ', 'La ', 'L\'', 'L ']:
            if sort_k.lower().startswith(article.lower()):
                sort_k = f"{sort_k[len(article):]}, {article.strip()}"
                break
                
        dna = FragranceDNA(
            canonical_name=item["name"],
            normalized_name=norm,
            sort_key=sort_k,
            origin_brand_id=brand.brand_id,
            market_segment=item["segment"],
            is_original_dna=(item["segment"] != FragranceMarketSegment.clone)
        )
        session.add(dna)
        await session.flush()
        
        # Create default line and product variants
        line_norm = f"{dna.normalized_name}_line"
        line = FragranceLine(
            brand_id=brand.brand_id,
            dna_id=dna.dna_id,
            name=f"{dna.canonical_name} Line",
            normalized_name=line_norm,
            marketing_gender=FragranceGenderMarketing.unisex
        )
        session.add(line)
        await session.flush()
        
        prod = FragranceProduct(
            line_id=line.line_id,
            formulation_version=f"{dna.normalized_name}_eau_de_parfum"
        )
        session.add(prod)
        await session.flush()
        
        var = ProductVariant(
            product_id=prod.product_id,
            volume_ml=100.0,
            package_type="spray"
        )
        session.add(var)
        await session.flush()
        
    return dna

async def seed():
    print("Seeding user requested list...")
    
    async with async_session_maker() as session:
        dna_map = {}
        
        for item in FRAGRANCES:
            brand = await get_or_create_brand(session, item["brand"])
            dna = await create_dna(session, brand, item)
            dna_map[(item["brand"], item["name"])] = dna.dna_id
            
        print(f"Inserted {len(FRAGRANCES)} fragrances.")
            
        clones_inserted = 0
        for item in FRAGRANCES:
            if "inspired_by" in item:
                source_id = dna_map.get((item["brand"], item["name"]))
                target_key = item["inspired_by"]
                target_id = dna_map.get(target_key)
                
                if source_id and target_id:
                    # Create relationship
                    result = await session.execute(
                        select(DNARelationship).filter_by(
                            source_dna_id=source_id, 
                            target_dna_id=target_id,
                            relationship_type=RelationType.inspired_by
                        )
                    )
                    if not result.scalar_one_or_none():
                        rel = DNARelationship(
                            source_dna_id=source_id,
                            target_dna_id=target_id,
                            relationship_type=RelationType.inspired_by,
                            confidence_score=0.95
                        )
                        session.add(rel)
                        clones_inserted += 1
                        
        print(f"Inserted {clones_inserted} inspired_by relationships.")
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed())
