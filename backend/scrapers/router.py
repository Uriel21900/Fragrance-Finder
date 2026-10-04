"""
Multi-Engine Scraper Router (backend/scrapers/router.py)

Routing Architecture:
- Tier 1 (Shopify Fast Path): Asynchronous httpx queries against /products.json?limit=250.
- Tier 2 (Protected Dynamic Sites): Scrapling stealth fetching -> Crawl4AI clean Markdown conversion.
- Tier 3 (Interactive / Multi-Variant Pages): browser-use with Gemini API / Playwright to navigate complex dropdowns (e.g., selecting 50ml vs 100ml sizes) on stubborn discounters.
- Neon Ingestion: Verification pass via backend/scrapers/verifier.py before atomic batch upserting into Neon PostgreSQL.
"""

import os
import re
import sys
import uuid
import json
import logging
import asyncio
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timezone
import urllib.parse

import httpx
import asyncpg
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Try relative package imports first (when used as a package),
# then fall back to absolute imports (when run directly as a script).
try:
    from .ai_parser import parse_markdown, ParsedFragrance
    from .verifier import verify_parsed_fragrance_async, VerificationResult
except ImportError:
    import sys as _sys
    _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from ai_parser import parse_markdown, ParsedFragrance  # type: ignore[import-not-found]
    from verifier import verify_parsed_fragrance_async, VerificationResult  # type: ignore[import-not-found]

# Load environment configuration
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("scraper_router")

# ==========================================
# 1. Target Registry & Store Classifications
# ==========================================

SHOPIFY_FAST_PATH_STORES: Dict[str, Dict[str, str]] = {
    "banadirfragrance.com": {"name": "Banadir Fragrance", "url": "https://banadirfragrance.com"},
    "aromaconcepts.com": {"name": "Aroma Concepts", "url": "https://aromaconcepts.com"},
    "fragflex.com": {"name": "Fragflex", "url": "https://fragflex.com"},
    "tripletraders.com": {"name": "Triple Traders", "url": "https://tripletraders.com"},
    "shoparomatix.com": {"name": "Shop Aromatix", "url": "https://shoparomatix.com"},
    "anaustore.com": {"name": "Anau Store", "url": "https://anaustore.com"},
    "lrlux.com": {"name": "LRLux", "url": "https://lrlux.com"},
}

PROTECTED_DYNAMIC_STORES: Dict[str, Dict[str, str]] = {
    "jomashop.com": {"name": "Jomashop", "url": "https://www.jomashop.com"},
    "aurafragrance.com": {"name": "Aura Fragrance", "url": "https://www.aurafragrance.com"},
    "reblscents.com": {"name": "Rebl Scents", "url": "https://reblscents.com"},
    "fragrancenet.com": {"name": "FragranceNet", "url": "https://www.fragrancenet.com"},
    "fragrancex.com": {"name": "FragranceX", "url": "https://www.fragrancex.com"},
}

INTERACTIVE_VARIANT_STORES: Dict[str, Dict[str, str]] = {
    "perfumania.com": {"name": "Perfumania", "url": "https://www.perfumania.com"},
    "fragrancebuy.ca": {"name": "FragranceBuy", "url": "https://fragrancebuy.ca"},
    "maxaroma.com": {"name": "MaxAroma", "url": "https://www.maxaroma.com"},
}

# ==========================================
# 2. Data Models
# ==========================================

class ExtractedVariant(BaseModel):
    volume_ml: float = 100.0
    package_type: str = "spray"
    price: float = 0.0
    is_refill: bool = False
    sku: Optional[str] = None

class ScrapedProductRecord(BaseModel):
    store_name: str
    store_domain: str
    product_title: str
    brand_name: str
    product_name: str
    is_dupe: bool = False
    inspired_by: Optional[str] = None
    price: float = 0.0
    volume_ml: float = 100.0
    package_type: str = "spray"
    variants: List[ExtractedVariant] = Field(default_factory=list)
    source_url: str
    image_url: Optional[str] = None
    confidence_score: float = 0.90
    requires_quarantine: bool = False
    quarantine_reason: Optional[str] = None


# ==========================================
# 3. Tier 1: Shopify Fast Path (httpx async)
# ==========================================

