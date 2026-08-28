import asyncio
from database import async_session_maker
from models.schema import PriceObservation
from sqlalchemy import delete

async def main():
    async with async_session_maker() as s:
        # Delete any price observation from Jomashop that contains the fake uuid format
        stmt = delete(PriceObservation).where(PriceObservation.source_url.like('https://jomashop.com/product/%-%'))
        res = await s.execute(stmt)
        await s.commit()
        print(f"Deleted {res.rowcount} corrupted PriceObservation records.")

if __name__ == "__main__":
    asyncio.run(main())
