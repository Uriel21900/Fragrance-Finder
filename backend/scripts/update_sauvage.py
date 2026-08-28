import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import FragranceDNA
from sqlalchemy import select, update

async def update_sauvage():
    async with async_session_maker() as session:
        # Sauvage Elixir
        stmt = (
            update(FragranceDNA)
            .where(FragranceDNA.canonical_name.ilike('%Sauvage Elixir%'))
            .values(image_url='/images/sauvage_elixir.jpg')
        )
        await session.execute(stmt)
        await session.commit()
        print("Updated Sauvage Elixir image URL to /images/sauvage_elixir.jpg")

if __name__ == "__main__":
    asyncio.run(update_sauvage())
