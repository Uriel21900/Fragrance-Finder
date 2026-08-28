import asyncio
import os
import sys
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import PriceObservation

async def clean_non_aventus():
    async with async_session_maker() as session:
        obs_res = await session.execute(select(PriceObservation))
        for obs in obs_res.scalars().all():
            u = (obs.source_url or "").lower()
            if "erba-pura" in u or "ariana-grande" in u or "banadir" in u or "dunhil" in u:
                await session.delete(obs)
        await session.commit()
        print("Cleaned non-aventus observations.")

if __name__ == "__main__":
    asyncio.run(clean_non_aventus())
