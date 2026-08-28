import asyncio
import os
import sys
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import FragranceDNA, FragranceProduct, FragranceLine, ProductVariant, PriceObservation, Brand

async def purge_all_clone_prices():
    print("=== PURGING ALL CLONE PRICES FROM NON-CLONE FRAGRANCES ===")
    
    clone_keywords = [
        "banadir", "banadirfragrance", "armaf", "afnan", "lattafa", "alhambra",
        "paris-corner", "french-avenue", "zimaya", "bujairami", "fragrance-world",
        "dunhil-desire-gold", "dunhill-desire-gold", "twist", "inspired"
    ]
    
    deleted_count = 0
    async with async_session_maker() as session:
        # Get all non-clone/original DNAs
        dnas_res = await session.execute(
            select(FragranceDNA, Brand)
            .outerjoin(Brand, FragranceDNA.origin_brand_id == Brand.brand_id)
            .where(FragranceDNA.is_dupe == False)
        )
        
        for dna, brand in dnas_res.all():
            brand_norm = brand.normalized_name if brand else ""
            lines = (await session.execute(select(FragranceLine).where(FragranceLine.dna_id == dna.dna_id))).scalars().all()
            for line in lines:
                prods = (await session.execute(select(FragranceProduct).where(FragranceProduct.line_id == line.line_id))).scalars().all()
                for prod in prods:
                    vars = (await session.execute(select(ProductVariant).where(ProductVariant.product_id == prod.product_id))).scalars().all()
                    for v in vars:
                        obs_list = (await session.execute(select(PriceObservation).where(PriceObservation.variant_id == v.variant_id))).scalars().all()
                        for obs in obs_list:
                            u_low = (obs.source_url or "").lower()
                            # If url has clone keywords and brand is not a clone house
                            if any(k in u_low for k in clone_keywords):
                                if brand_norm not in ["banadir_fragrance", "armaf", "afnan", "lattafa", "alfred_dunhill", "paris_corner", "maison_alhambra", "fragrance_world"]:
                                    print(f"Purging [{brand.name if brand else 'N/A'} - {dna.canonical_name}]: {obs.source_url}")
                                    await session.delete(obs)
                                    deleted_count += 1

        await session.commit()
    print(f"Purged {deleted_count} mismatched clone price observations.")

if __name__ == "__main__":
    asyncio.run(purge_all_clone_prices())
