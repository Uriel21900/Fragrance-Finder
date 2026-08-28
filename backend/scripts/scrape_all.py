import asyncio
from crawl4ai import AsyncWebCrawler

urls = [
    "https://www.jomashop.com",
    "https://www.fragflex.com",
    "https://www.labelle.com",
    "https://www.bestbrandsperfume.com",
    "https://www.theperfumespot.com",
    "https://www.reblscents.com",
    "https://www.aurafragrance.com",
    "https://www.banadirfragrance.com",
    "https://www.tripletraders.com",
    "https://www.perfumeonline.com",
    "https://www.shoparomatix.com",
    "https://www.aromaconcepts.com",
    "https://www.anaustore.com",
    "https://www.lrlux.com",
    "https://www.beautyhouse.com",
    "https://www.giftexpress.com",
    "https://www.fragranceshop.com",
    "https://www.macys.com"
]

async def scrape_site(crawler, url):
    try:
        print(f"Scraping {url}...")
        result = await crawler.arun(url=url)
        # Check if scraping was successful
        if result and hasattr(result, 'markdown'):
            print(f"Successfully scraped {url}")
            return f"### {url}\n\n{result.markdown}\n\n"
        else:
            print(f"Failed to get markdown for {url}")
            return f"### {url}\n\nError: No markdown extracted.\n\n"
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return f"### {url}\n\nError: {e}\n\n"

async def main():
    print("Initializing crawler...")
    # Initialize the web crawler
    async with AsyncWebCrawler(verbose=True) as crawler:
        # We process in batches to avoid overwhelming the system or being blocked
        # Although gather can run all at once, let's do a few at a time just in case
        results = []
        for url in urls:
            res = await scrape_site(crawler, url)
            results.append(res)
            # Small delay to be polite
            await asyncio.sleep(1)
            
    print("Writing scraped data to scraped_markdown.txt...")
    with open("scraped_markdown.txt", "w", encoding="utf-8") as f:
        f.writelines(results)
    
    print("Finished scraping all sites!")

if __name__ == "__main__":
    asyncio.run(main())