class ShopifyFastPath:
    """Asynchronously queries public /products.json?limit=250 endpoints."""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 FragranceFinder/2.0",
        "Accept": "application/json"
    }

    @classmethod
    async def fetch_products(cls, domain: str, limit: int = 250) -> List[Dict[str, Any]]:
        clean_domain = domain.replace("https://", "").replace("http://", "").strip("/")
        store_info = SHOPIFY_FAST_PATH_STORES.get(
            clean_domain,
            {"name": clean_domain.capitalize(), "url": f"https://{clean_domain}"}
        )
        endpoint = f"{store_info['url']}/products.json?limit={limit}"
        logger.info(f"[Tier 1 Shopify] Querying {endpoint}...")
        records: List[Dict[str, Any]] = []

        async with httpx.AsyncClient(timeout=25.0, headers=cls.HEADERS, follow_redirects=True) as client:
            try:
                resp = await client.get(endpoint)
                if resp.status_code == 200:
                    data = resp.json()
                    products = data.get("products", [])
                    logger.info(f"[Tier 1 Shopify] Retrieved {len(products)} products from {clean_domain}.")
                    for p in products:
                        title = p.get("title", "")
                        vendor = p.get("vendor", "") or store_info["name"]
                        handle = p.get("handle", "")
                        body_html = p.get("body_html", "")
                        images = p.get("images", [])
                        raw_variants = p.get("variants", [])
                        
                        img_url = images[0].get("src") if images else None
                        
                        parsed_variants: List[ExtractedVariant] = []
                        lowest_price = 0.0

                        for v in raw_variants:
                            try:
                                v_price = float(v.get("price", 0.0))
                            except (ValueError, TypeError):
                                v_price = 0.0

                            v_title = v.get("title", "")
                            # Parse volume in variant title (e.g. 100ml, 3.4 oz, 50ml)
                            vol = 100.0
                            vol_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:ml|oz|fl\s*oz)", v_title, re.IGNORECASE)
                            if vol_m:
                                vol = float(vol_m.group(1))
                                if "oz" in v_title.lower() and vol < 15:
                                    vol = vol * 29.5735
                            elif "100" in v_title:
                                vol = 100.0
                            elif "50" in v_title:
                                vol = 50.0

                            if lowest_price == 0.0 or (0 < v_price < lowest_price):
                                lowest_price = v_price

                            parsed_variants.append(ExtractedVariant(
                                volume_ml=round(vol, 1),
                                package_type="spray",
                                price=v_price,
                                sku=v.get("sku")
                            ))

                        product_url = f"{store_info['url']}/products/{handle}" if handle else store_info['url']

                        records.append({
                            "store_name": store_info["name"],
                            "store_domain": clean_domain,
                            "title": title,
                            "vendor": vendor,
                            "body_html": body_html,
                            "price": lowest_price,
                            "product_url": product_url,
                            "image_url": img_url,
                            "variants": parsed_variants
                        })
            except Exception as e:
                logger.error(f"[Tier 1 Shopify] Failed to fetch {domain}: {e}")

        return records


# ==========================================
# 4. Tier 2: Protected Dynamic Sites (Scrapling + Crawl4AI)
# ==========================================

class ScraplingCrawl4AIPath:
    """Uses Scrapling for stealth page fetching and Crawl4AI for clean Markdown conversion."""

    @classmethod
    async def fetch_clean_markdown(cls, url: str) -> str:
        logger.info(f"[Tier 2 Protected] Fetching stealth HTML via Scrapling for {url}...")
        raw_html = ""

        # Step A: Stealth HTML fetching with Scrapling
        try:
            from scrapling import Fetcher
            fetcher = Fetcher(stealthy_headers=True)
            response = fetcher.get(url)
            if response and response.body:
                raw_html = response.body.decode("utf-8", errors="ignore")
                logger.info(f"[Tier 2 Protected] Scrapling retrieved {len(raw_html)} bytes of HTML.")
        except Exception as e:
            logger.warning(f"[Tier 2 Protected] Scrapling fetch note: {e}")

        # Step B: Clean Markdown conversion with Crawl4AI
        try:
            from crawl4ai import AsyncWebCrawler
            async with AsyncWebCrawler(verbose=False) as crawler:
                if raw_html:
                    # Feed Scrapling HTML directly to Crawl4AI
                    res = await crawler.arun(url=url, raw_html=raw_html)
                else:
                    res = await crawler.arun(url=url)

                if res and res.markdown:
                    logger.info(f"[Tier 2 Protected] Crawl4AI generated {len(res.markdown)} chars of clean Markdown.")
                    return res.markdown
        except Exception as e:
            logger.warning(f"[Tier 2 Protected] Crawl4AI markdown conversion note: {e}")

        # Fallback text extraction if Crawl4AI is unavailable
        if raw_html:
            cleaned_text = re.sub(r"<script.*?</script>", " ", raw_html, flags=re.DOTALL | re.IGNORECASE)
            cleaned_text = re.sub(r"<style.*?</style>", " ", cleaned_text, flags=re.DOTALL | re.IGNORECASE)
            cleaned_text = re.sub(r"<[^>]+>", " ", cleaned_text)
            return re.sub(r"\s+", " ", cleaned_text).strip()

        return ""


