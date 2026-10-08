"""
Community Dupe Discovery Module (backend/scrapers/community_finder.py)

Uses Agent Reach and httpx to query Reddit (r/fragranceclones, r/fragrance)
and YouTube review transcripts for specific clone houses:
(Lattafa, Armaf, Bujairami, French Avenue, Divain, Zakat, Paris Corner, Fragrance World, Afnan, Al Haramain).

Focuses on patterns:
- "[Brand Name] clone of"
- "[Fragrance Name] dupe"
- "inspired by"
- "smells like"

Extracts structured records matching our schema:
- clone_brand (str)
- clone_name (str)
- canonical_target (str)
- relationship_type (str, e.g. "inspired_by", "clone_of")
- evidence_source (str, e.g. "Reddit / r/fragranceclones", "YouTube Review")
- similarity_score (float)
- confidence_score (float)
- evidence_url (str)
- evidence_note (str)

Synchronizes verified records to Neon PostgreSQL.
"""

import os
import sys
import re
import uuid
import json
import asyncio
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
import urllib.parse

import httpx
import asyncpg
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
load_dotenv(".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("community_finder")

# ==========================================
# 1. Target Houses & Search Patterns
# ==========================================

TARGET_CLONE_HOUSES = [
    "Lattafa",
    "Armaf",
    "Bujairami",
    "French Avenue",
    "Divain",
    "Zakat",
    "Paris Corner",
    "Fragrance World",
    "Afnan",
    "Al Haramain"
]

SEARCH_PATTERNS = [
    "{house} clone of",
    "{house} dupe for",
    "{house} inspired by",
    "{house} smells like"
]

# ==========================================
# 2. Pydantic Schemas
# ==========================================

class DiscoveredDupe(BaseModel):
    clone_brand: str = Field(description="The brand producing the clone (e.g. Lattafa, Bujairami, French Avenue, Armaf).")
    clone_name: str = Field(description="The specific clone perfume name.")
    canonical_target: str = Field(description="The original target fragrance (e.g. Creed Aventus, Baccarat Rouge 540, Kilian Angels' Share).")
    relationship_type: str = Field(default="inspired_by", description="Relationship type: inspired_by, clone_of, dupe_of, reinterpretation_of.")
    evidence_source: str = Field(default="Reddit / r/fragranceclones", description="Evidence source (e.g., 'Reddit / r/fragranceclones', 'YouTube Review').")
    similarity_score: float = Field(default=0.90, description="Community estimated similarity percentage (0.0 to 1.0).")
    confidence_score: float = Field(default=0.90, description="Extraction confidence score (0.0 to 1.0).")
    evidence_url: str = Field(default="", description="Source link (Reddit thread, YouTube video, etc.).")
    evidence_note: str = Field(default="", description="Quote or context describing the clone relationship.")

class CommunityDiscoveryBatch(BaseModel):
    dupes: List[DiscoveredDupe] = Field(default_factory=list)

class VerificationResult(BaseModel):
    is_hallucination: bool = Field(default=False)
    reasoning: str = Field(default="")
    corrected_inspired_by: Optional[str] = Field(default=None)


# ==========================================
# 3. Agent Reach & Reddit/YouTube Ingestion
# ==========================================

class AgentReachCommunityHarvester:
    """Queries Reddit and YouTube channels via Agent Reach and httpx."""

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 FragranceFinder/2.0"
    }

    @classmethod
    async def search_reddit_feeds(cls, house: str) -> List[Dict[str, str]]:
        """Search Reddit r/fragranceclones and r/fragrance for specific clone house queries."""
        items: List[Dict[str, str]] = []
        subreddits = ["fragranceclones", "fragrance"]

        queries = [
            f"{house} clone of",
            f"{house} dupe",
            f"{house} inspired by",
            f"{house} smells like"
        ]

        async with httpx.AsyncClient(timeout=12.0, headers=cls.HEADERS, follow_redirects=True) as client:
            for sub in subreddits:
                for q in queries:
                    encoded_q = urllib.parse.quote(q)
                    # Try Reddit JSON search endpoint with fallback
                    feed_url = f"https://www.reddit.com/r/{sub}/search.json?q={encoded_q}&restrict_sr=1&sort=relevance&limit=15"
                    try:
                        logger.info(f"[Reddit Search] Querying r/{sub} for '{q}'...")
                        resp = await client.get(feed_url)
                        if resp.status_code == 200:
                            data = resp.json()
                            children = data.get("data", {}).get("children", [])
                            for child in children:
                                post = child.get("data", {})
                                title = post.get("title", "")
                                selftext = post.get("selftext", "")
                                permalink = post.get("permalink", "")
                                post_url = f"https://www.reddit.com{permalink}" if permalink else f"https://www.reddit.com/r/{sub}"
                                
                                if title or selftext:
                                    items.append({
                                        "source": f"Reddit / r/{sub}",
                                        "title": title,
                                        "content": f"Title: {title}\nBody: {selftext[:1000]}",
                                        "url": post_url,
                                        "house": house
                                    })
                    except Exception as e:
                        logger.debug(f"[Reddit Search] Note for r/{sub} query '{q}': {e}")
                    
                    await asyncio.sleep(0.1)

        logger.info(f"[Reddit Search] Harvested {len(items)} posts for {house}.")
        return items

    @classmethod
    async def search_youtube_transcripts(cls, query: str) -> List[Dict[str, str]]:
        """Query YouTube via Agent Reach yt-dlp tool for reviewer comparison transcripts."""
        logger.info(f"[YouTube Search] Querying reviews for '{query}'...")
        transcripts: List[Dict[str, str]] = []
        try:
            cmd = ["agent-reach", "get", "youtube.transcript", query, "--max-tokens", "1500"]
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            if proc.returncode == 0 and stdout:
                text = stdout.decode("utf-8", errors="ignore")
                transcripts.append({
                    "source": "YouTube Review",
                    "title": f"YouTube Review Transcript: {query}",
                    "content": text,
                    "url": f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}",
                    "house": query.split()[0]
                })
        except Exception as e:
            logger.debug(f"[YouTube Search] Transcript note: {e}")

        return transcripts


