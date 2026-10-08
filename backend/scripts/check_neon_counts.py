import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

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

async def check():
    engine = create_async_engine(get_db_url(), echo=False)
    async with engine.connect() as conn:
        dnas = await conn.execute(text("SELECT count(*) FROM fragrance_dna;"))
        lines = await conn.execute(text("SELECT count(*) FROM fragrance_line;"))
        prods = await conn.execute(text("SELECT count(*) FROM fragrance_product;"))
        vars = await conn.execute(text("SELECT count(*) FROM product_variant;"))
        prices = await conn.execute(text("SELECT count(*) FROM price_observation;"))
        
        print("Neon Database Content:")
        print(f"  Fragrance DNAs: {dnas.scalar()}")
        print(f"  Fragrance Lines: {lines.scalar()}")
        print(f"  Fragrance Products: {prods.scalar()}")
        print(f"  Product Variants: {vars.scalar()}")
        print(f"  Price Observations: {prices.scalar()}")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check())
