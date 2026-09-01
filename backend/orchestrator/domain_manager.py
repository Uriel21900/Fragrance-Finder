"""
Domain Manager & Anti-Bot Detection (backend/orchestrator/domain_manager.py)
Detects anti-bot blocks, pauses only the affected domain worker, issues alerts,
and allows Shopify endpoints and unaffected domains to proceed seamlessly.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger("DomainManager")

class DomainType(str, Enum):
    SHOPIFY = "shopify"
    CUSTOM = "custom"
    PROTECTED = "protected"

class DomainStatus(str, Enum):
    READY = "READY"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PAUSED_ANTIBOT = "PAUSED_ANTIBOT"
    FAILED = "FAILED"

@dataclass
class DomainConfig:
    name: str
    url: str
    domain_type: DomainType
    rate_limit_rps: float = 2.0
    max_retries: int = 3

@dataclass
class DomainState:
    config: DomainConfig
    status: DomainStatus = DomainStatus.READY
    scraped_count: int = 0
    inserted_count: int = 0
    error_count: int = 0
    antibot_detected: bool = False
    pause_reason: Optional[str] = None
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

class AntiBotDetector:
    CHALLENGE_SIGNATURES = [
        "cf-chl-bypass",
        "cloudflare ray id",
        "attention required! | cloudflare",
        "access denied | datadome",
        "perimeterx",
        "pnd.js",
        "captcha-delivery.com",
        "please verify you are a human",
        "enable javascript and cookies to continue",
        "just a moment...",
        "security check to continue",
    ]

    @classmethod
    def check_response(cls, status_code: int, headers: dict, body_text: str) -> Optional[str]:
        headers_lower = {k.lower(): v.lower() for k, v in headers.items()}
        body_lower = body_text.lower() if body_text else ""

        # 1. Status Code Check
        if status_code in (403, 429, 503):
            for sig in cls.CHALLENGE_SIGNATURES:
                if sig in body_lower:
                    return f"HTTP {status_code} with bot signature: '{sig}'"
            if status_code == 403:
                return "HTTP 403 Access Forbidden / WAF Block"
            elif status_code == 429:
                return "HTTP 429 Rate Limited"

        # 2. Header and Captcha Challenges
        if "cf-mitigated" in headers_lower or "x-datadome" in headers_lower or "x-px" in headers_lower:
            return "WAF Mitigation / DataDome / PerimeterX header detected"

        # 3. Page body challenge check
        for sig in cls.CHALLENGE_SIGNATURES:
            if sig in body_lower:
                return f"Bot challenge block detected in page body: '{sig}'"

        return None


class DomainOrchestrator:
    def __init__(self, domain_configs: List[DomainConfig], log_streamer):
        self.domains: Dict[str, DomainState] = {
            d.name: DomainState(config=d) for d in domain_configs
        }
        self.log_streamer = log_streamer
        self.run_id: Optional[str] = None

    def get_summary_state(self):
        active = sum(1 for s in self.domains.values() if s.status == DomainStatus.RUNNING)
        paused = sum(1 for s in self.domains.values() if s.status == DomainStatus.PAUSED_ANTIBOT)
        return {
            "status": "RUNNING" if active > 0 else "IDLE",
            "active_count": active,
            "paused_count": paused,
        }

    async def trigger_antibot_pause(self, domain_name: str, reason: str, run_id: str):
        state = self.domains[domain_name]
        state.status = DomainStatus.PAUSED_ANTIBOT
        state.antibot_detected = True
        state.pause_reason = reason
        state.ended_at = datetime.now(timezone.utc)

        msg = (
            f"🚨 ANTI-BOT ALERT: Worker for [{domain_name}] ({state.config.domain_type.value}) "
            f"has been PAUSED. Reason: {reason}. All other domain workers (including Shopify) continue executing."
        )
        logger.error(msg)
        
        await self.log_streamer.log(
            run_id=run_id,
            domain=domain_name,
            level="CRITICAL",
            message=msg,
            context={"antibot_detected": True, "reason": reason, "domain_type": state.config.domain_type.value}
        )

    def is_paused(self, domain_name: str) -> bool:
        return self.domains[domain_name].status == DomainStatus.PAUSED_ANTIBOT