# ==========================================
# 5. Tier 3: Interactive Multi-Variant Pages (browser-use + Gemini)
# ==========================================

class InteractiveVariantPath:
    """Uses browser-use with Gemini API or Playwright to navigate complex size dropdowns (e.g. 50ml vs 100ml)."""

    @classmethod
    async def extract_interactive_variants(cls, url: str) -> List[Dict[str, Any]]:
        logger.info(f"[Tier 3 Interactive] Navigating dropdowns and variant selectors on {url}...")
        results: List[Dict[str, Any]] = []

        api_key = os.getenv("GEMINI_API_KEY")

        # Method A: Use browser-use Agent if available and API key present
        if api_key:
            try:
                from browser_use import Agent as BrowserAgent
                from langchain_google_genai import ChatGoogleGenerativeAI

                llm: Any = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash",
                    google_api_key=api_key
                )
                task_prompt = f"""
                Navigate to {url}.
                1. Identify all fragrance size/volume dropdown options (e.g., 30ml, 50ml, 100ml, 200ml, 3.4 oz).
                2. Click or select each option to observe the price change.
                3. Return a structured list of variants with volume_ml and price.
                """
                agent = BrowserAgent(
                    task=task_prompt,
                    llm=llm
                )
                history = await agent.run(max_steps=8)
                if history:
                    logger.info(f"[Tier 3 Interactive] browser-use completed navigation with result: {history.final_result()}")
            except Exception as e:
                logger.debug(f"[Tier 3 Interactive] browser-use Agent note: {e}")

        # Method B: Direct Playwright interactive DOM selector
        try:
            from patchright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                )
                page = await context.new_page()
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await page.wait_for_timeout(2000)

                # Look for select boxes, size pills, and buttons
                dropdown_options = await page.query_selector_all("select option, .variant-picker button, [data-variant-id]")
                for opt in dropdown_options[:8]:
                    opt_text = await opt.inner_text()
                    vol_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:ml|oz)", opt_text, re.IGNORECASE)
                    price_m = re.search(r"\$\s*(\d+(?:\.\d{2})?)", opt_text)
                    
                    vol = float(vol_m.group(1)) if vol_m else 100.0
                    price = float(price_m.group(1)) if price_m else 0.0

                    if vol > 0:
                        results.append({
                            "volume_ml": vol,
                            "price": price,
                            "label": opt_text.strip()
                        })

                await browser.close()
                logger.info(f"[Tier 3 Interactive] Harvested {len(results)} interactive variants.")
        except Exception as e:
            logger.warning(f"[Tier 3 Interactive] Playwright interactive automation note: {e}")

        return results


# ==========================================
# 6. Pipeline Processor: AI Parsing & QA Verification
# ==========================================

