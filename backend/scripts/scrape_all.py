"""
Unified Scraper Orchestrator (backend/scripts/scrape_all.py)

Manages concurrent scraping across all 17 target domains, provides isolated worker
queues, monitors error rates and anti-bot challenges, and streams operational telemetry
directly to Neon PostgreSQL.
"""

import asyncio
import os
import sys
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional, Any
import httpx
from dotenv import load_dotenv

# Ensure root import visibility
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from backend.db.neon_client import NeonLogStreamer
from backend.orchestrator.domain_manager import (
    AntiBotDetector,
    DomainConfig,
    DomainOrchestrator,
    DomainStatus,
    DomainType,
)
from backend.scrapers.router import (
    ShopifyFastPath,
    ScraplingCrawl4AIPath,
    InteractiveVariantPath,
    PipelineProcessor,
    NeonDatabaseSync,
    ScrapedProductRecord,
)

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("scrape_all")

# ==========================================
# 1. Configuration of the 17 Target Domains
# ==========================================

TARGET_DOMAINS: List[DomainConfig] = [
    # --- Shopify Fast Path Endpoints (1..8) ---
    DomainConfig("banadirfragrance.com", "https://banadirfragrance.com/products.json", DomainType.SHOPIFY, rate_limit_rps=4.0),
    DomainConfig("aromaconcepts.com", "https://aromaconcepts.com/products.json", DomainType.SHOPIFY, rate_limit_rps=4.0),
    DomainConfig("fragflex.com", "https://fragflex.com/products.json", DomainType.SHOPIFY, rate_limit_rps=3.0),
    DomainConfig("tripletraders.com", "https://tripletraders.com/products.json", DomainType.SHOPIFY, rate_limit_rps=4.0),
    DomainConfig("shoparomatix.com", "https://shoparomatix.com/products.json", DomainType.SHOPIFY, rate_limit_rps=4.0),
    DomainConfig("anaustore.com", "https://anaustore.com/products.json", DomainType.SHOPIFY, rate_limit_rps=3.0),
    DomainConfig("lrlux.com", "https://lrlux.com/products.json", DomainType.SHOPIFY, rate_limit_rps=4.0),
    DomainConfig("oudstore.com", "https://oudstore.com/products.json", DomainType.SHOPIFY, rate_limit_rps=3.0),

    # --- Protected Dynamic Sites (9..14) ---
    DomainConfig("jomashop.com", "https://www.jomashop.com", DomainType.PROTECTED, rate_limit_rps=1.0),
    DomainConfig("aurafragrance.com", "https://www.aurafragrance.com", DomainType.PROTECTED, rate_limit_rps=1.0),
    DomainConfig("reblscents.com", "https://reblscents.com", DomainType.PROTECTED, rate_limit_rps=1.0),
    DomainConfig("fragrancenet.com", "https://www.fragrancenet.com", DomainType.PROTECTED, rate_limit_rps=0.8),
    DomainConfig("fragrancex.com", "https://www.fragrancex.com", DomainType.PROTECTED, rate_limit_rps=1.0),
    DomainConfig("beautyencounter.com", "https://www.beautyencounter.com", DomainType.PROTECTED, rate_limit_rps=1.0),

    # --- Interactive / Multi-Variant Sites (15..17) ---
    DomainConfig("perfumania.com", "https://www.perfumania.com", DomainType.CUSTOM, rate_limit_rps=1.5),
    DomainConfig("fragrancebuy.ca", "https://fragrancebuy.ca", DomainType.CUSTOM, rate_limit_rps=1.5),
    DomainConfig("maxaroma.com", "https://www.maxaroma.com", DomainType.CUSTOM, rate_limit_rps=1.2),
]


# ==========================================
# 2. Domain Scraping Worker
# ==========================================

