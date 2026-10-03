"""
Verify telemetry data in Neon PostgreSQL.
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")

async def check_telemetry():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    conn = await asyncpg.connect(db_url)
    try:
        runs = await conn.fetch("SELECT run_id, started_at, status, total_domains, successful_domains, blocked_domains, total_records_inserted FROM scrape_runs ORDER BY started_at DESC LIMIT 5;")
        print("=== RECENT SCRAPE RUNS IN NEON ===")
        for r in runs:
            print(dict(r))

        metrics = await conn.fetch("SELECT domain, domain_type, status, items_scraped, items_inserted, error_count, antibot_detected, antibot_reason FROM domain_metrics ORDER BY id DESC LIMIT 17;")
        print("\n=== RECENT DOMAIN METRICS IN NEON ===")
        for m in metrics:
            print(dict(m))

        logs = await conn.fetch("SELECT domain, level, message, created_at FROM scrape_logs ORDER BY id DESC LIMIT 10;")
        print("\n=== RECENT LOGS IN NEON ===")
        for l in logs:
            print(dict(l))

        heartbeats = await conn.fetch("SELECT status, active_domains, paused_domains, memory_usage_mb, cpu_usage_pct, last_ping_at FROM orchestrator_heartbeats ORDER BY id DESC LIMIT 5;")
        print("\n=== RECENT HEARTBEATS IN NEON ===")
        for h in heartbeats:
            print(dict(h))

        totals = await conn.fetchrow("""
            SELECT 
                (SELECT COUNT(*) FROM brand) as brand_count,
                (SELECT COUNT(*) FROM fragrance_dna) as dna_count,
                (SELECT COUNT(*) FROM fragrance_product) as product_count,
                (SELECT COUNT(*) FROM product_variant) as variant_count,
                (SELECT COUNT(*) FROM price_observation) as price_count
        """)
        print("\n=== OVERALL FRAGRANCE DATABASE STATS ===")
        print(dict(totals))

    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check_telemetry())
