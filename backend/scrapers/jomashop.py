import asyncio
from typing import List
from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
import json

from .base import BaseScraper, Job, ScrapedProduct
from .ai_parser import get_llm_strategy

class JomashopScraper(BaseScraper):
    RETAILER_NAME = "Jomashop"
    RETAILER_NORM = "jomashop"
    RETAILER_URL = "https://jomashop.com"

    async def scrape(self, job: Job) -> List[ScrapedProduct]:
        print(f"[Jomashop] Scraping {job.search_term} using Crawl4AI...")
        encoded_query = job.search_term.replace(' ', '+')
        url = f"https://www.jomashop.com/fragrances.html?q={encoded_query}"
        
        strategy = get_llm_strategy(job.target_brand, job.search_term)
        
        scraped_data = []
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url=url,
                extraction_strategy=strategy,
                bypass_cache=True,
            )
            
            if result.extracted_content:
                print(f"[Jomashop] LLM Output: {result.extracted_content}")
                try:
                    items = json.loads(result.extracted_content)
                    for item in items:
                        if item.get("is_match"):
                            extracted_url = item.get("url", "")
                            
                            # Anti-hallucination check for Jomashop: Jomashop doesn't use "product/[uuid]" format.
                            if extracted_url and "product/" in extracted_url and len(extracted_url.split("-")) >= 4:
                                print(f"[Jomashop] Discarding hallucinated URL: {extracted_url}")
                                extracted_url = url # fallback to search url
                                
                            if not extracted_url:
                                extracted_url = url
                                
                            sp = ScrapedProduct(
                                title=item.get("title", ""),
                                price=float(item.get("price", 0.0)),
                                url=extracted_url,
                                is_dupe=item.get("is_dupe", False),
                                inspired_by=item.get("inspired_by"),
                                volume_ml=item.get("volume_ml"),
                                concentration=item.get("concentration"),
                                llm_validated=True
                            )
                            scraped_data.append(sp)
                except Exception as e:
                    print(f"[Jomashop] Error parsing LLM output: {e}")
                    
        return scraped_data