async def scrape_domain_worker(
    domain_cfg: DomainConfig,
    orchestrator: DomainOrchestrator,
    log_streamer: NeonLogStreamer,
    run_id: str
):
    domain_name = domain_cfg.name
    state = orchestrator.domains[domain_name]
    state.status = DomainStatus.RUNNING
    state.started_at = datetime.now(timezone.utc)

    await log_streamer.log(
        run_id, domain_name, "INFO", f"Starting scraping worker for {domain_name} ({state.config.domain_type.value})"
    )

    records: List[ScrapedProductRecord] = []

    try:
        # Check if domain was already paused
        if orchestrator.is_paused(domain_name):
            await log_streamer.log(run_id, domain_name, "WARN", "Worker exited because domain is PAUSED.")
            return

        # ----------------------------------------------------
        # Execution Branch: Tier 1 Shopify Stores
        # ----------------------------------------------------
        if domain_cfg.domain_type == DomainType.SHOPIFY:
            raw_items = await ShopifyFastPath.fetch_products(domain_name, limit=50)
            if raw_items:
                records = await PipelineProcessor.process_shopify_items(raw_items)
                state.scraped_count = len(records)
                await log_streamer.log(
                    run_id, domain_name, "INFO", f"Extracted {len(records)} products via Tier 1 Shopify JSON."
                )
            else:
                state.error_count += 1
                await log_streamer.log(
                    run_id, domain_name, "WARN", f"Shopify endpoint returned 0 products for {domain_name}."
                )

        # ----------------------------------------------------
        # Execution Branch: Tier 2 Protected Sites
        # ----------------------------------------------------
        elif domain_cfg.domain_type == DomainType.PROTECTED:
            # Pre-flight anti-bot probe
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as probe_client:
                try:
                    probe_resp = await probe_client.get(
                        domain_cfg.url,
                        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
                    )
                    block_reason = AntiBotDetector.check_response(
                        probe_resp.status_code, dict(probe_resp.headers), probe_resp.text
                    )
                    if block_reason:
                        await orchestrator.trigger_antibot_pause(domain_name, block_reason, run_id)
                        return
                except Exception as e:
                    logger.debug(f"Probe note for {domain_name}: {e}")

            markdown = await ScraplingCrawl4AIPath.fetch_clean_markdown(domain_cfg.url)
            if markdown:
                records = await PipelineProcessor.process_markdown(markdown, domain_name, domain_name.capitalize())
                state.scraped_count = len(records)
                await log_streamer.log(
                    run_id, domain_name, "INFO", f"Extracted {len(records)} products via Scrapling + Crawl4AI."
                )

        # ----------------------------------------------------
        # Execution Branch: Tier 3 Custom / Interactive Sites
        # ----------------------------------------------------
        else:
            interactive_variants = await InteractiveVariantPath.extract_interactive_variants(domain_cfg.url)
            markdown = await ScraplingCrawl4AIPath.fetch_clean_markdown(domain_cfg.url)
            if markdown:
                records = await PipelineProcessor.process_markdown(markdown, domain_name, domain_name.capitalize())
                state.scraped_count = len(records)
                await log_streamer.log(
                    run_id, domain_name, "INFO", f"Extracted {len(records)} products from custom/interactive storefront."
                )

        # ----------------------------------------------------
        # Batch Upsert to Neon PostgreSQL
        # ----------------------------------------------------
        if records and log_streamer.pool:
            db_stats = await NeonDatabaseSync.batch_upsert(log_streamer.pool, records)
            state.inserted_count = db_stats.get("prices_inserted", 0)
            await log_streamer.log(
                run_id, domain_name, "INFO",
                f"Neon DB sync completed for {domain_name}: {db_stats}"
            )

        if state.status != DomainStatus.PAUSED_ANTIBOT:
            state.status = DomainStatus.COMPLETED

    except Exception as e:
        state.status = DomainStatus.FAILED
        state.error_count += 1
        await log_streamer.log(run_id, domain_name, "ERROR", f"Worker failure for {domain_name}: {str(e)}")
    finally:
        state.ended_at = datetime.now(timezone.utc)


# ==========================================
# 3. Master Orchestration Runner
# ==========================================

