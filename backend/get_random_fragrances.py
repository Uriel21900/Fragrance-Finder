import asyncio
import sys
import os

from database import async_session_maker
from models.schema import FragranceDNA
from sqlalchemy import select
from sqlalchemy.sql.expression import func

async def main():
    async with async_session_maker() as s:
        res = await s.execute(select(FragranceDNA).order_by(func.random()).limit(15))
        dnas = res.scalars().all()
        with open('names.txt', 'w', encoding='utf-8') as f:
            for d in dnas:
                f.write(d.canonical_name + "\n")

if __name__ == "__main__":
    asyncio.run(main())
