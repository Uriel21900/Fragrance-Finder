import asyncio
from typing import List
from bs4 import BeautifulSoup
from .base import BaseScraper, Job, ScrapedProduct

class MacysScraper(BaseScraper):
    RETAILER_NAME = "Macy's"
    RETAILER_NORM = "macys"
    RETAILER_URL = "https://www.macys.com"

    async def scrape(self, job: Job) -> List[ScrapedProduct]:
        print(f"[Macy's] Scraping {job.search_term}...")
        encoded_query = job.search_term.replace(' ', '%20')
        url = f"https://www.macys.com/shop/featured/{encoded_query}"
        
        await self.start_browser()
        assert self.browser is not None
        page = await self.browser.get(url)
        await asyncio.sleep(5)
        
        html = await page.get_content()
        soup = BeautifulSoup(html, 'html.parser')
        
        product_elements = soup.select('.productThumbnailItem, .product-thumbnail')
        print(f"[Macy's] Found {len(product_elements)} products on page.")
        
        scraped_data = []
        for p in product_elements:
            title_el = p.select_one('.productDescLink, .product-name')
            price_el = p.select_one('.regular, .discount, .price')
            link_el = p.select_one('a.productDescLink, a')
            
            if title_el and price_el:
                title = title_el.text.strip()
                price_str = price_el.text.strip()
                price_amount = self.parse_price(price_str)
                
                href = str(link_el.get('href', '')) if link_el else ''
                full_url = f"https://www.macys.com{href}" if href.startswith('/') else href
                
                if price_amount > 0:
                    scraped_data.append(ScrapedProduct(title=title, price=price_amount, url=full_url))
                    
        return scraped_data
