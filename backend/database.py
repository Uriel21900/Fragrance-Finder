import os
from typing import AsyncGenerator
from dotenv import load_dotenv
import asyncpg
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(".env")

DEFAULT_NEON_URL = (
    "postgresql://neondb_owner:npg_iN45StWGXmpK@ep-winter-surf-ay718z8s-pooler.c-5.us-east-2.aws.neon.tech/neondb?sslmode=require"
)

DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_NEON_URL)

def get_sqlalchemy_async_url(raw_url: str) -> str:
    """Format connection URL for SQLAlchemy asyncpg engine."""
    url = raw_url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    # Ensure query parameters are compatible with asyncpg
    if "neon.tech" in url:
        if "?" in url:
            base, _ = url.split("?", 1)
            url = f"{base}?ssl=require"
        else:
            url = f"{url}?ssl=require"
    return url

def get_asyncpg_dsn(raw_url: str) -> str:
    """Format connection DSN for raw asyncpg connection pools."""
    url = raw_url
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    
    if "sslmode=" not in url and "ssl=" not in url:
        join_char = "&" if "?" in url else "?"
        url += f"{join_char}sslmode=require"
    return url

SQLALCHEMY_DATABASE_URL = get_sqlalchemy_async_url(DATABASE_URL)
ASYNCPG_DSN = get_asyncpg_dsn(DATABASE_URL)

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    future=True,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

async_session_maker = async_sessionmaker(
    engine, expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for obtaining async SQLAlchemy sessions."""
    async with async_session_maker() as session:
        yield session

async def get_asyncpg_pool(min_size: int = 1, max_size: int = 10) -> asyncpg.Pool:
    """Create asyncpg connection pool for high-performance batch upserts."""
    pool = await asyncpg.create_pool(
        dsn=ASYNCPG_DSN,
        min_size=min_size,
        max_size=max_size,
        command_timeout=30.0
    )
    if pool is None:
        raise RuntimeError("Failed to create asyncpg connection pool")
    return pool
