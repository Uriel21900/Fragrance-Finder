import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, delete, update

load_dotenv("backend/.env")
load_dotenv(".env")

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

async def fine_tune(db_url: str, name: str):
    engine = create_async_engine(db_url, echo=False)
    session_maker = async_sessionmaker(engine, expire_on_commit=False)
    async with session_maker() as session:
        from models.schema import PriceObservation
        await session.execute(
            delete(PriceObservation).where(PriceObservation.source_url.ilike('%mystery-tobacco%'))
        )
        await session.commit()
    print(f"Fine tuned {name}")
    await engine.dispose()

async def main():
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_url = get_db_url()
    await fine_tune(db_url, "Neon")

if __name__ == '__main__':
    asyncio.run(main())
