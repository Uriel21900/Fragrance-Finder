from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Any
from sqlalchemy import select
if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
try:
    import nodriver as uc
except Exception:
    uc = None

try:
    from backend.database import async_session_maker
    from backend.models.schema import (
        Brand, FragranceDNA, FragranceLine, FragranceProduct, ProductVariant, Retailer, PriceObservation,
        FragranceMarketSegment, FragranceGenderMarketing
    )
except ImportError:
    from database import async_session_maker
    from models.schema import (
        Brand, FragranceDNA, FragranceLine, FragranceProduct, ProductVariant, Retailer, PriceObservation,
        FragranceMarketSegment, FragranceGenderMarketing
    )

@dataclass
class Job:
    target_brand: str
    search_term: str
    correlation_id: str

@dataclass
class ScrapedProduct:
    title: str
    price: float
    url: str
    is_dupe: bool = False
    inspired_by: Optional[str] = None
    volume_ml: Optional[float] = None
    concentration: Optional[str] = None
    llm_validated: bool = False

class BaseScraper:
    RETAILER_NAME = "Unknown"
    RETAILER_NORM = "unknown"
    RETAILER_URL = "https://unknown.com"

    def __init__(self):
        self.browser: Optional[Any] = None

    async def start_browser(self):
        if not self.browser:
            if uc is not None:
                self.browser = await uc.start(headless=True)
            else:
                raise RuntimeError("nodriver is not installed or available")

    async def stop_browser(self):
        if self.browser:
            self.browser.stop()
            self.browser = None

    def parse_price(self, price_str: str) -> float:
        cleaned = re.sub(r'[^\d.]', '', price_str)
        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def extract_volume_ml(self, title: str) -> Optional[float]:
        oz_match = re.search(r'(\d+(?:\.\d+)?)\s*oz', title, re.IGNORECASE)
        if oz_match:
            oz = float(oz_match.group(1))
            return round(oz * 29.5735, 1)
            
        ml_match = re.search(r'(\d+(?:\.\d+)?)\s*ml', title, re.IGNORECASE)
        if ml_match:
            return float(ml_match.group(1))
            
        return None

    def extract_concentration(self, title: str) -> str:
        title_upper = title.upper()
        if "EDP" in title_upper or "EAU DE PARFUM" in title_upper:
            return "EAU DE PARFUM"
        if "EDT" in title_upper or "EAU DE TOILETTE" in title_upper:
            return "EAU DE TOILETTE"
        if "PARFUM" in title_upper:
            return "PARFUM"
        if "EXTRAIT" in title_upper:
            return "EXTRAIT DE PARFUM"
        if "COLOGNE" in title_upper or "EDC" in title_upper:
            return "EAU DE COLOGNE"
        return "UNKNOWN"

    async def scrape(self, job: Job) -> List[ScrapedProduct]:
        raise NotImplementedError("Subclasses must implement scrape()")

    async def get_or_create_retailer(self, session: AsyncSession) -> Retailer:
        result = await session.execute(select(Retailer).filter_by(normalized_name=self.RETAILER_NORM))
        retailer = result.scalar_one_or_none()
        if not retailer:
            retailer = Retailer(name=self.RETAILER_NAME, normalized_name=self.RETAILER_NORM, website_url=self.RETAILER_URL)
            session.add(retailer)
            await session.flush()
        return retailer

    def is_valid_match(self, sp: ScrapedProduct, job: Job) -> bool:
        if getattr(sp, 'llm_validated', False):
            return True
            
        title_lower = sp.title.lower()
        search_lower = job.search_term.lower()
        target_brand_lower = job.target_brand.lower() if job.target_brand else ""
        
        # Check for clones/inspirations
        clone_phrases = [
            "inspired by", "inspired", "impression of", "impression", "type", "our version of", 
            "alternative to", "clone", "dupe", "twist", "smells like", "oil version", "our impression"
        ]
        for phrase in clone_phrases:
            if phrase in title_lower and phrase not in search_lower:
                return False

        # Brand conflict check (e.g. title has Banadirfragrance or Dunhill when target is Creed)
        known_clone_brands = ["banadir", "banadirfragrance", "armaf", "afnan", "lattafa", "maison alhambra", "french avenue", "paris corner", "zimaya", "bujairami", "fragrance world", "dunhill", "dunhil"]
        for cb in known_clone_brands:
            if cb in title_lower and cb not in target_brand_lower and cb not in search_lower:
                return False
                
        # Anti-flanker list
        flanker_words = [
            "absolu", "for her", "for women", "pour femme", "intense", "extreme", "elixir", 
            "sport", "l'eau", "fraiche", "privee", "oud", "wood", "noir", "l'intense", 
            "valentina", "lyric", "lumiere", "absolue", "cologne"
        ]
        
        for word in flanker_words:
            if re.search(rf'\b{word}\b', title_lower) and not re.search(rf'\b{word}\b', search_lower):
                return False
                
        if search_lower in title_lower:
            return True
            
        stop_words = {"the", "and", "for", "men", "women", "mens", "womens", "unisex", "eau", "de", "parfum", "toilette", "cologne", "spray", "intense", "extreme", "elixir"}
        words = [w for w in search_lower.split() if w not in stop_words and len(w) > 2]
        
        if not words:
            return False
            
        matches = 0
        for w in words:
            if re.search(rf'\b{re.escape(w)}\b', title_lower):
                matches += 1
                
        return matches == len(words)

    async def save_to_db(self, job: Job, scraped_products: List[ScrapedProduct]):
        if not scraped_products:
            print(f"[{self.RETAILER_NAME}] No products scraped for {job.search_term}.")
            return
            
        print(f"[{self.RETAILER_NAME}] Saving {len(scraped_products)} products to DB...")
        
        async with async_session_maker() as session:
            retailer = await self.get_or_create_retailer(session)
            
            # Brand
            b_norm = job.target_brand.lower().replace(" ", "_")
            result = await session.execute(select(Brand).filter_by(normalized_name=b_norm))
            brand = result.scalar_one_or_none()
            if not brand:
                brand = Brand(name=job.target_brand, normalized_name=b_norm)
                session.add(brand)
                await session.flush()
                
            # DNA
            dna_norm = job.search_term.lower().replace(" ", "_")
            result = await session.execute(select(FragranceDNA).filter_by(normalized_name=dna_norm, origin_brand_id=brand.brand_id))
            dna = result.scalar_one_or_none()
            if not dna:
                # Generate sort key by stripping leading articles
                sort_k = job.search_term
                for article in ['The ', 'Le ', 'La ', 'L\'', 'L ']:
                    if sort_k.lower().startswith(article.lower()):
                        sort_k = f"{sort_k[len(article):]}, {article.strip()}"
                        break
                        
                dna = FragranceDNA(
                    canonical_name=job.search_term, 
                    normalized_name=dna_norm, 
                    sort_key=sort_k,
                    origin_brand_id=brand.brand_id,
                    market_segment=FragranceMarketSegment.niche,
                    is_dupe=False
                )
                session.add(dna)
                await session.flush()
                
            # Line
            line_norm = f"{dna.normalized_name}_line"
            result = await session.execute(select(FragranceLine).filter_by(normalized_name=line_norm))
            line = result.scalar_one_or_none()
            if not line:
                line = FragranceLine(
                    brand_id=brand.brand_id,
                    dna_id=dna.dna_id,
                    name=f"{dna.canonical_name} Line",
                    normalized_name=line_norm,
                    marketing_gender=FragranceGenderMarketing.unisex
                )
                session.add(line)
                await session.flush()

            prices_saved = 0
            for sp in scraped_products:
                if not self.is_valid_match(sp, job):
                    print(f"[{self.RETAILER_NAME}] Skipping irrelevant search result: '{sp.title}'")
                    continue
                    
                if getattr(sp, 'is_dupe', False) and getattr(sp, 'inspired_by', None):
                    setattr(dna, 'is_dupe', True)
                    setattr(dna, 'inspired_by', sp.inspired_by)

                volume_ml = getattr(sp, 'volume_ml', None) or self.extract_volume_ml(sp.title) or 100.0
                concentration = getattr(sp, 'concentration', None) or self.extract_concentration(sp.title)
                
                prod_version = f"{dna.normalized_name}_{concentration.lower().replace(' ', '_')}"
                result = await session.execute(select(FragranceProduct).filter_by(formulation_version=prod_version))
                product = result.scalar_one_or_none()
                if not product:
                    product = FragranceProduct(
                        line_id=line.line_id,
                        formulation_version=prod_version
                    )
                    session.add(product)
                    await session.flush()
                    
                result = await session.execute(select(ProductVariant).filter_by(product_id=product.product_id, volume_ml=volume_ml))
                variant = result.scalar_one_or_none()
                if not variant:
                    pseudo_barcode = f"{prod_version}_{int(volume_ml)}ML_{self.RETAILER_NORM}"
                    variant = ProductVariant(
                        product_id=product.product_id,
                        volume_ml=volume_ml,
                        package_type="spray",
                        barcode=pseudo_barcode
                    )
                    session.add(variant)
                    await session.flush()
                    
                obs = PriceObservation(
                    variant_id=variant.variant_id,
                    retailer_id=retailer.retailer_id,
                    currency_code="USD",
                    price_amount=sp.price,
                    source_url=sp.url,
                    tax_included=False
                )
                session.add(obs)
                prices_saved += 1
                
            await session.commit()
            print(f"[{self.RETAILER_NAME}] Saved {prices_saved} new live Price Observations for {job.search_term}!")

    async def run(self, job: Job):
        try:
            await self.start_browser()
            scraped = await self.scrape(job)
            await self.save_to_db(job, scraped)
        finally:
            await self.stop_browser()
