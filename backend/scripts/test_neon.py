import os
import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

DATABASE_URL = "postgresql://neondb_owner:npg_iN45StWGXmpK@ep-winter-surf-ay718z8s-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

# Clean connection URL for asyncpg
clean_url = DATABASE_URL
if clean_url.startswith("postgres://"):
    clean_url = clean_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif clean_url.startswith("postgresql://") and "+asyncpg" not in clean_url:
    clean_url = clean_url.replace("postgresql://", "postgresql+asyncpg://", 1)

# Fix query params for asyncpg
if "?" in clean_url:
    base, _ = clean_url.split("?", 1)
    clean_url = f"{base}?ssl=require"

async def test():
    print(f"Testing connection with URL: {clean_url}")
    engine = create_async_engine(clean_url, echo=False)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT count(*) FROM fragrance_dna;"))
        count = res.scalar()
        print(f"Connected to Neon! Found {count} Fragrance DNAs in cloud database.")

if __name__ == "__main__":
    asyncio.run(test())
