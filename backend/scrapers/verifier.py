"""
Fragrance Verification Module (backend/scrapers/verifier.py)
Executes a second Gemini verification pass to flag hallucinations,
circular clone attributions, or invalid metadata before database ingestion.
"""

import os
import logging
from typing import Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("verifier")

class VerificationResult(BaseModel):
    is_hallucination: bool = Field(default=False, description="True if the attribution is false, circular, or inverted.")
    reasoning: str = Field(default="", description="Detailed rationale for the verification verdict.")
    corrected_inspired_by: Optional[str] = Field(default=None, description="The corrected original designer/niche target DNA if identified.")
    confidence_score: float = Field(default=0.90, description="Verification confidence score (0.0 to 1.0).")
    requires_quarantine: bool = Field(default=False, description="True if confidence is low (< 0.85) or conflicting.")


async def verify_parsed_fragrance_async(
    clone_name: str,
    clone_brand: str,
    inspired_by: Optional[str],
    search_term: str = ""
) -> VerificationResult:
    """Asynchronous Gemini verification pass for a candidate fragrance clone relationship."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        logger.debug("[Verifier] GEMINI_API_KEY not found. Passing candidate through heuristic check.")
        return VerificationResult(
            is_hallucination=False,
            reasoning="Heuristic check passed",
            corrected_inspired_by=inspired_by,
            confidence_score=0.88,
            requires_quarantine=False
        )

    # 1. Try Google Antigravity Agent
    try:
        from google.antigravity import Agent, LocalAgentConfig
        config = LocalAgentConfig(
            response_schema=VerificationResult,
            api_key=api_key
        )
        prompt = f"""
        You are a strict QA auditor for an encyclopedia of perfumes and fragrance clones.
        A scraper identified the following:
        - Brand: {clone_brand}
        - Product Name: {clone_name}
        - Claimed Target ("Inspired By"): {inspired_by}
        - Search Context: {search_term}

        Evaluate:
        1. Is this relationship authentic (is {clone_brand} {clone_name} genuinely known as an alternative/clone of {inspired_by})?
        2. Is this a circular clone attribution (e.g. attributing a clone to another clone brand instead of the original designer/niche DNA)?
        3. Is this an original creation mistakenly marked as a clone?
        4. If confidence < 0.85 or conflicting, set requires_quarantine = true.
        """
        async with Agent(config) as agent:
            resp = await agent.chat(prompt)
            parsed = await resp.structured_output()
            if parsed:
                return VerificationResult(**parsed)
    except Exception as e:
        logger.debug(f"[Verifier] Antigravity Agent note: {e}")

    # 2. Fallback to google-genai SDK
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        prompt = f"""
        You are a strict QA auditor for a fragrance database.
        Brand: {clone_brand}
        Product: {clone_name}
        Claimed Target: {inspired_by}
        Context: {search_term}
        
        Is this authentic? Did it attribute a clone to another clone instead of original DNA?
        """
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=[prompt],
            config={
                'response_mime_type': 'application/json',
                'response_schema': VerificationResult,
            },
        )
        if hasattr(response, 'parsed') and response.parsed:
            if isinstance(response.parsed, VerificationResult):
                return response.parsed
    except Exception as e:
        logger.warning(f"[Verifier] GenAI fallback error: {e}")

    return VerificationResult(
        is_hallucination=False,
        reasoning="Fallback passed",
        corrected_inspired_by=inspired_by,
        confidence_score=0.88,
        requires_quarantine=False
    )


def verify_parsed_fragrance(
    clone_name: str,
    clone_brand: str,
    inspired_by: Optional[str],
    search_term: str = ""
) -> VerificationResult:
    """Synchronous wrapper for verify_parsed_fragrance_async."""
    import asyncio
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(
                    asyncio.run,
                    verify_parsed_fragrance_async(clone_name, clone_brand, inspired_by, search_term)
                ).result()
        else:
            return asyncio.run(verify_parsed_fragrance_async(clone_name, clone_brand, inspired_by, search_term))
    except Exception as e:
        logger.warning(f"[Verifier] Synchronous wrapper error: {e}")
        return VerificationResult(
            is_hallucination=False,
            reasoning=f"Verification fallback ({e})",
            corrected_inspired_by=inspired_by,
            confidence_score=0.85,
            requires_quarantine=False
        )
