import asyncio
import sys
import os
import httpx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.run_scheduled_scrapers import RETAILERS, scrape_shopify_search

async def main():
    async with httpx.AsyncClient(follow_redirects=True, timeout=10.0) as client:
        for q in ['Parfums de Marly Layton', 'Versace The Dreamer', 'Creed Aventus', 'Xerjoff Naxos']:
            print(f"\n=================== Query: {q} ===================")
            for ret in RETAILERS:
                res = await scrape_shopify_search(client, ret['url'], q)
                print(f"--- {ret['name']} ({len(res)} results) ---")
                for r in res[:4]:
                    print(f"  Title: {r['title']}")
                    print(f"  Price: ${r['price']}")
                    print(f"  URL:   {r['url']}")

if __name__ == "__main__":
    asyncio.run(main())
