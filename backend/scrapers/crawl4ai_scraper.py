from typing import List
from crawl4ai import AsyncWebCrawler
from .base import BaseScraper, Job, ScrapedProduct
from .ai_parser import parse_markdown
from .verifier import verify_parsed_fragrance

class Crawl4AIScraper(BaseScraper):
    def __init__(self, retailer_name: str, base_url: str, search_url_format: str):
        super().__init__()
        self.retailer_name = retailer_name
        self.base_url = base_url.rstrip('/')
        self.RETAILER_NAME = retailer_name
        self.RETAILER_NORM = retailer_name.lower().replace(" ", "_")
        self.RETAILER_URL = self.base_url
        self.search_url_format = search_url_format

    @property
    def name(self) -> str:
        return self.retailer_name

    def get_search_url(self, search_term: str) -> str:
        encoded_query = search_term.replace(' ', '+')
        return self.search_url_format.format(query=encoded_query)

    async def scrape(self, job: Job) -> List[ScrapedProduct]:
        print(f"[{self.RETAILER_NAME}] Scraping {job.search_term} using Crawl4AI...")
        url = self.get_search_url(job.search_term)
        
        scraped_data = []
        async with AsyncWebCrawler(verbose=True) as crawler:
            result = await crawler.arun(
                url=url,
                bypass_cache=True,
            )
            
            if result.markdown:
                print(f"[{self.RETAILER_NAME}] Extracted Markdown. Running Gemini Parsing...")
                
                parsed_items = parse_markdown(result.markdown, job.search_term, job.target_brand)
                
                for item in parsed_items:
                    # Run verifier
                    verification = verify_parsed_fragrance(
                        clone_name=item.clone_name,
                        clone_brand=item.clone_brand,
                        inspired_by=item.inspired_by or "",
                        search_term=job.search_term
                    )
                    
                    if verification.is_hallucination:
                        print(f"[{self.RETAILER_NAME}] Verifier rejected item {item.clone_name} (Hallucination: {verification.reasoning})")
                        continue
                        
                    # If passed, add to scraped_data
                    sp = ScrapedProduct(
                        title=f"{item.clone_brand} {item.clone_name}",
                        price=item.price,
                        url=url, # using search url as fallback since markdown might not have accurate links
                        is_dupe=item.is_dupe,
                        inspired_by=verification.corrected_inspired_by or item.inspired_by,
                        llm_validated=True
                    )
                    
                    # We rely on the base class save logic for stock checks if needed, but we can set it here
                    scraped_data.append(sp)
                    
        return scraped_data

    async def run(self, job: Job):
        try:
            scraped = await self.scrape(job)
            await self.save_to_db(job, scraped)
        except Exception as e:
            print(f"[{self.RETAILER_NAME}] Run failed: {e}")