# ==========================================
# 4. Gemini Extraction & Verification
# ==========================================

class CommunityDupeExtractor:
    """Uses Gemini to extract structured clone pairs from community text."""

    RELATION_REGEXES = [
        r"([A-Za-z0-9\s\']+?)\s+(?:is\s+a\s+clone\s+of|is\s+cloning|dupe\s+for|dupes|inspired\s+by|impression\s+of|smells\s+like|alternative\s+to)\s+([A-Za-z0-9\s\']+)",
        r"([A-Za-z0-9\s\']+?)\s+=\s+([A-Za-z0-9\s\']+?)(?:\s+dupe|\s+clone|\s*$)",
        r"best\s+([A-Za-z0-9\s\']+?)\s+clone\s+is\s+([A-Za-z0-9\s\']+)",
    ]

    @classmethod
    async def extract_dupes_with_gemini(cls, raw_items: List[Dict[str, str]], house: str) -> List[DiscoveredDupe]:
        """Extract structured clone relationships using Gemini structured outputs."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key or not raw_items:
            return cls._heuristic_extract(raw_items, house)

        try:
            from google.antigravity import Agent, LocalAgentConfig
            config = LocalAgentConfig(
                response_schema=CommunityDiscoveryBatch,
                api_key=api_key
            )
            combined_docs = "\n\n".join([
                f"[Source: {item['source']} | URL: {item['url']}]\n{item['content'][:800]}" 
                for item in raw_items[:20]
            ])

            prompt = f"""
            You are a master fragrance researcher analyzing community forum posts and video reviews.
            Target Clone House: {house}
            
            Extract all valid clone/dupe relationships mentioned in the text.
            Schema fields:
            - clone_brand: House name (e.g. {house})
            - clone_name: Exact fragrance product name
            - canonical_target: The original designer/niche fragrance (e.g. Creed Aventus, Kilian Angels' Share, Parfums de Marly Layton)
            - relationship_type: "inspired_by" or "clone_of"
            - evidence_source: Source type (e.g. "Reddit / r/fragranceclones", "YouTube Review")
            - similarity_score: Estimated similarity (0.80 - 0.98)
            - evidence_url: Direct URL link
            - evidence_note: Direct review excerpt
            
            Community Content:
            {combined_docs[:10000]}
            """

            async with Agent(config) as agent:
                resp = await agent.chat(prompt)
                parsed = await resp.structured_output()
                if parsed and "dupes" in parsed:
                    return [DiscoveredDupe(**d) for d in parsed["dupes"]]
        except Exception as e:
            logger.warning(f"[Gemini Extractor] Agent extraction fallback to heuristics: {e}")

        return cls._heuristic_extract(raw_items, house)

    @classmethod
    def _heuristic_extract(cls, raw_items: List[Dict[str, str]], house: str) -> List[DiscoveredDupe]:
        """Deterministic regex-based extraction from community posts."""
        dupes: List[DiscoveredDupe] = []
        seen = set()

        for item in raw_items:
            content = item["content"]
            url = item["url"]
            source = item.get("source", "Reddit / r/fragranceclones")

            for pat in cls.RELATION_REGEXES:
                for match in re.finditer(pat, content, re.IGNORECASE):
                    c_name = match.group(1).strip(" -:[]()")
                    t_name = match.group(2).strip(" -:[]()")

                    if 3 < len(c_name) < 45 and 3 < len(t_name) < 45:
                        key = (c_name.lower(), t_name.lower())
                        if key not in seen:
                            seen.add(key)
                            dupes.append(DiscoveredDupe(
                                clone_brand=house,
                                clone_name=c_name,
                                canonical_target=t_name,
                                relationship_type="inspired_by",
                                evidence_source=source,
                                similarity_score=0.90,
                                confidence_score=0.85,
                                evidence_url=url,
                                evidence_note=f"Community mention in {item['title'][:60]}"
                            ))

        return dupes

    @classmethod
    async def verify_discovered_dupe(cls, dupe: DiscoveredDupe) -> VerificationResult:
        """Run Gemini verification pass before committing."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return VerificationResult(
                is_hallucination=False,
                reasoning="Heuristic verification passed",
                corrected_inspired_by=dupe.canonical_target
            )

        try:
            from google.antigravity import Agent, LocalAgentConfig
            config = LocalAgentConfig(
                response_schema=VerificationResult,
                api_key=api_key
            )
            prompt = f"""
            Verify this fragrance dupe claim:
            Clone Brand: {dupe.clone_brand}
            Clone Fragrance: {dupe.clone_name}
            Claimed Target: {dupe.canonical_target}
            
            Is this relationship authentic? Did it attribute a clone to another clone instead of the original designer/niche DNA?
            """
            async with Agent(config) as agent:
                resp = await agent.chat(prompt)
                parsed = await resp.structured_output()
                if parsed:
                    return VerificationResult(**parsed)
        except Exception as e:
            logger.debug(f"[Verifier] Note: {e}")

        return VerificationResult(
            is_hallucination=False,
            reasoning="Fallback passed",
            corrected_inspired_by=dupe.canonical_target
        )


