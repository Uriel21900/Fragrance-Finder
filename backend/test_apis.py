import asyncio
import httpx

async def test_apis():
    async with httpx.AsyncClient(base_url='http://localhost:8000') as client:
        # Test Trending
        print('--- Testing /api/trending ---')
        r1 = await client.get('/api/trending')
        print(f'Status 1: {r1.status_code}, Results: {len(r1.json())}')
        r2 = await client.get('/api/trending')
        print(f'Status 2: {r2.status_code}, Results: {len(r2.json())}')
        
        # Test Search with typo
        print('\n--- Testing /api/search with fuzzy typo: \'Avntus\' ---')
        r3 = await client.get('/api/search?q=Avntus')
        print(f'Status: {r3.status_code}')
        for res in r3.json():
            print(f"Found: {res['canonical_name']} by {res['brand_name']}")
            
asyncio.run(test_apis())
