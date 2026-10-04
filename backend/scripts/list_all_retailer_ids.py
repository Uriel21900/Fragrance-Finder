import asyncio
import os
import sys
import asyncpg
from dotenv import load_dotenv

load_dotenv("backend/.env")
load_dotenv(".env")
if hasattr(sys.stdout, 'reconfigure'):
    getattr(sys.stdout, 'reconfigure')(encoding='utf-8')

async def main():
    db_url = os.getenv("DATABASE_URL")
    conn = await asyncpg.connect(db_url)

    rows = await conn.fetch("SELECT retailer_id, name, website_url FROM retailer ORDER BY name;")
    print(f"Total retailers in DB: {len(rows)}")
    for r in rows:
        print(f"  ID: {r['retailer_id']} | Name: {r['name']} | URL: {r['website_url']}")

    await conn.close()

if __name__ == "__main__":
    asyncio.run(main())
