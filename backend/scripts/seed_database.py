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

# Original Fragrances Data
FRAGRANCES = [
    # Creed
    {"brand": "Creed", "name": "Aventus", "segment": FragranceMarketSegment.niche},
    {"brand": "Creed", "name": "Green Irish Tweed", "segment": FragranceMarketSegment.niche},
    {"brand": "Creed", "name": "Silver Mountain Water", "segment": FragranceMarketSegment.niche},
    {"brand": "Creed", "name": "Millesime Imperial", "segment": FragranceMarketSegment.niche},
    {"brand": "Creed", "name": "Aventus Cologne", "segment": FragranceMarketSegment.niche},
    {"brand": "Creed", "name": "Original Santal", "segment": FragranceMarketSegment.niche},
    {"brand": "Creed", "name": "Royal Oud", "segment": FragranceMarketSegment.niche},
    
    # Parfums De Marly
    {"brand": "Parfums De Marly", "name": "Layton", "segment": FragranceMarketSegment.niche},
    {"brand": "Parfums De Marly", "name": "Herod", "segment": FragranceMarketSegment.niche},
    {"brand": "Parfums De Marly", "name": "Pegasus", "segment": FragranceMarketSegment.niche},
    {"brand": "Parfums De Marly", "name": "Sedley", "segment": FragranceMarketSegment.niche},
    {"brand": "Parfums De Marly", "name": "Greenley", "segment": FragranceMarketSegment.niche},
    {"brand": "Parfums De Marly", "name": "Percival", "segment": FragranceMarketSegment.niche},
    {"brand": "Parfums De Marly", "name": "Carlisle", "segment": FragranceMarketSegment.niche},
    {"brand": "Parfums De Marly", "name": "Oajan", "segment": FragranceMarketSegment.niche},
    
    # Maison Francis Kurkdjian
    {"brand": "Maison Francis Kurkdjian", "name": "Baccarat Rouge 540", "segment": FragranceMarketSegment.niche},
    {"brand": "Maison Francis Kurkdjian", "name": "Grand Soir", "segment": FragranceMarketSegment.niche},
    {"brand": "Maison Francis Kurkdjian", "name": "Gentle Fluidity Silver", "segment": FragranceMarketSegment.niche},
    {"brand": "Maison Francis Kurkdjian", "name": "Oud Satin Mood", "segment": FragranceMarketSegment.niche},
    {"brand": "Maison Francis Kurkdjian", "name": "L'Homme A La Rose", "segment": FragranceMarketSegment.niche},
    
    # Tom Ford
    {"brand": "Tom Ford", "name": "Oud Wood", "segment": FragranceMarketSegment.designer},
    {"brand": "Tom Ford", "name": "Tobacco Vanille", "segment": FragranceMarketSegment.designer},
    {"brand": "Tom Ford", "name": "Tuscan Leather", "segment": FragranceMarketSegment.designer},
    {"brand": "Tom Ford", "name": "Ombre Leather", "segment": FragranceMarketSegment.designer},
    {"brand": "Tom Ford", "name": "Noir Extreme", "segment": FragranceMarketSegment.designer},
    {"brand": "Tom Ford", "name": "Neroli Portofino", "segment": FragranceMarketSegment.designer},
    {"brand": "Tom Ford", "name": "Lost Cherry", "segment": FragranceMarketSegment.designer},
    
    # Dior
    {"brand": "Dior", "name": "Sauvage", "segment": FragranceMarketSegment.designer},
    {"brand": "Dior", "name": "Sauvage Elixir", "segment": FragranceMarketSegment.designer},
    {"brand": "Dior", "name": "Dior Homme Intense", "segment": FragranceMarketSegment.designer},
    {"brand": "Dior", "name": "Fahrenheit", "segment": FragranceMarketSegment.designer},
    {"brand": "Dior", "name": "Ambre Nuit", "segment": FragranceMarketSegment.designer},
    
    # Chanel
    {"brand": "Chanel", "name": "Bleu De Chanel", "segment": FragranceMarketSegment.designer},
    {"brand": "Chanel", "name": "Allure Homme Sport Eau Extreme", "segment": FragranceMarketSegment.designer},
    {"brand": "Chanel", "name": "Platinum Egoiste", "segment": FragranceMarketSegment.designer},
    {"brand": "Chanel", "name": "Sycomore", "segment": FragranceMarketSegment.designer},
    {"brand": "Chanel", "name": "Coromandel", "segment": FragranceMarketSegment.designer},
    
    # Yves Saint Laurent
    {"brand": "Yves Saint Laurent", "name": "Y", "segment": FragranceMarketSegment.designer},
    {"brand": "Yves Saint Laurent", "name": "La Nuit De L'Homme", "segment": FragranceMarketSegment.designer},
    {"brand": "Yves Saint Laurent", "name": "Tuxedo", "segment": FragranceMarketSegment.designer},
    {"brand": "Yves Saint Laurent", "name": "Kouros", "segment": FragranceMarketSegment.designer},
    {"brand": "Yves Saint Laurent", "name": "L'Homme", "segment": FragranceMarketSegment.designer},
    
    # Versace
    {"brand": "Versace", "name": "Eros", "segment": FragranceMarketSegment.designer},
    {"brand": "Versace", "name": "Dylan Blue", "segment": FragranceMarketSegment.designer},
    {"brand": "Versace", "name": "Pour Homme", "segment": FragranceMarketSegment.designer},
    {"brand": "Versace", "name": "The Dreamer", "segment": FragranceMarketSegment.designer},
    
    # Xerjoff
    {"brand": "Xerjoff", "name": "Naxos", "segment": FragranceMarketSegment.niche},
    {"brand": "Xerjoff", "name": "Alexandria II", "segment": FragranceMarketSegment.niche},
    {"brand": "Xerjoff", "name": "Erba Pura", "segment": FragranceMarketSegment.niche},
    {"brand": "Xerjoff", "name": "Renaissance", "segment": FragranceMarketSegment.niche},
    
    # Roja Parfums
    {"brand": "Roja Parfums", "name": "Elysium", "segment": FragranceMarketSegment.niche},
    {"brand": "Roja Parfums", "name": "Enigma", "segment": FragranceMarketSegment.niche},
    {"brand": "Roja Parfums", "name": "Danger", "segment": FragranceMarketSegment.niche},
    {"brand": "Roja Parfums", "name": "Scandal", "segment": FragranceMarketSegment.niche},
    
    # Initio
    {"brand": "Initio Parfums Prives", "name": "Oud for Greatness", "segment": FragranceMarketSegment.niche},
    {"brand": "Initio Parfums Prives", "name": "Side Effect", "segment": FragranceMarketSegment.niche},
    {"brand": "Initio Parfums Prives", "name": "Rehab", "segment": FragranceMarketSegment.niche},
    {"brand": "Initio Parfums Prives", "name": "Musk Therapy", "segment": FragranceMarketSegment.niche},
    
    # Giorgio Armani
    {"brand": "Giorgio Armani", "name": "Acqua Di Gio Profumo", "segment": FragranceMarketSegment.designer},
    {"brand": "Giorgio Armani", "name": "Stronger With You Intensely", "segment": FragranceMarketSegment.designer},
    {"brand": "Giorgio Armani", "name": "Armani Code Profumo", "segment": FragranceMarketSegment.designer},
    
    # Jean Paul Gaultier
    {"brand": "Jean Paul Gaultier", "name": "Le Male Le Parfum", "segment": FragranceMarketSegment.designer},
    {"brand": "Jean Paul Gaultier", "name": "Ultra Male", "segment": FragranceMarketSegment.designer},
    
    # Azzaro
    {"brand": "Azzaro", "name": "The Most Wanted", "segment": FragranceMarketSegment.designer},
    {"brand": "Azzaro", "name": "Wanted By Night", "segment": FragranceMarketSegment.designer},
    
    # Paco Rabanne
    {"brand": "Paco Rabanne", "name": "1 Million", "segment": FragranceMarketSegment.designer},
    {"brand": "Paco Rabanne", "name": "Invictus", "segment": FragranceMarketSegment.designer},
    
    # Prada
    {"brand": "Prada", "name": "L'Homme", "segment": FragranceMarketSegment.designer},
    {"brand": "Prada", "name": "Luna Rossa Black", "segment": FragranceMarketSegment.designer},
    {"brand": "Prada", "name": "Luna Rossa Carbon", "segment": FragranceMarketSegment.designer}
]

