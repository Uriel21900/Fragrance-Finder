import asyncio
import urllib.parse
import re
from curl_cffi.requests import AsyncSession

RETAILERS = [
    ('FragFlex', 'https://fragflex.com'),
    ('Labelle Perfumes', 'https://labelleperfumes.com'),
    ('Best Brands Perfume', 'https://bestbrandsperfume.com'),
    ('ReblScents', 'https://reblscents.com'),
    ('Aura Fragrance', 'https://aurafragrance.com'),
    ('Banadir Fragrance', 'https://banadirfragrance.com'),
    ('Triple Traders', 'https://tripletraders.com'),
    ('PerfumeOnline.com', 'https://perfumeonline.com'),
    ('Shop Aromatix', 'https://shoparomatix.com'),
    ('Aroma Concepts', 'https://aromaconcepts.com'),
    ('Anau Store', 'https://anaustore.com'),
    ('LR LUX', 'https://lrlux.com'),
    ('BeautyHouse', 'https://beautyhouse.com'),
]

async def test_all():
    query = 'Giorgio Armani Acqua di Gio'
    clean = re.sub(r'[^a-zA-Z0-9\s]', ' ', query)
    clean = re.sub(r'\s+', ' ', clean).strip()
    encoded = urllib.parse.quote_plus(clean)
    async with AsyncSession(impersonate='chrome', timeout=10.0) as client:
        for name, url in RETAILERS:
            try:
                s_url = f'{url}/search/suggest.json?q={encoded}&resources[type]=product&resources[options][unavailable_products]=hide'
                r = await client.get(s_url)
                if r.status_code == 200:
                    data = r.json()
                    prods = data.get('resources', {}).get('results', {}).get('products', [])
                    print(f'{name}: 200 OK - {len(prods)} products found')
                    for p in prods[:1]:
                        print(f'   -> {p.get("title")} | ${p.get("price")}')
                else:
                    print(f'{name}: HTTP {r.status_code}')
            except Exception as e:
                print(f'{name}: ERROR {e}')
            await asyncio.sleep(0.2)

if __name__ == '__main__':
    asyncio.run(test_all())
