import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from redis_client import get_redis

async def flush():
    async for r in get_redis():
        await r.flushdb()
        print("Redis cache flushed successfully!")
        break

if __name__ == "__main__":
    asyncio.run(flush())