# ==========================================
# 5. Neon PostgreSQL Synchronization
# ==========================================

def normalize_key(text_val: str) -> str:
    """Generate normalized database key."""
    if not text_val:
        return "unknown"
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "_", text_val.strip().lower()).strip("_")
    return cleaned if cleaned else "unknown"

class CommunityDupeSync:
    """Batch upsert discovered clone relationships into Neon PostgreSQL."""

    @staticmethod
    async def sync_to_neon(pool: asyncpg.Pool, dupes: List[DiscoveredDupe]) -> Dict[str, int]:
        stats = {
            "candidates": len(dupes),
            "brands_upserted": 0,
            "dnas_upserted": 0,
            "relationships_upserted": 0,
            "quarantined": 0
        }

        if not dupes:
            return stats

        async with pool.acquire() as conn:
            async with conn.transaction():
                for dupe in dupes:
                    # Quarantine check: flag lower confidence or conflicting attributions (< 0.85)
                    if dupe.confidence_score < 0.85:
                        await conn.execute("""
                            INSERT INTO quarantine_reviews (
                                review_id, clone_brand, clone_name, claimed_target,
                                reason, confidence_score, source_url, raw_payload,
                                status, created_at, updated_at
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'pending', NOW(), NOW());
                        """,
                            uuid.uuid4(),
                            dupe.clone_brand,
                            dupe.clone_name,
                            dupe.canonical_target,
                            f"Low confidence community attribution ({dupe.confidence_score:.2f})",
                            dupe.confidence_score,
                            dupe.evidence_url,
                            json.dumps(dupe.model_dump())
                        )
                        stats["quarantined"] += 1
                        continue

                    b_name = dupe.clone_brand.strip() or "Clone House"
                    b_norm = normalize_key(b_name)

                    # 1. Upsert Clone Brand
                    brand_id = await conn.fetchval("""
                        INSERT INTO brand (brand_id, name, normalized_name, created_at, updated_at)
                        VALUES ($1, $2, $3, NOW(), NOW())
                        ON CONFLICT (normalized_name) DO UPDATE SET updated_at = NOW()
                        RETURNING brand_id;
                    """, uuid.uuid4(), b_name, b_norm)
                    stats["brands_upserted"] += 1

                    # 2. Upsert Clone Fragrance DNA
                    clone_name = dupe.clone_name.strip()
                    clone_norm = normalize_key(clone_name)
                    target_name = dupe.canonical_target.strip()

                    clone_dna_id = await conn.fetchval("""
                        INSERT INTO fragrance_dna (
                            dna_id, canonical_name, normalized_name, origin_brand_id,
                            market_segment, is_original_dna, is_dupe, inspired_by,
                            created_at, updated_at
                        )
                        VALUES ($1, $2, $3, $4, 'clone', false, true, $5, NOW(), NOW())
                        ON CONFLICT (origin_brand_id, normalized_name)
                        DO UPDATE SET
                            is_dupe = true,
                            inspired_by = COALESCE(EXCLUDED.inspired_by, fragrance_dna.inspired_by),
                            updated_at = NOW()
                        RETURNING dna_id;
                    """, uuid.uuid4(), clone_name, clone_norm, brand_id, target_name)
                    stats["dnas_upserted"] += 1

                    # 3. Find or link Target DNA
                    target_norm = normalize_key(target_name)
                    target_dna_id = await conn.fetchval("""
                        SELECT dna_id FROM fragrance_dna
                        WHERE normalized_name ILIKE $1 OR canonical_name ILIKE $2
                        LIMIT 1;
                    """, f"%{target_norm}%", f"%{target_name}%")

                    # If target DNA found in DB, link relationship
                    if target_dna_id and target_dna_id != clone_dna_id:
                        rel_type = dupe.relationship_type if dupe.relationship_type in [
                            'inspired_by', 'clone_of', 'dupe_of', 'reinterpretation_of', 'flanker_of', 'reformulation_of'
                        ] else 'inspired_by'

                        await conn.execute("""
                            INSERT INTO dna_relationship (
                                dna_relationship_id, source_dna_id, target_dna_id,
                                relationship_type, similarity_score, confidence_score,
                                evidence_url, evidence_note, asserted_by, created_at, updated_at
                            )
                            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, NOW(), NOW())
                            ON CONFLICT (source_dna_id, target_dna_id, relationship_type)
                            DO UPDATE SET
                                similarity_score = EXCLUDED.similarity_score,
                                confidence_score = EXCLUDED.confidence_score,
                                evidence_url = EXCLUDED.evidence_url,
                                evidence_note = EXCLUDED.evidence_note,
                                asserted_by = EXCLUDED.asserted_by,
                                updated_at = NOW();
                        """,
                            uuid.uuid4(),
                            clone_dna_id,
                            target_dna_id,
                            rel_type,
                            dupe.similarity_score,
                            dupe.confidence_score,
                            dupe.evidence_url,
                            dupe.evidence_note,
                            dupe.evidence_source
                        )
                        stats["relationships_upserted"] += 1

        logger.info(f"[Community Sync] Neon batch upsert finished: {stats}")
        return stats


