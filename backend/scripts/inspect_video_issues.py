import asyncio
import os
import sys
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import FragranceDNA, FragranceLine, FragranceProduct, ProductVariant, PriceObservation, Retailer

async def inspect():
    async with async_session_maker() as session:
        names = ["Charuto Tobacco Vanille", "Aventus", "Desire Gold", "Tobacco Vanille"]
        for name in names:
            dnas = (await session.execute(select(FragranceDNA).where(FragranceDNA.canonical_name.ilike(f"%{name}%")))).scalars().all()
            print("=" * 70)
            print(f"QUERY: {name} (Found {len(dnas)} DNAs)")
            for d in dnas:
                print(f"DNA: [{d.canonical_name}] (ID: {d.dna_id}) | Image: {d.image_url} | IsDupe: {d.is_dupe}")
                
                # Fetch price observations
                stmt = (
                    select(PriceObservation, Retailer.name.label("ret_name"))
                    .join(ProductVariant, PriceObservation.variant_id == ProductVariant.variant_id)
                    .join(FragranceProduct, ProductVariant.product_id == FragranceProduct.product_id)
                    .join(FragranceLine, FragranceProduct.line_id == FragranceLine.line_id)
                    .outerjoin(Retailer, PriceObservation.retailer_id == Retailer.retailer_id)
                    .where(FragranceLine.dna_id == d.dna_id)
                )
                prices = (await session.execute(stmt)).all()
                print(f"  -> {len(prices)} Price Observations:")
                for obs, ret_name in prices:
                    print(f"     * [{ret_name}] ${obs.price_amount:.2f} | URL: {obs.source_url}")

if __name__ == "__main__":
    asyncio.run(inspect())