class PipelineProcessor:
    """Processes scraped payloads, extracts structured metadata, and applies Gemini QA verification."""

    CLONE_PATTERNS = [
        r"(?:inspired\s+by|impression\s+of|our\s+version\s+of|clone\s+of|dupe\s+for|smells\s+like)\s+[:\-]?\s*([a-zA-Z0-9\s\'\.\-]+?)(?:\s*\(|\s*\[|\s*\||\s*-\s*\d|\s*\d+\s*ml|$)",
        r"(?:cloning|dupes)\s+([a-zA-Z0-9\s\'\.\-]+)",
    ]

    @classmethod
    async def process_shopify_items(cls, raw_items: List[Dict[str, Any]]) -> List[ScrapedProductRecord]:
        records: List[ScrapedProductRecord] = []

        for item in raw_items:
            title = item["title"]
            vendor = item["vendor"] or item["store_name"]
            body = item.get("body_html", "")
            price = item.get("price", 29.99)
            url = item.get("product_url", "")
            img_url = item.get("image_url", None)
            variants = item.get("variants", [])

            is_dupe = False
            inspired_by = None
            search_text = f"{title} {body}"

            for pat in cls.CLONE_PATTERNS:
                m = re.search(pat, search_text, re.IGNORECASE)
                if m:
                    target_cand = m.group(1).strip(" -:[]()")
                    if 2 < len(target_cand) < 60:
                        is_dupe = True
                        inspired_by = target_cand
                        break

            if not is_dupe and any(k in title.lower() for k in ["inspired by", "impression", "dupe", "clone"]):
                is_dupe = True

            vol_m = re.search(r"(\d+(?:\.\d+)?)\s*(?:ml|fl\s*oz|oz)", title, re.IGNORECASE)
            volume_ml = float(vol_m.group(1)) if vol_m else 100.0
            if "oz" in title.lower() and volume_ml < 15:
                volume_ml = volume_ml * 29.5735

            record = ScrapedProductRecord(
                store_name=item["store_name"],
                store_domain=item["store_domain"],
                product_title=title,
                brand_name=vendor,
                product_name=title,
                is_dupe=is_dupe,
                inspired_by=inspired_by,
                price=price,
                volume_ml=round(volume_ml, 1),
                variants=variants,
                source_url=url,
                image_url=img_url,
                confidence_score=0.90 if is_dupe else 0.85
            )

            # Gemini verification pass
            if record.is_dupe and record.inspired_by:
                verdict = await verify_parsed_fragrance_async(
                    clone_name=record.product_name,
                    clone_brand=record.brand_name,
                    inspired_by=record.inspired_by,
                    search_term=record.product_title
                )
                if verdict.is_hallucination:
                    record.requires_quarantine = True
                    record.quarantine_reason = f"Hallucination flagged: {verdict.reasoning}"
                elif verdict.requires_quarantine or verdict.confidence_score < 0.85:
                    record.requires_quarantine = True
                    record.quarantine_reason = f"Low confidence ({verdict.confidence_score:.2f}): {verdict.reasoning}"
                elif verdict.corrected_inspired_by:
                    record.inspired_by = verdict.corrected_inspired_by

            records.append(record)

        return records

    @classmethod
    async def process_markdown(cls, markdown: str, store_domain: str, store_name: str) -> List[ScrapedProductRecord]:
        """Send Markdown through ai_parser.py (Gemini Pydantic extraction)."""
        parsed_fragrances: List[ParsedFragrance] = parse_markdown(markdown, search_term="fragrance catalog", target_brand=store_name)
        records: List[ScrapedProductRecord] = []

        for pf in parsed_fragrances:
            record = ScrapedProductRecord(
                store_name=store_name,
                store_domain=store_domain,
                product_title=f"{pf.clone_brand} {pf.clone_name}",
                brand_name=pf.clone_brand,
                product_name=pf.clone_name,
                is_dupe=pf.is_dupe,
                inspired_by=pf.inspired_by,
                price=pf.price if pf.price > 0 else 39.99,
                volume_ml=100.0,
                source_url=f"https://{store_domain}",
                confidence_score=pf.confidence_score
            )

            if record.is_dupe and record.inspired_by:
                verdict = await verify_parsed_fragrance_async(
                    clone_name=record.product_name,
                    clone_brand=record.brand_name,
                    inspired_by=record.inspired_by
                )
                if verdict.is_hallucination:
                    record.requires_quarantine = True
                    record.quarantine_reason = f"Hallucination: {verdict.reasoning}"
                elif verdict.confidence_score < 0.85 or verdict.requires_quarantine:
                    record.requires_quarantine = True
                    record.quarantine_reason = f"Low confidence QA: {verdict.reasoning}"
                elif verdict.corrected_inspired_by:
                    record.inspired_by = verdict.corrected_inspired_by

            records.append(record)

        return records


# ==========================================
# 7. Neon PostgreSQL Batch Upsert Engine
# ==========================================

def normalize_key(text_val: str) -> str:
    """Generate normalized database key."""
    if not text_val:
        return "unknown"
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text_val.strip().lower()).strip("_")
    return cleaned if cleaned else "unknown"

