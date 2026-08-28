import asyncio
from typing import List
from bs4 import BeautifulSoup
from .base import BaseScraper, Job, ScrapedProduct

class FragFlexScraper(BaseScraper):
    RETAILER_NAME = "FragFlex"
    RETAILER_NORM = "fragflex"
    RETAILER_URL = "https://fragflex.com"

    async def scrape(self, job: Job) -> List[ScrapedProduct]:
        print(f"[FragFlex] Scraping {job.search_term}...")
        encoded_query = job.search_term.replace(' ', '+')
        url = f"https://fragflex.com/search?q={encoded_query}"
        
        await self.start_browser()
        assert self.browser is not None
        page = await self.browser.get(url)
        await asyncio.sleep(5)
        
        html = await page.get_content()
        soup = BeautifulSoup(html, 'html.parser')
        
        # FragFlex is typically Shopify-based
        product_elements = soup.select('.grid-product, .product-card, .grid__item')
        print(f"[FragFlex] Found {len(product_elements)} products on page.")
        
        scraped_data = []
        for p in product_elements:
            title_el = p.select_one('.grid-product__title, .product-card__title, .h4')
            price_el = p.select_one('.grid-product__price, .price-item--sale, .price')
            link_el = p.select_one('a.grid-product__link, a')
            
            if title_el and price_el:
                title = title_el.text.strip()
                price_str = price_el.text.strip()
                price_amount = self.parse_price(price_str)
                
                href = str(link_el.get('href', '')) if link_el else ''
                full_url = f"https://fragflex.com{href}" if href.startswith('/') else href
                
                if price_amount > 0:
                    scraped_data.append(ScrapedProduct(title=title, price=price_amount, url=full_url))
                    
        return scraped_data
