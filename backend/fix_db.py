import asyncio
from database import engine
from sqlalchemy import text

async def fix_db():
    print("Applying ALTER TABLE...")
    async with engine.begin() as conn:
        await conn.execute(text("ALTER TABLE fragrance_dna ALTER COLUMN is_dupe SET DEFAULT false;"))
    print("Database fixed!")

if __name__ == "__main__":
    asyncio.run(fix_db())
