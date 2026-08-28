import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, delete

LOCAL_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/fragrance_finder"
NEON_DB_URL = "postgresql+asyncpg://neondb_owner:npg_iN45StWGXmpK@ep-winter-surf-ay718z8s-pooler.c-5.us-east-2.aws.neon.tech/neondb?ssl=require"

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.schema import FragranceDNA, FragranceLine, FragranceProduct, ProductVariant, PriceObservation

async def fix_tf_price(db_url: str, name: str):
    engine = create_async_engine(db_url, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        # Find TF Tobacco Vanille variants
        var_ids = (await session.execute(
            select(ProductVariant.variant_id)
            .join(FragranceProduct, ProductVariant.product_id == FragranceProduct.product_id)
            .join(FragranceLine, FragranceProduct.line_id == FragranceLine.line_id)
            .join(FragranceDNA, FragranceLine.dna_id == FragranceDNA.dna_id)
            .where(FragranceDNA.canonical_name == 'Tobacco Vanille', FragranceDNA.is_dupe == False)
        )).scalars().all()
        
        if var_ids:
            # Delete any price observation under $150 on authentic Tom Ford Tobacco Vanille full bottles
            d_stmt = delete(PriceObservation).where(
                PriceObservation.variant_id.in_(var_ids),
                PriceObservation.price_amount < 150.0
            )
            res = await session.execute(d_stmt)
            print(f"Deleted {res.rowcount} anomalous low prices on TF Tobacco Vanille in {name}")
            await session.commit()

async def main():
    await fix_tf_price(LOCAL_DB_URL, "Local")
    await fix_tf_price(NEON_DB_URL, "Neon")

if __name__ == '__main__':
    asyncio.run(main())
