from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.endpoints import router as api_router

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scrapers import Job, JomashopScraper, MacysScraper, FragFlexScraper

async def run_scrapers():
    print("=== BACKGROUND SCRAPER WAKING UP ===")
    jobs = [
        Job(target_brand="Creed", search_term="Aventus", correlation_id="cron_001"),
        Job(target_brand="Armaf", search_term="Club De Nuit Intense", correlation_id="cron_002")
    ]
    scrapers = [JomashopScraper(), MacysScraper(), FragFlexScraper()]
    
    for scraper in scrapers:
        for job in jobs:
            try:
                await scraper.run(job)
            except Exception as e:
                print(f"[{scraper.RETAILER_NAME}] Failed to run job {job.search_term}: {e}")
    print("=== BACKGROUND SCRAPER SLEEPING ===")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup logic: initialize DB connections, Redis, Elasticsearch
    print("Starting up Fragrance Finder API...")
    
    # Start the background task scheduler
    scheduler = AsyncIOScheduler()
    # Run the scrapers every 12 hours
    scheduler.add_job(run_scrapers, 'interval', hours=12)
    scheduler.start()
    
    yield
    
    # Shutdown logic: close connections
    print("Shutting down Fragrance Finder API...")
    scheduler.shutdown()

app = FastAPI(title="Fragrance Finder API", lifespan=lifespan)

# Allow CORS for local development with Next.js
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

@app.get("/")
async def root():
    return {"status": "ok", "message": "Fragrance Finder API is running"}

@app.get("/health")
async def health_check():
    # In the future, this would check DB, Redis, and ES health
    return {"status": "healthy"}
