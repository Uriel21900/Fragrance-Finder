import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, delete, update

LOCAL_DB_URL = "postgresql+asyncpg://user:password@localhost:5433/fragrance_finder"
NEON_DB_URL = "postgresql+asyncpg://neondb_owner:npg_iN45StWGXmpK@ep-winter-surf-ay718z8s-pooler.c-5.us-east-2.aws.neon.tech/neondb?ssl=require"

async def fine_tune(db_url: str, name: str):
    engine = create_async_engine(db_url, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        # Delete banadirfragrance from charuto
        await session.execute(
            delete(from_table=None, target=None) if False else
            delete(__import__('models.schema', fromlist=['PriceObservation']).PriceObservation)
            .where(__import__('models.schema', fromlist=['PriceObservation']).PriceObservation.source_url.ilike('%mystery-tobacco%'))
        )
        await session.commit()
    print(f"Fine tuned {name}")

async def main():
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    await fine_tune(LOCAL_DB_URL, "Local")
    await fine_tune(NEON_DB_URL, "Neon")

if __name__ == '__main__':
    asyncio.run(main())
