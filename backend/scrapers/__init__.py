"""
scrapers package initialization.
Safe lazy/optional imports to avoid hard crashes when optional browser/Crawl4AI
dependencies are not installed in lightweight runners (such as GitHub Actions).
"""

__all__ = [
    "BaseScraper",
    "Job",
    "ScrapedProduct",
    "JomashopScraper",
    "MacysScraper",
    "FragFlexScraper",
    "route_and_scrape",
    "ShopifyFastPath",
    "ScraplingCrawl4AIPath",
    "InteractiveVariantPath",
    "NeonDatabaseSync",
    "PipelineProcessor",
    "ScrapedProductRecord",
    "parse_markdown",
    "ParsedFragrance",
    "verify_parsed_fragrance",
    "verify_parsed_fragrance_async",
    "VerificationResult",
]

try:
    from .base import BaseScraper, Job, ScrapedProduct
except ImportError:
    pass

try:
    from .jomashop import JomashopScraper
except ImportError:
    pass

try:
    from .macys import MacysScraper
except ImportError:
    pass

try:
    from .fragflex import FragFlexScraper
except ImportError:
    pass

try:
    from .router import (
        route_and_scrape,
        ShopifyFastPath,
        ScraplingCrawl4AIPath,
        InteractiveVariantPath,
        NeonDatabaseSync,
        PipelineProcessor,
        ScrapedProductRecord,
    )
except ImportError:
    pass

try:
    from .ai_parser import parse_markdown, ParsedFragrance
except ImportError:
    pass

try:
    from .verifier import verify_parsed_fragrance, verify_parsed_fragrance_async, VerificationResult
except ImportError:
    pass
