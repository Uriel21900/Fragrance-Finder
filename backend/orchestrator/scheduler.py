"""
Background Scheduler Daemon (backend/orchestrator/scheduler.py)

Runs continuous local background scheduling for scrape_all.py every 6 hours
with immediate execution on startup.
"""

import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from backend.scripts.scrape_all import run_all_scrapers

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("OrchestratorScheduler")

async def main():
    scheduler = AsyncIOScheduler()
    
    # Schedule every 6 hours
    scheduler.add_job(
        run_all_scrapers, 
        trigger="interval", 
        hours=6, 
        id="scrape_all_job", 
        name="Scrape 17 Domains"
    )
    
    scheduler.start()
    logger.info("Orchestrator scheduler started. Running immediate startup cycle, then repeating every 6 hours...")
    
    # Run immediate first iteration
    try:
        await run_all_scrapers()
    except Exception as e:
        logger.error(f"Startup run exception: {e}")

    # Keep daemon alive
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
