import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

NEON_DB_URL = "postgresql+asyncpg://neondb_owner:npg_iN45StWGXmpK@ep-winter-surf-ay718z8s-pooler.c-5.us-east-2.aws.neon.tech/neondb?ssl=require"

async def check():
    engine = create_async_engine(NEON_DB_URL, echo=False)
    async with engine.connect() as conn:
        dnas = await conn.execute(text("SELECT count(*) FROM fragrance_dna;"))
        lines = await conn.execute(text("SELECT count(*) FROM fragrance_line;"))
        prods = await conn.execute(text("SELECT count(*) FROM fragrance_product;"))
        vars = await conn.execute(text("SELECT count(*) FROM product_variant;"))
        prices = await conn.execute(text("SELECT count(*) FROM price_observation;"))
        
        print(f"Neon Database Content:")
        print(f"  Fragrance DNAs: {dnas.scalar()}")
        print(f"  Fragrance Lines: {lines.scalar()}")
        print(f"  Fragrance Products: {prods.scalar()}")
        print(f"  Product Variants: {vars.scalar()}")
        print(f"  Price Observations: {prices.scalar()}")

if __name__ == "__main__":
    asyncio.run(check())
