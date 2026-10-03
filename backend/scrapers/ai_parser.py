"""
AI Parser: Extracts structured fragrance and clone relationships from Markdown,
HTML, community forum discussions, and video transcripts using Gemini and Google Antigravity SDK.
"""

import os
import re
import json
import logging
from typing import List, Optional, cast
from pydantic import BaseModel, Field

logger = logging.getLogger("ai_parser")

class ParsedFragrance(BaseModel):
    clone_brand: str = Field(description="The brand of the fragrance or clone house (e.g. Lattafa, Armaf, Bujairami, French Avenue, Afnan).")
    clone_name: str = Field(description="The name of the fragrance or clone product.")
    is_dupe: bool = Field(default=False, description="True if this is explicitly a clone/dupe/inspired-by fragrance.")
    inspired_by: Optional[str] = Field(default=None, description="The original target fragrance DNA this clones, if known (e.g. Creed Aventus, Angels' Share, Baccarat Rouge 540).")
    price: float = Field(default=0.0, description="The numeric price extracted in USD.")
    stock_status: bool = Field(default=True, description="True if in stock.")
    confidence_score: float = Field(default=0.90, description="Confidence score from 0.0 to 1.0.")

class ParsedFragranceBatch(BaseModel):
    fragrances: List[ParsedFragrance] = Field(default_factory=list)


def parse_markdown(markdown_content: str, search_term: str = "", target_brand: str = "") -> List[ParsedFragrance]:
    """Parse raw markdown from Crawl4AI, Scrapling, Reddit discussions, or YouTube transcripts into structured Pydantic models."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.info("[AI Parser] GEMINI_API_KEY not found. Running deterministic heuristic extractor.")
        return _heuristic_parse(markdown_content, search_term, target_brand)

    # 1. Try Google Antigravity SDK
    try:
        from google.antigravity import Agent, LocalAgentConfig
        import asyncio

        config = LocalAgentConfig(
            response_schema=ParsedFragranceBatch,
            api_key=api_key
        )
        prompt = f"""
        You are an expert fragrance parser. Extract all relevant fragrances and clone relationships from the following text/markdown.
        Search Intent / Context: {search_term} by {target_brand}
        
        Be extremely careful to identify if a fragrance is a clone/dupe ('inspired by', 'our version of', 'dupe of', 'impression of', 'smells like').
        Extract:
        - clone_brand
        - clone_name
        - is_dupe (bool)
        - inspired_by (target fragrance name, e.g. Creed Aventus, Baccarat Rouge 540, etc.)
        - price (float)
        - stock_status (bool)
        - confidence_score (0.0 to 1.0)
        
        Content:
        {markdown_content[:8000]}
        """

        async def _run_agent():
            async with Agent(config) as agent:
                resp = await agent.chat(prompt)
                parsed = await resp.structured_output()
                if parsed and "fragrances" in parsed:
                    return [ParsedFragrance(**f) for f in parsed["fragrances"]]
                return []

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    results = pool.submit(asyncio.run, _run_agent()).result()
                    if results:
                        return results
            else:
                results = asyncio.run(_run_agent())
                if results:
                    return results
        except Exception as agy_err:
            logger.debug(f"[AI Parser] Antigravity Agent call note: {agy_err}")
    except Exception as e:
        logger.debug(f"[AI Parser] Antigravity SDK note: {e}")

    # 2. Fallback to google-genai Client
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = f"""
        You are an expert fragrance parser. Extract all relevant fragrances from the following text.
        Target Search: {search_term} by {target_brand}
        """
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[prompt, markdown_content[:8000]],
            config={
                'response_mime_type': 'application/json',
                'response_schema': list[ParsedFragrance],
            },
        )
        if hasattr(response, 'parsed') and response.parsed:
            if isinstance(response.parsed, list):
                return cast(List[ParsedFragrance], response.parsed)
    except Exception as e:
        logger.warning(f"[AI Parser] Error parsing with google-genai: {e}")

    return _heuristic_parse(markdown_content, search_term, target_brand)


def _heuristic_parse(content: str, search_term: str = "", target_brand: str = "") -> List[ParsedFragrance]:
    """Deterministic regex-based fallback extractor for fragrance and clone claims."""
    results: List[ParsedFragrance] = []
    lines = content.split("\n")

    patterns = [
        r"(?:inspired\s+by|impression\s+of|our\s+version\s+of|clone\s+of|dupe\s+for|dupes|smells\s+like)\s+[:\-]?\s*([a-zA-Z0-9\s\'\.\-]+?)(?:\s*\(|\s*\[|\s*\||\s*-\s*\d|\s*\d+\s*ml|$)",
    ]

    for line in lines:
        line_clean = line.strip(" #*[]-")
        if not line_clean or len(line_clean) < 4:
            continue

        price = 0.0
        price_match = re.search(r"\$\s*(\d+(?:\.\d{2})?)", line_clean)
        if price_match:
            price = float(price_match.group(1))

        is_dupe = False
        target = None
        for pat in patterns:
            m = re.search(pat, line_clean, re.IGNORECASE)
            if m:
                target_cand = m.group(1).strip(" -:[]()")
                if 2 < len(target_cand) < 50:
                    is_dupe = True
                    target = target_cand
                    break

        if is_dupe or price > 0:
            brand = target_brand if target_brand else "Clone House"
            results.append(ParsedFragrance(
                clone_brand=brand,
                clone_name=line_clean[:50],
                is_dupe=is_dupe,
                inspired_by=target,
                price=price if price > 0 else 39.99,
                stock_status=True,
                confidence_score=0.90 if is_dupe else 0.75
            ))

    return results


def get_llm_strategy(target_brand: str, search_term: str):
    """Crawl4AI extraction strategy helper."""
    try:
        from crawl4ai.extraction_strategy import LLMExtractionStrategy
        api_key = os.getenv("GEMINI_API_KEY", "")
        instruction = f"Extract all fragrances matching {search_term} by {target_brand}. Identify if any are clones or inspired by another fragrance."
        return LLMExtractionStrategy(
            provider="gemini/gemini-1.5-flash",
            api_token=api_key,
            schema=ParsedFragrance.model_json_schema(),
            extraction_type="schema",
            instruction=instruction,
        )
    except Exception as e:
        logger.debug(f"[AI Parser] LLMExtractionStrategy fallback: {e}")
        return None

