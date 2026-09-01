import asyncio
from scrapers import Job, MacysScraper, FragFlexScraper
from scrapers.generic import PerfumeSpotScraper
from scrapers.shopify_json import ShopifyJsonScraper
from scrapers.crawl4ai_scraper import Crawl4AIScraper

async def main():
    print("=== STARTING CONTINUOUS SCRAPER DAEMON ===")
    
    from database import async_session_maker
    from models.schema import FragranceDNA
    from sqlalchemy import select
    
    plugins = [
        MacysScraper(),
        FragFlexScraper(),
        PerfumeSpotScraper(),
        
        # Protected / Dynamic sites using Crawl4AI + Gemini
        Crawl4AIScraper("Jomashop", "https://jomashop.com", "https://www.jomashop.com/fragrances.html?q={query}"),
        Crawl4AIScraper("AuraFragrance", "https://www.aurafragrance.com", "https://www.aurafragrance.com/search?q={query}"),
        Crawl4AIScraper("ReblScents", "https://reblscents.com", "https://reblscents.com/search?q={query}"),
        
        # Shopify standard sites using JSON API
        ShopifyJsonScraper("Labelle", "https://labelleperfumes.com"),
        ShopifyJsonScraper("BestBrandsPerfume", "https://bestbrandsperfume.com"),
        ShopifyJsonScraper("BanadirFragrance", "https://banadirfragrance.com"),
        ShopifyJsonScraper("TripleTraders", "https://tripletraders.com"),
        ShopifyJsonScraper("PerfumeOnline.com", "https://perfumeonline.com"),
        ShopifyJsonScraper("ShopAromatix", "https://shoparomatix.com"),
        ShopifyJsonScraper("AromaConcepts", "https://www.aromaconcepts.com"),
        ShopifyJsonScraper("GiftExpress", "https://www.giftexpress.com"),
        ShopifyJsonScraper("AnauStore", "https://anaustore.com"),
        ShopifyJsonScraper("LRLux", "https://lrlux.com"),
        ShopifyJsonScraper("BeautyHouse", "https://beautyhouse.com"),
        ShopifyJsonScraper("FragranceShop", "https://fragranceshop.com"),
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
