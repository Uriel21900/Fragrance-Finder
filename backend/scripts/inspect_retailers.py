import asyncio, os, sys, asyncpg
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")

async def main():
    sys.stdout.reconfigure(encoding='utf-8')
    db_url = os.getenv("DATABASE_URL")
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    if "sslmode=" not in db_url and "ssl=" not in db_url:
        db_url += "?sslmode=require"

    conn = await asyncpg.connect(db_url)
    retailers = await conn.fetch("SELECT retailer_id, name, base_url FROM retailer")
    print(f"Total retailers: {len(retailers)}")
    for r in retailers:
        print(f"  {r['name']} -> {r['base_url']}")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(main())
