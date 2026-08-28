import redis.asyncio as redis
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Create a global redis connection pool
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

async def get_redis():
    yield redis_client
