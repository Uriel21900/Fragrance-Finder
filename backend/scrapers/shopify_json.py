import httpx
from typing import Optional, Dict, List
from .base import BaseScraper, Job, ScrapedProduct

class ShopifyJsonScraper(BaseScraper):
    """Generic scraper for Shopify-based fragrance retailers using products.json."""
    
    def __init__(self, retailer_name: str, base_url: str):
        super().__init__()
        self.retailer_name = retailer_name
        self.base_url = base_url.rstrip('/')
        self.RETAILER_NAME = retailer_name
        self.RETAILER_NORM = retailer_name.lower().replace(" ", "_")
        self.RETAILER_URL = self.base_url
    
    @property
    def name(self) -> str:
        return self.retailer_name
        
    def get_search_url(self, search_term: str) -> str:
        return f"{self.base_url}/products.json?limit=250"
        
    async def scrape(self, job: Job) -> list[ScrapedProduct]:
        print(f"[{self.RETAILER_NAME}] Scraping {job.search_term} via products.json...")
        url = self.get_search_url(job.search_term)
        
        scraped_data = []
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                
                products = data.get('products', [])
                print(f"[{self.RETAILER_NAME}] Found {len(products)} products in JSON.")
                
                search_lower = job.search_term.lower()
                
                for p in products:
                    title = p.get('title', '')
                    if not title:
                        continue
                        
                    words = search_lower.split()
                    if not any(w in title.lower() for w in words if len(w) > 3):
                        continue
                            
                    handle = p.get('handle', '')
                    product_url = f"{self.base_url}/products/{handle}"
                    
                    variants = p.get('variants', [])
                    available_variants = [v for v in variants if v.get('available', False)]
                    
                    if not available_variants:
                        continue
                        
                    lowest_price = float('inf')
                    for v in available_variants:
                        try:
                            price = float(v.get('price', 0))
                            if price > 0 and price < lowest_price:
                                lowest_price = price
                        except (ValueError, TypeError):
                            continue
                            
                    if lowest_price == float('inf'):
                        continue
                        
                    scraped_data.append(ScrapedProduct(
                        title=title,
                        price=lowest_price,
                        url=product_url
                    ))
                    
        except Exception as e:
            print(f"[{self.RETAILER_NAME}] JSON scrape failed: {e}")
            
        return scraped_data

    async def run(self, job: Job):
        try:
            scraped = await self.scrape(job)
            await self.save_to_db(job, scraped)
        except Exception as e:
            print(f"[{self.RETAILER_NAME}] Run failed: {e}")