# Clone Fragrances Data
CLONES = [
    # Aventus Clones
    {"brand": "Armaf", "name": "Club De Nuit Intense Man", "segment": FragranceMarketSegment.clone, "inspired_by": ("Creed", "Aventus")},
    {"brand": "Montblanc", "name": "Explorer", "segment": FragranceMarketSegment.designer, "inspired_by": ("Creed", "Aventus")},
    {"brand": "Afnan", "name": "Supremacy Silver", "segment": FragranceMarketSegment.clone, "inspired_by": ("Creed", "Aventus")},
    {"brand": "Lattafa", "name": "Asad", "segment": FragranceMarketSegment.clone, "inspired_by": ("Dior", "Sauvage Elixir")},
    
    # Green Irish Tweed Clones
    {"brand": "Armaf", "name": "Tres Nuit", "segment": FragranceMarketSegment.clone, "inspired_by": ("Creed", "Green Irish Tweed")},
    {"brand": "Davidoff", "name": "Cool Water", "segment": FragranceMarketSegment.designer, "inspired_by": ("Creed", "Green Irish Tweed")},
    
    # Silver Mountain Water Clones
    {"brand": "Armaf", "name": "Club De Nuit Sillage", "segment": FragranceMarketSegment.clone, "inspired_by": ("Creed", "Silver Mountain Water")},
    
    # Millesime Imperial Clones
    {"brand": "Armaf", "name": "Club De Nuit Milestone", "segment": FragranceMarketSegment.clone, "inspired_by": ("Creed", "Millesime Imperial")},
    
    # Baccarat Rouge 540 Clones
    {"brand": "Ariana Grande", "name": "Cloud", "segment": FragranceMarketSegment.celebrity, "inspired_by": ("Maison Francis Kurkdjian", "Baccarat Rouge 540")},
    {"brand": "Armaf", "name": "Club De Nuit Untold", "segment": FragranceMarketSegment.clone, "inspired_by": ("Maison Francis Kurkdjian", "Baccarat Rouge 540")},
    {"brand": "Lattafa", "name": "Ana Abiyedh Rouge", "segment": FragranceMarketSegment.clone, "inspired_by": ("Maison Francis Kurkdjian", "Baccarat Rouge 540")},
    
    # Layton Clones
    {"brand": "Al Haramain", "name": "Detour Noir", "segment": FragranceMarketSegment.clone, "inspired_by": ("Parfums De Marly", "Layton")},
    
    # Oud Wood Clones
    {"brand": "Maison Alhambra", "name": "Woody Oud", "segment": FragranceMarketSegment.clone, "inspired_by": ("Tom Ford", "Oud Wood")},
    
    # Tobacco Vanille Clones
    {"brand": "Maison Alhambra", "name": "Tobacco Touch", "segment": FragranceMarketSegment.clone, "inspired_by": ("Tom Ford", "Tobacco Vanille")},
    
    # Tuscan Leather Clones
    {"brand": "Maison Alhambra", "name": "Toscano Leather", "segment": FragranceMarketSegment.clone, "inspired_by": ("Tom Ford", "Tuscan Leather")},
    
    # Lost Cherry Clones
    {"brand": "Maison Alhambra", "name": "Lovely Cherie", "segment": FragranceMarketSegment.clone, "inspired_by": ("Tom Ford", "Lost Cherry")},
    
    # Erba Pura Clones
    {"brand": "Al Haramain", "name": "Amber Oud Gold Edition", "segment": FragranceMarketSegment.clone, "inspired_by": ("Xerjoff", "Erba Pura")},
    
    # YSL Tuxedo Clones
    {"brand": "Maison Alhambra", "name": "Kismet For Men", "segment": FragranceMarketSegment.clone, "inspired_by": ("Yves Saint Laurent", "Tuxedo")},
    
    # Initio Oud for Greatness Clones
    {"brand": "Lattafa", "name": "Bade'e Al Oud Oud for Glory", "segment": FragranceMarketSegment.clone, "inspired_by": ("Initio Parfums Prives", "Oud for Greatness")},
    
    # Tom Ford Neroli Portofino Clones
    {"brand": "Maison Alhambra", "name": "Porto Neroli", "segment": FragranceMarketSegment.clone, "inspired_by": ("Tom Ford", "Neroli Portofino")},
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

async def create_dna(session, brand, item, is_original=True):
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
            is_original_dna=is_original
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
    print("Seeding database with hundreds of fragrances...")
    
    async with async_session_maker() as session:
        dna_map = {}
        
        # 1. Insert originals
        for item in FRAGRANCES:
            brand = await get_or_create_brand(session, item["brand"])
            dna = await create_dna(session, brand, item, True)
            dna_map[(item["brand"], item["name"])] = dna.dna_id
            
        print(f"Inserted {len(FRAGRANCES)} original fragrances.")
            
        # 2. Insert clones and relationships
        clones_inserted = 0
        for item in CLONES:
            brand = await get_or_create_brand(session, item["brand"])
            dna = await create_dna(session, brand, item, False)
            
            # Map inspired_by
            if "inspired_by" in item:
                target_key = item["inspired_by"]
                if target_key in dna_map:
                    target_dna_id = dna_map[target_key]
                    
                    # Create relationship
                    result = await session.execute(
                        select(DNARelationship).filter_by(
                            source_dna_id=dna.dna_id, 
                            target_dna_id=target_dna_id,
                            relationship_type=RelationType.inspired_by
                        )
                    )
                    if not result.scalar_one_or_none():
                        rel = DNARelationship(
                            source_dna_id=dna.dna_id,
                            target_dna_id=target_dna_id,
                            relationship_type=RelationType.inspired_by,
                            confidence_score=0.95
                        )
                        session.add(rel)
                        clones_inserted += 1
                        
        print(f"Inserted {len(CLONES)} clone fragrances and {clones_inserted} inspired_by relationships.")
        await session.commit()
        
    print("Database seeding complete!")

if __name__ == "__main__":
    asyncio.run(seed())
