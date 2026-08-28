import asyncio
from database import engine
from models.schema import Base
from sqlalchemy import text

async def init_db():
    print("Initializing Database Schema...")
    async with engine.begin() as conn:
        # Enable citext extension before creating tables
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext;"))
        # Drop all existing tables to apply new schema
        await conn.run_sync(Base.metadata.drop_all)
        # Create all tables defined in schema.py
        await conn.run_sync(Base.metadata.create_all)
    print("Database schema successfully created!")

if __name__ == "__main__":
    asyncio.run(init_db())