async def run_all_scrapers() -> Dict[str, Any]:
    run_id = str(uuid.uuid4())
    log_streamer = NeonLogStreamer()
    await log_streamer.connect()
    if not log_streamer.pool:
        raise RuntimeError("Failed to connect to Neon database pool.")
    pool = log_streamer.pool

    orchestrator = DomainOrchestrator(TARGET_DOMAINS, log_streamer)
    await log_streamer.start_heartbeat(orchestrator.get_summary_state, interval_sec=15)

    started_at = datetime.now(timezone.utc)
    logger.info(f"=== STARTING 6-HOUR SCRAPING ORCHESTRATION RUN [{run_id}] ACROSS {len(TARGET_DOMAINS)} DOMAINS ===")

    # 1. Record initial run record in Neon
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO scrape_runs (run_id, started_at, status, total_domains)
            VALUES ($1, $2, $3, $4)
            """,
            uuid.UUID(run_id), started_at, "IN_PROGRESS", len(TARGET_DOMAINS)
        )

    async def _safe_worker(d):
        try:
            await asyncio.wait_for(
                scrape_domain_worker(d, orchestrator, log_streamer, run_id),
                timeout=60.0
            )
        except asyncio.TimeoutError:
            state = orchestrator.domains[d.name]
            state.status = DomainStatus.FAILED
            state.error_count += 1
            state.ended_at = datetime.now(timezone.utc)
            await log_streamer.log(run_id, d.name, "WARN", f"Worker timed out after 60s for {d.name}")
        except Exception as e:
            logger.error(f"Unexpected worker error for {d.name}: {e}")

    # 2. Launch all 17 domain workers concurrently with isolated timeouts
    tasks = [asyncio.create_task(_safe_worker(domain)) for domain in TARGET_DOMAINS]
    await asyncio.gather(*tasks, return_exceptions=True)

    # 3. Finalize run statistics
    finished_at = datetime.now(timezone.utc)
    total_inserted = sum(d.inserted_count for d in orchestrator.domains.values())
    total_errors = sum(d.error_count for d in orchestrator.domains.values())
    blocked_domains = sum(1 for d in orchestrator.domains.values() if d.status == DomainStatus.PAUSED_ANTIBOT)
    successful_domains = sum(1 for d in orchestrator.domains.values() if d.status == DomainStatus.COMPLETED)

    # 4. Persist domain-level metrics to Neon
    async with pool.acquire() as conn:
        for name, d in orchestrator.domains.items():
            duration = (d.ended_at - d.started_at).total_seconds() if d.ended_at and d.started_at else 0
            await conn.execute(
                """
                INSERT INTO domain_metrics 
                (run_id, domain, domain_type, status, items_scraped, items_inserted, error_count, antibot_detected, antibot_reason, duration_seconds, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW())
                """,
                uuid.UUID(run_id), name, d.config.domain_type.value, d.status.value,
                d.scraped_count, d.inserted_count, d.error_count, d.antibot_detected, d.pause_reason, round(duration, 2)
            )

        run_status = "COMPLETED" if blocked_domains == 0 else "PARTIAL_FAIL"
        await conn.execute(
            """
            UPDATE scrape_runs 
            SET finished_at = $1, status = $2, successful_domains = $3, 
                blocked_domains = $4, total_records_inserted = $5, total_errors = $6
            WHERE run_id = $7
            """,
            finished_at, run_status, successful_domains, blocked_domains, total_inserted, total_errors, uuid.UUID(run_id)
        )

    await log_streamer.log(
        run_id, None, "INFO", 
        f"Orchestration Run {run_id} completed. Inserted: {total_inserted}, Blocked: {blocked_domains}, Successful: {successful_domains}"
    )

    await asyncio.sleep(2)  # Flush log queue
    await log_streamer.close()

    summary = {
        "run_id": run_id,
        "status": run_status,
        "total_domains": len(TARGET_DOMAINS),
        "successful_domains": successful_domains,
        "blocked_domains": blocked_domains,
        "total_records_inserted": total_inserted,
        "total_errors": total_errors,
        "duration_seconds": round((finished_at - started_at).total_seconds(), 2)
    }
    logger.info(f"=== ORCHESTRATION RUN COMPLETED: {summary} ===")
    return summary


if __name__ == "__main__":
    result = asyncio.run(run_all_scrapers())
    print("\n--- ORCHESTRATOR RUN REPORT ---")
    import json
    print(json.dumps(result, indent=2))