def infer_gender(text_val: str) -> str:
    """Infer gender classification from fragrance name."""
    if not text_val:
        return "unisex"
    n = text_val.lower()
    if any(k in n for k in ['for men', 'for him', 'pour homme', 'eau de homme', 'edp man', 'edt man', ' for man', 'men spray', 'men edp', 'men edt', 'homme']):
        return 'masculine'
    if any(k in n for k in ['for women', 'for her', 'pour femme', 'eau de femme', 'edp woman', 'edt woman', ' for woman', 'women spray', 'ladies', 'women edp', 'women edt', 'femme']):
        return 'feminine'
    return 'unisex'


class NeonDatabaseSync:
    """High-performance batch upsert engine into Neon PostgreSQL."""

    @staticmethod
    async def batch_upsert(pool: asyncpg.Pool, records: List[ScrapedProductRecord]) -> Dict[str, int]:
        stats = {
            "processed": len(records),
            "brands_upserted": 0,
            "dnas_upserted": 0,
            "products_upserted": 0,
            "variants_upserted": 0,
            "prices_inserted": 0,
            "quarantined": 0,
            "relationships_upserted": 0
        }

        if not records:
            return stats

        async with pool.acquire() as conn:
            async with conn.transaction():
                retailer_cache: Dict[str, uuid.UUID] = {}

                for item in records:
                    # 1. Route to Quarantine Review if flagged
                    if item.requires_quarantine:
                        await conn.execute("""
                            INSERT INTO quarantine_reviews (
                                review_id, clone_brand, clone_name, claimed_target,
                                reason, confidence_score, source_url, raw_payload,
                                status, created_at, updated_at
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending', NOW(), NOW());
                        """,
                            uuid.uuid4(),
                            item.brand_name,
                            item.product_name,
                            item.inspired_by,
                            item.quarantine_reason or "Flagged by QA verifier",
                            item.confidence_score,
                            item.source_url,
                            json.dumps(item.model_dump())
                        )
                        stats["quarantined"] += 1
                        continue

                    # 2. Upsert Retailer
                    r_norm = normalize_key(item.store_domain)
                    if r_norm not in retailer_cache:
                        r_id = await conn.fetchval("""
                            INSERT INTO retailer (retailer_id, name, normalized_name, website_url, is_marketplace)
                            VALUES ($1, $2, $3, $4, false)
                            ON CONFLICT (normalized_name)
                            DO UPDATE SET name = EXCLUDED.name
                            RETURNING retailer_id;
                        """, uuid.uuid4(), item.store_name, r_norm, f"https://{item.store_domain}")
                        retailer_cache[r_norm] = r_id
                    retailer_id = retailer_cache[r_norm]

                    # 3. Upsert Brand
                    b_norm = normalize_key(item.brand_name)
                    brand_id = await conn.fetchval("""
                        INSERT INTO brand (brand_id, name, normalized_name, created_at, updated_at)
                        VALUES ($1, $2, $3, NOW(), NOW())
                        ON CONFLICT (normalized_name)
                        DO UPDATE SET updated_at = NOW()
                        RETURNING brand_id;
                    """, uuid.uuid4(), item.brand_name, b_norm)
                    stats["brands_upserted"] += 1

                    # 4. Upsert Fragrance DNA
                    dna_name = item.product_name
                    dna_norm = normalize_key(dna_name)
                    inferred_gender = infer_gender(dna_name)
                    dna_id = await conn.fetchval("""
                        INSERT INTO fragrance_dna (
                            dna_id, canonical_name, normalized_name, origin_brand_id,
                            market_segment, is_original_dna, is_dupe, inspired_by,
                            image_url, gender, created_at, updated_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, NOW(), NOW())
                        ON CONFLICT (origin_brand_id, normalized_name)
                        DO UPDATE SET
                            is_dupe = EXCLUDED.is_dupe,
                            inspired_by = COALESCE(EXCLUDED.inspired_by, fragrance_dna.inspired_by),
                            image_url = COALESCE(EXCLUDED.image_url, fragrance_dna.image_url),
                            gender = COALESCE(fragrance_dna.gender, EXCLUDED.gender),
                            updated_at = NOW()
                        RETURNING dna_id;
                    """,
                        uuid.uuid4(),
                        dna_name,
                        dna_norm,
                        brand_id,
                        'clone' if item.is_dupe else 'designer',
                        not item.is_dupe,
                        item.is_dupe,
                        item.inspired_by,
                        item.image_url,
                        inferred_gender
                    )
                    stats["dnas_upserted"] += 1

                    # 5. Upsert Fragrance Line
                    line_norm = f"{dna_norm}_line"
                    line_id = await conn.fetchval("""
                        INSERT INTO fragrance_line (
                            line_id, brand_id, dna_id, name, normalized_name, marketing_gender, created_at, updated_at
                        )
                        VALUES ($1, $2, $3, $4, $5, $6::fragrance_gender_marketing, NOW(), NOW())
                        ON CONFLICT (brand_id, normalized_name)
                        DO UPDATE SET 
                            marketing_gender = COALESCE(fragrance_line.marketing_gender, EXCLUDED.marketing_gender),
                            updated_at = NOW()
                        RETURNING line_id;
                    """, uuid.uuid4(), brand_id, dna_id, dna_name, line_norm, inferred_gender)

                    # 6. Upsert Fragrance Product
                    product_id = await conn.fetchval("""
                        INSERT INTO fragrance_product (
                            product_id, line_id, concentration_id, formulation_version,
                            is_limited_edition, is_active, created_at, updated_at
                        )
                        VALUES ($1, $2, NULL, 'original', false, true, NOW(), NOW())
                        ON CONFLICT (line_id, concentration_id, formulation_version)
                        DO UPDATE SET is_active = true, updated_at = NOW()
                        RETURNING product_id;
                    """, uuid.uuid4(), line_id)
                    stats["products_upserted"] += 1

                    # 7. Upsert Product Variants & Pricing
                    variant_list = item.variants if item.variants else [
                        ExtractedVariant(volume_ml=item.volume_ml, package_type=item.package_type, price=item.price)
                    ]

                    for v in variant_list:
                        vol = v.volume_ml if v.volume_ml > 0 else 100.0
                        pkg = v.package_type if v.package_type else "spray"
                        v_price = v.price if v.price > 0 else item.price

                        variant_id = await conn.fetchval("""
                            INSERT INTO product_variant (
                                variant_id, product_id, volume_ml, package_type, is_refill, is_active
                            )
                            VALUES ($1, $2, $3, $4, false, true)
                            ON CONFLICT (product_id, volume_ml, package_type, is_refill)
                            DO UPDATE SET is_active = true
                            RETURNING variant_id;
                        """, uuid.uuid4(), product_id, vol, pkg)
                        stats["variants_upserted"] += 1

                        if v_price > 0:
                            await conn.execute("""
                                INSERT INTO price_observation (
                                    price_observation_id, variant_id, retailer_id, observed_at,
                                    currency_code, price_amount, condition, source_url, captured_at
                                )
                                VALUES ($1, $2, $3, NOW(), 'USD', $4, 'new', $5, NOW());
                            """, uuid.uuid4(), variant_id, retailer_id, v_price, item.source_url)
                            stats["prices_inserted"] += 1

                    # 8. Link DNA Relationship if dupe
                    if item.is_dupe and item.inspired_by:
                        target_norm = normalize_key(item.inspired_by)
                        target_dna_id = await conn.fetchval("""
                            SELECT dna_id FROM fragrance_dna
                            WHERE normalized_name ILIKE $1 OR canonical_name ILIKE $2
                            LIMIT 1;
                        """, f"%{target_norm}%", f"%{item.inspired_by}%")

                        if target_dna_id and target_dna_id != dna_id:
                            await conn.execute("""
                                INSERT INTO dna_relationship (
                                    dna_relationship_id, source_dna_id, target_dna_id,
                                    relationship_type, similarity_score, confidence_score,
                                    evidence_url, evidence_note, asserted_by, created_at, updated_at
                                )
                                VALUES ($1, $2, $3, 'inspired_by', 0.90, $4, $5, $6, 'Multi-Engine Router', NOW(), NOW())
                                ON CONFLICT (source_dna_id, target_dna_id, relationship_type)
                                DO UPDATE SET
                                    similarity_score = EXCLUDED.similarity_score,
                                    confidence_score = EXCLUDED.confidence_score,
                                    evidence_url = EXCLUDED.evidence_url,
                                    updated_at = NOW();
                            """, uuid.uuid4(), dna_id, target_dna_id, item.confidence_score, item.source_url, f"Scraped from {item.store_name}")
                            stats["relationships_upserted"] += 1

        logger.info(f"[Database Sync] Batch upsert completed: {stats}")
        return stats


