import bs4
from typing import Optional, Dict
from bs4 import BeautifulSoup
import re
import asyncio
from .base import BaseScraper, Job, ScrapedProduct

class ShopifyScraper(BaseScraper):
    """Generic scraper for Shopify-based fragrance retailers."""
    
    def __init__(self, retailer_name: str, base_url: str):
        super().__init__()
        self.retailer_name = retailer_name
        self.base_url = base_url
        self.RETAILER_NAME = retailer_name
        self.RETAILER_NORM = retailer_name.lower().replace(" ", "_")
        self.RETAILER_URL = base_url
    
    @property
    def name(self) -> str:
        return self.retailer_name
        
    def get_search_url(self, search_term: str) -> str:
        term = search_term.replace(" ", "+")
        return f"{self.base_url}/search?q={term}"
        
    def get_headers(self) -> dict:
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9',
            'Accept-Language': 'en-US,en;q=0.9'
        }
        
    def extract_products(self, html: str) -> list[bs4.element.Tag]:
        soup = BeautifulSoup(html, 'html.parser')
        return soup.select('.grid__item, .product-item, .product-card, .card')
        
    def extract_product_data(self, element: bs4.element.Tag) -> Optional[Dict]:
        title_elem = element.select_one('.title, .product-title, .card__heading, h2, h3, a.product-item__title')
        if not title_elem:
            return None
        title = title_elem.text.strip()
        
        price_elem = element.select_one('.price-item--sale, .price-item, .money, .price')
        if not price_elem:
            return None
            
        price_text = price_elem.text.strip()
        price_match = re.search(r'[\d,\.]+', price_text)
        if not price_match:
            return None
            
        try:
            price = float(price_match.group().replace(',', ''))
        except ValueError:
            return None
            
        link_elem = element.select_one('a')
        if not link_elem or not link_elem.get('href'):
            return None
            
        url_attr = link_elem.get('href')
        if isinstance(url_attr, list):
            url_attr = url_attr[0]
        if not url_attr or not isinstance(url_attr, str):
            return None
            
        url = url_attr
        if not url.startswith('http'):
            url = f"{self.base_url}{url}"
            
        return {
            "title": title,
            "price": price,
            "url": url,
            "in_stock": True # Default to true for search results usually
        }

    async def scrape(self, job: Job) -> list[ScrapedProduct]:
        print(f"[{self.RETAILER_NAME}] Scraping {job.search_term}...")
        url = self.get_search_url(job.search_term)
        
        await self.start_browser()
        assert self.browser is not None
        page = await self.browser.get(url)
        await asyncio.sleep(5)
        
        html = await page.get_content()
        product_elements = self.extract_products(html)
        print(f"[{self.RETAILER_NAME}] Found {len(product_elements)} products on page.")
        
        scraped_data = []
        for p in product_elements:
            data = self.extract_product_data(p)
            if data and data.get("price", 0) > 0:
                scraped_data.append(ScrapedProduct(
                    title=data["title"],
                    price=data["price"],
                    url=data["url"]
                ))
        return scraped_data

class PerfumeSpotScraper(BaseScraper):
    RETAILER_NAME = "ThePerfumeSpot"
    RETAILER_NORM = "theperfumespot"
    RETAILER_URL = "https://theperfumespot.com"

    def __init__(self):
        super().__init__()
        self.RETAILER_NAME = "ThePerfumeSpot"
        self.RETAILER_NORM = "theperfumespot"
        self.RETAILER_URL = "https://theperfumespot.com"

    @property
    def name(self) -> str:
        return "ThePerfumeSpot"
        
    def get_search_url(self, search_term: str) -> str:
        term = search_term.replace(" ", "+")
        return f"https://theperfumespot.com/search.php?search_query={term}"
        
    def get_headers(self) -> dict:
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
    def extract_products(self, html: str) -> list[bs4.element.Tag]:
        soup = BeautifulSoup(html, 'html.parser')
        return soup.select('.product, article.card')
        
    def extract_product_data(self, element: bs4.element.Tag) -> Optional[Dict]:
        title_elem = element.select_one('.card-title, .product-title, h4 a, h3 a')
        if not title_elem:
            return None
        title = title_elem.text.strip()
        
        price_elem = element.select_one('.price.price--withoutTax, .price-section .price')
        if not price_elem:
            return None
            
        price_text = price_elem.text.strip()
        price_match = re.search(r'[\d,\.]+', price_text)
        if not price_match:
            return None
            
        try:
            price = float(price_match.group().replace(',', ''))
        except ValueError:
            return None
            
        link_elem = element.select_one('a')
        if not link_elem or not link_elem.get('href'):
            return None
            
        url_attr = link_elem.get('href')
        if isinstance(url_attr, list):
            url_attr = url_attr[0]
        if not url_attr or not isinstance(url_attr, str):
            return None
            
        url = url_attr
        
        return {
            "title": title,
            "price": price,
            "url": url,
            "in_stock": True
        }

    async def scrape(self, job: Job) -> list[ScrapedProduct]:
        print(f"[{self.RETAILER_NAME}] Scraping {job.search_term}...")
        url = self.get_search_url(job.search_term)
        
        await self.start_browser()
        assert self.browser is not None
        page = await self.browser.get(url)
        await asyncio.sleep(5)
        
        html = await page.get_content()
        product_elements = self.extract_products(html)
        print(f"[{self.RETAILER_NAME}] Found {len(product_elements)} products on page.")
        
        scraped_data = []
        for p in product_elements:
            data = self.extract_product_data(p)
            if data and data.get("price", 0) > 0:
                scraped_data.append(ScrapedProduct(
                    title=data["title"],
                    price=data["price"],
                    url=data["url"]
                ))
        return scraped_data
