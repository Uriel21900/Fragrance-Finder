"""
Database migration script to create orchestrator monitoring, telemetry,
and logging tables in Neon PostgreSQL.
"""

import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(".env")

MIGRATION_SQL = """
-- 1. Heartbeat & Connection Health
CREATE TABLE IF NOT EXISTS orchestrator_heartbeats (
    id BIGSERIAL PRIMARY KEY,
    instance_name VARCHAR(100) DEFAULT 'local-worker-1',
    status VARCHAR(50) NOT NULL, -- 'RUNNING', 'IDLE', 'ERROR', 'PAUSED'
    active_domains INT NOT NULL,
    paused_domains INT NOT NULL,
    memory_usage_mb NUMERIC(8, 2),
    cpu_usage_pct NUMERIC(5, 2),
    last_ping_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 2. Overall Scrape Run Records
CREATE TABLE IF NOT EXISTS scrape_runs (
    run_id UUID PRIMARY KEY,
    started_at TIMESTAMPTZ NOT NULL,
    finished_at TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL, -- 'IN_PROGRESS', 'COMPLETED', 'PARTIAL_FAIL'
    total_domains INT NOT NULL DEFAULT 17,
    successful_domains INT DEFAULT 0,
    blocked_domains INT DEFAULT 0,
    total_records_inserted INT DEFAULT 0,
    total_errors INT DEFAULT 0
);

-- 3. Per-Domain Status & Error Tracking
CREATE TABLE IF NOT EXISTS domain_metrics (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES scrape_runs(run_id) ON DELETE CASCADE,
    domain VARCHAR(255) NOT NULL,
    domain_type VARCHAR(50) NOT NULL, -- 'shopify', 'custom', 'protected'
    status VARCHAR(50) NOT NULL,      -- 'ACTIVE', 'PAUSED_ANTIBOT', 'COMPLETED', 'FAILED'
    items_scraped INT DEFAULT 0,
    items_inserted INT DEFAULT 0,
    error_count INT DEFAULT 0,
    antibot_detected BOOLEAN DEFAULT FALSE,
    antibot_reason TEXT,
    duration_seconds NUMERIC(10, 2),
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- 4. Streamed Operational Logs
CREATE TABLE IF NOT EXISTS scrape_logs (
    id BIGSERIAL PRIMARY KEY,
    run_id UUID REFERENCES scrape_runs(run_id) ON DELETE CASCADE,
    domain VARCHAR(255),
    level VARCHAR(20) NOT NULL,       -- 'INFO', 'WARN', 'ERROR', 'CRITICAL'
    message TEXT NOT NULL,
    context JSONB,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_scrape_logs_run_id ON scrape_logs(run_id);
CREATE INDEX IF NOT EXISTS idx_domain_metrics_status ON domain_metrics(domain, status);
"""

async def run_migration():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is not set")

    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    print("Connecting to Neon PostgreSQL...")
    conn = await asyncpg.connect(db_url)
    try:
        await conn.execute(MIGRATION_SQL)
        print("Successfully created orchestrator_heartbeats, scrape_runs, domain_metrics, and scrape_logs tables in Neon!")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
