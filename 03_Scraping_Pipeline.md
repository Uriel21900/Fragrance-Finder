import asyncio
import json
import random
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, List
from urllib.parse import urlparse
import nodriver as uc

ALLOWED_API_HOSTS = {"target.example", "catalog.partner.example"}
ALLOWED_PATH_PREFIXES = ("/v1/search", "/v1/products", "/api/")
PROXIES = [
    "http://user:pass@proxy1.example.com:8080",
    "http://user:pass@proxy2.example.com:8080",
]

@dataclass
class Job:
    source: str
    search_term: str
    correlation_id: str

class RetryableError(Exception):
    pass

def is_allowed_api_response(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.hostname in ALLOWED_API_HOSTS
        and parsed.path.startswith(ALLOWED_PATH_PREFIXES)
    )

async def publish_dlq(message: dict[str, Any]) -> None:
    # Outputs to DLQ stream / logging
    print(f"[DLQ PUBLISH] {json.dumps(message, default=str)}")

async def collect_authorized_payloads(job: Job, proxy: str) -> List[dict[str, Any]]:
    payloads: List[dict[str, Any]] = []

    # Launch nodriver (starts a clean, undetected session automatically)
    args = [f"--proxy-server={proxy}"] if proxy else []
    browser = await uc.start(browser_args=args, headless=False)
    
    # nodriver returns the default page directly
    page = await browser.get('about:blank')

    # nodriver handles CDP events directly instead of standard event listeners
    async def intercept_response(event):
        if 'Network.responseReceived' in event.method:
            url = event.params.get('response', {}).get('url', '')
            if is_allowed_api_response(url):
                request_id = event.params.get('requestId')
                try:
                    # Fetch the body using nodriver's CDP network module
                    body_response = await page.send(uc.cdp.network.get_response_body(request_id))
                    
                    # Convert body text to JSON if possible
                    try:
                        parsed_body = json.loads(body_response.body)
                    except (json.JSONDecodeError, AttributeError):
                        parsed_body = body_response.body

                    payloads.append({
                        "url": url,
                        "captured_at": datetime.now(timezone.utc).isoformat(),
                        "correlation_id": job.correlation_id,
                        "body": parsed_body,
                    })
                except Exception:
                    pass

    # Attach the handler directly to the CDP event listener
    page.add_handler(uc.cdp.network.ResponseReceived, intercept_response)

    try:
        await page.get(f"https://target.example/search?q={job.search_term}")
        # Wait for the network to settle and the JSON to be captured
        await asyncio.sleep(random.uniform(3.5, 6.5))
    finally:
        await browser.stop()

    return payloads

async def process_job(job: Job, attempts: int = 4) -> dict[str, Any]:
    for attempt in range(1, attempts + 1):
        proxy = random.choice(PROXIES) if PROXIES else None
        try:
            records = await collect_authorized_payloads(job, proxy)
            if not records:
                raise RetryableError("No target API payload captured")
            return {"status": "ok", "job": job.correlation_id, "records": records}

        except RetryableError as exc:
            if attempt == attempts:
                await publish_dlq({
                    "job": job.__dict__,
                    "failure_type": "retry_exhausted",
                    "message": str(exc),
                    "attempts": attempt,
                })
                raise

            delay = min(30, (2 ** attempt) + random.uniform(0.5, 1.5))
            await asyncio.sleep(delay)

        except Exception as exc:
            if attempt == attempts:
                await publish_dlq({
                    "job": job.__dict__,
                    "failure_type": type(exc).__name__,
                    "message": str(exc)[:500],
                    "attempts": attempt,
                })
                raise
            await asyncio.sleep(min(15, 2 ** attempt))

async def main():
    job = Job(source="fragrance_discounters", search_term="Aventus", correlation_id="job_001")
    try:
        result = await process_job(job)
        print(f"Captured {len(result['records'])} records.")
    except Exception as e:
        print(f"Job terminated: {e}")

if __name__ == "__main__":
    asyncio.run(main())