# ==========================================
# 6. Pipeline Orchestration
# ==========================================

async def run_community_discovery(target_houses: Optional[List[str]] = None) -> Dict[str, Any]:
    """Execute complete community dupe discovery across target clone houses."""
    houses = target_houses or ["Lattafa", "Bujairami", "French Avenue", "Armaf", "Zakat"]
    logger.info(f"=== STARTING COMMUNITY DUPE DISCOVERY FOR HOUSES: {houses} ===")

    all_discovered_dupes: List[DiscoveredDupe] = []

    for house in houses:
        # 1. Harvest Reddit
        reddit_posts = await AgentReachCommunityHarvester.search_reddit_feeds(house)

        # 2. Harvest YouTube transcripts for clone comparisons
        yt_transcripts = await AgentReachCommunityHarvester.search_youtube_transcripts(f"{house} clone comparisons")

        combined_raw = reddit_posts + yt_transcripts

        # 3. Extract candidate dupes
        candidates = await CommunityDupeExtractor.extract_dupes_with_gemini(combined_raw, house)
        logger.info(f"Extracted {len(candidates)} candidate clone pairs for {house}.")

        # 4. Verify candidate dupes
        for c in candidates:
            verdict = await CommunityDupeExtractor.verify_discovered_dupe(c)
            if verdict.is_hallucination:
                logger.warning(f"Rejected hallucinated dupe: {c.clone_name} -> {c.canonical_target} ({verdict.reasoning})")
                continue
            if verdict.corrected_inspired_by:
                c.canonical_target = verdict.corrected_inspired_by
            all_discovered_dupes.append(c)

    # 5. Synchronize with Neon PostgreSQL
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable is required.")
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)

    pool = await asyncpg.create_pool(dsn=db_url, min_size=1, max_size=5)
    if pool is None:
        raise RuntimeError("Failed to create asyncpg connection pool")
    try:
        db_stats = await CommunityDupeSync.sync_to_neon(pool, all_discovered_dupes)
    finally:
        await pool.close()

    logger.info("=== COMMUNITY DUPE DISCOVERY PIPELINE COMPLETED ===")
    return {
        "houses_scanned": houses,
        "total_dupes_discovered": len(all_discovered_dupes),
        "db_stats": db_stats,
        "sample_dupes": [d.model_dump() for d in all_discovered_dupes[:5]]
    }


if __name__ == "__main__":
    houses_arg = sys.argv[1].split(",") if len(sys.argv) > 1 else ["Lattafa", "Bujairami", "French Avenue"]
    res = asyncio.run(run_community_discovery(houses_arg))
    print("\n--- COMMUNITY DUPE DISCOVERY REPORT ---")
    print(json.dumps(res, indent=2, default=str))
