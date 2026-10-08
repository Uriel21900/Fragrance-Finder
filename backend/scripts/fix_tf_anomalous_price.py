import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, delete

load_dotenv("backend/.env")
load_dotenv(".env")

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.schema import FragranceDNA, FragranceLine, FragranceProduct, ProductVariant, PriceObservation

def get_db_url() -> str:
    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise ValueError("DATABASE_URL environment variable is required.")
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if "sslmode=require" in url:
        url = url.replace("sslmode=require", "ssl=require")
    return url

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
    await engine.dispose()

async def main():
    await fix_tf_price(get_db_url(), "Neon")

if __name__ == '__main__':
    asyncio.run(main())