# ==========================================
# 8. Master Router Dispatcher
# ==========================================

async def route_and_scrape(target: str, limit: int = 50, force_tier: Optional[int] = None) -> Dict[str, Any]:
    """
    Routes a target store domain through the optimal scraping tier:
    - Tier 1: Shopify Fast Path (httpx async)
    - Tier 2: Protected Dynamic Sites (Scrapling + Crawl4AI)
    - Tier 3: Interactive Multi-Variant Pages (browser-use / Playwright)
    """
    clean_target = target.replace("https://", "").replace("http://", "").strip("/")
    logger.info(f"=== DISPATCHING MULTI-ENGINE SCRAPER FOR: {clean_target} ===")

    records: List[ScrapedProductRecord] = []
    selected_tier = force_tier

    # Determine Tier automatically if not forced
    if not selected_tier:
        if clean_target in SHOPIFY_FAST_PATH_STORES:
            selected_tier = 1
        elif clean_target in INTERACTIVE_VARIANT_STORES:
            selected_tier = 3
        elif clean_target in PROTECTED_DYNAMIC_STORES:
            selected_tier = 2
        else:
            selected_tier = 1  # Default to Shopify check first

    logger.info(f"[Router Dispatch] Selected Engine: Tier {selected_tier}")

    # --- TIER 1 ---
    if selected_tier == 1:
        raw_items = await ShopifyFastPath.fetch_products(clean_target, limit=limit)
        if raw_items:
            records = await PipelineProcessor.process_shopify_items(raw_items)
        else:
            logger.info("[Router Dispatch] Tier 1 returned 0 items, falling back to Tier 2 (Scrapling + Crawl4AI)...")
            markdown = await ScraplingCrawl4AIPath.fetch_clean_markdown(f"https://{clean_target}")
            records = await PipelineProcessor.process_markdown(markdown, clean_target, clean_target.capitalize())

    # --- TIER 2 ---
    elif selected_tier == 2:
        store_info = PROTECTED_DYNAMIC_STORES.get(clean_target, {"name": clean_target.capitalize(), "url": f"https://{clean_target}"})
        markdown = await ScraplingCrawl4AIPath.fetch_clean_markdown(store_info["url"])
        records = await PipelineProcessor.process_markdown(markdown, clean_target, store_info["name"])

    # --- TIER 3 ---
    elif selected_tier == 3:
        store_info = INTERACTIVE_VARIANT_STORES.get(clean_target, {"name": clean_target.capitalize(), "url": f"https://{clean_target}"})
        interactive_variants = await InteractiveVariantPath.extract_interactive_variants(store_info["url"])
        
        # Also grab markdown for general catalog parsing
        markdown = await ScraplingCrawl4AIPath.fetch_clean_markdown(store_info["url"])
        records = await PipelineProcessor.process_markdown(markdown, clean_target, store_info["name"])

        # Attach interactive variants to corresponding records if found
        if interactive_variants and records:
            for r in records:
                for iv in interactive_variants:
                    r.variants.append(ExtractedVariant(
                        volume_ml=iv.get("volume_ml", 100.0),
                        package_type="spray",
                        price=iv.get("price", r.price)
                    ))

    # --- NEON DATABASE INGESTION ---
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL environment variable is not set. "
            "Configure it in your .env file or GitHub Actions secrets."
        )
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    pool = await asyncpg.create_pool(dsn=db_url, min_size=1, max_size=5)
    if pool is None:
        raise RuntimeError("asyncpg.create_pool() returned None — check DATABASE_URL and SSL settings.")
    try:
        db_stats = await NeonDatabaseSync.batch_upsert(pool, records)
    finally:
        await pool.close()

    logger.info("=== MULTI-ENGINE SCRAPER RUN COMPLETED ===")
    return {
        "target": clean_target,
        "engine_tier": selected_tier,
        "total_extracted": len(records),
        "db_stats": db_stats,
        "sample_records": [r.model_dump() for r in records[:3]]
    }


if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "banadirfragrance.com"
    tier_arg = int(sys.argv[2]) if len(sys.argv) > 2 else None
    res = asyncio.run(route_and_scrape(target_arg, force_tier=tier_arg))
    print("\n--- MULTI-ENGINE SCRAPER EXECUTION SUMMARY ---")
    print(json.dumps(res, indent=2, default=str))
