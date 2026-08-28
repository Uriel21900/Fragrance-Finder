import asyncio
from scrapers import Job, JomashopScraper, MacysScraper, FragFlexScraper

async def main():
    print("=== STARTING CONTINUOUS SCRAPER DAEMON ===")
    
    from database import async_session_maker
    from models.schema import FragranceDNA
    from sqlalchemy import select
    from scrapers.generic import ShopifyScraper, PerfumeSpotScraper
    
    plugins = [
        JomashopScraper(),
        MacysScraper(),
        FragFlexScraper(),
        ShopifyScraper("Labelle", "https://labelleperfumes.com"),
        ShopifyScraper("BestBrandsPerfume", "https://bestbrandsperfume.com"),
        ShopifyScraper("ReblScents", "https://reblscents.com"),
        ShopifyScraper("AuraFragrance", "https://www.aurafragrance.com"),
        ShopifyScraper("BanadirFragrance", "https://banadirfragrance.com"),
        ShopifyScraper("TripleTraders", "https://tripletraders.com"),
        ShopifyScraper("PerfumeOnline.com", "https://perfumeonline.com"),
        ShopifyScraper("ShopAromatix", "https://shoparomatix.com"),
        ShopifyScraper("AromaConcepts", "https://www.aromaconcepts.com"),
        ShopifyScraper("GiftExpress", "https://www.giftexpress.com"),
        ShopifyScraper("AnauStore", "https://anaustore.com"),
        ShopifyScraper("LRLux", "https://lrlux.com"),
        ShopifyScraper("BeautyHouse", "https://beautyhouse.com"),
        ShopifyScraper("FragranceShop", "https://fragranceshop.com"),
        PerfumeSpotScraper()
    ]
    
    while True:
        jobs = []
        async with async_session_maker() as session:
            # We prioritize the earliest inserted records (the user's specific 60 fragrances)
            from sqlalchemy.orm import selectinload
            result = await session.execute(
                select(FragranceDNA)
                .options(selectinload(FragranceDNA.origin_brand))
                .order_by(FragranceDNA.created_at.asc())
            )
            dnas = result.scalars().all()
            for dna in dnas:
                brand_name = dna.origin_brand.name if dna.origin_brand else "Unknown"
                jobs.append(Job(target_brand=brand_name, search_term=dna.canonical_name, correlation_id=str(dna.dna_id)))
                
        print(f"Loaded {len(jobs)} jobs from database for this scraping cycle.")
        
        # Run sequentially to save RAM, but interleaved by job
        for job in jobs:
            for scraper in plugins:
                try:
                    await scraper.run(job)
                except Exception as e:
                    safe_name = job.search_term.encode('ascii', 'replace').decode('ascii')
                    print(f"[{scraper.RETAILER_NAME}] Failed to run job {safe_name}: {e}")
                    
        print("=== SCRAPING CYCLE COMPLETE. RESTARTING IN 12 HOURS ===")
        await asyncio.sleep(43200)

if __name__ == "__main__":
    asyncio.run(main())
