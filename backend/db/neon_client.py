"""
Neon PostgreSQL Logging & Heartbeat Streamer (backend/db/neon_client.py)
Handles persistent connection pooling, log queue buffering, and real-time streaming to Neon.
"""

import asyncio
import json
import logging
import os
import uuid
import psutil  # type: ignore
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import asyncpg
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")

logger = logging.getLogger("NeonClient")

class NeonLogStreamer:
    def __init__(self, dsn: Optional[str] = None):
        raw_dsn = dsn or os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")
        if not raw_dsn:
            raw_dsn = ""
        if raw_dsn.startswith("postgresql+asyncpg://"):
            raw_dsn = raw_dsn.replace("postgresql+asyncpg://", "postgresql://", 1)
        elif raw_dsn.startswith("postgres://"):
            raw_dsn = raw_dsn.replace("postgres://", "postgresql://", 1)
        
        if "sslmode=" not in raw_dsn and "ssl=" not in raw_dsn:
            join_char = "&" if "?" in raw_dsn else "?"
            raw_dsn += f"{join_char}sslmode=require"

        self.dsn = raw_dsn
        self.pool: Optional[asyncpg.Pool] = None
        self._log_queue: asyncio.Queue = asyncio.Queue()
        self._flush_task: Optional[asyncio.Task] = None
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._running = False

    async def connect(self):
        if not self.dsn:
            raise ValueError("DATABASE_URL / NEON_DATABASE_URL environment variable is required.")
        
        # Neon PostgreSQL requires SSL
        self.pool = await asyncpg.create_pool(
            dsn=self.dsn,
            min_size=2,
            max_size=10,
            command_timeout=60,
        )
        self._running = True
        self._flush_task = asyncio.create_task(self._background_log_flusher())
        logger.info("Connected to Neon PostgreSQL pool.")

    async def start_heartbeat(self, get_state_func, interval_sec: int = 30):
        async def _heartbeat_loop():
            while self._running:
                try:
                    state = get_state_func()
                    mem = psutil.Process().memory_info().rss / (1024 * 1024)
                    cpu = psutil.cpu_percent()
                    if self.pool:
                        async with self.pool.acquire() as conn:
                            await conn.execute(
                                """
                                INSERT INTO orchestrator_heartbeats 
                                (status, active_domains, paused_domains, memory_usage_mb, cpu_usage_pct, last_ping_at)
                                VALUES ($1, $2, $3, $4, $5, NOW())
                                """,
                                state.get("status", "RUNNING"),
                                state.get("active_count", 0),
                                state.get("paused_count", 0),
                                round(mem, 2),
                                round(cpu, 2),
                            )
                except Exception as e:
                    logger.warning(f"Failed to record heartbeat to Neon: {e}")
                await asyncio.sleep(interval_sec)

        self._heartbeat_task = asyncio.create_task(_heartbeat_loop())

    async def log(self, run_id: str, domain: Optional[str], level: str, message: str, context: Optional[Dict] = None):
        await self._log_queue.put({
            "run_id": run_id,
            "domain": domain,
            "level": level,
            "message": message,
            "context": json.dumps(context or {}),
            "created_at": datetime.now(timezone.utc)
        })

    async def _flush_batch(self, batch: List[Dict]):
        if not batch or not self.pool:
            return
        try:
            async with self.pool.acquire() as conn:
                await conn.executemany(
                    """
                    INSERT INTO scrape_logs (run_id, domain, level, message, context, created_at)
                    VALUES ($1, $2, $3, $4, $5::jsonb, $6)
                    """,
                    [
                        (
                            uuid.UUID(b["run_id"]),
                            b["domain"],
                            b["level"],
                            b["message"],
                            b["context"],
                            b["created_at"]
                        )
                        for b in batch
                    ]
                )
        except Exception as e:
            logger.error(f"Error streaming logs to Neon: {e}")

    async def _background_log_flusher(self):
        while self._running:
            batch = []
            try:
                while len(batch) < 50:
                    item = await asyncio.wait_for(self._log_queue.get(), timeout=2.0)
                    batch.append(item)
                    self._log_queue.task_done()
            except asyncio.TimeoutError:
                pass

            if batch:
                await self._flush_batch(batch)

    async def close(self):
        self._running = False
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        if self._flush_task:
            self._flush_task.cancel()

        # Drain remaining logs
        remaining = []
        while not self._log_queue.empty():
            try:
                remaining.append(self._log_queue.get_nowait())
            except Exception:
                break
        if remaining and self.pool:
            await self._flush_batch(remaining)

        if self.pool:
            await self.pool.close()
            logger.info("Neon PostgreSQL connection pool closed.")
