import os
import sys
import asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

load_dotenv("backend/.env")
load_dotenv(".env")

raw_url = os.getenv("DATABASE_URL", "")
if not raw_url:
    raise ValueError("DATABASE_URL environment variable is required. Please set it in backend/.env")

# Clean connection URL for asyncpg
clean_url = raw_url
if clean_url.startswith("postgres://"):
    clean_url = clean_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif clean_url.startswith("postgresql://") and "+asyncpg" not in clean_url:
    clean_url = clean_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Fix query params for asyncpg
if "?" in clean_url:
    base, _ = clean_url.split("?", 1)
    clean_url = f"{base}?ssl=require"
elif "ssl=" not in clean_url:
    clean_url = f"{clean_url}?ssl=require"

async def test():
    masked_url = clean_url.split("@")[-1] if "@" in clean_url else clean_url
    print(f"Testing connection to host: {masked_url}")
    engine = create_async_engine(clean_url, echo=False)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT count(*) FROM fragrance_dna;"))
        count = res.scalar()
        print(f"Connected to Neon! Found {count} Fragrance DNAs in cloud database.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(test())
