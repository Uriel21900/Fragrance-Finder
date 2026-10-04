import asyncio
import urllib.parse
from curl_cffi.requests import AsyncSession

TEST_NAMES = [
    'Creed Aventus for Her',
    'Giorgio Armani Acqua di Gio',
    'Dolce & Gabbana Light Blue',
    'Dior J adore',
    'Dior Miss Dior',
    'Viktor Rolf Flowerbomb',
    'Marc Jacobs Daisy',
    'Versace Bright Crystal',
    'Yves Saint Laurent Black Opium',
    'Mugler Alien',
    'Tom Ford Black Orchid',
    'Calvin Klein CK One',
    'Hermes Terre d Hermes',
    'Guerlain Shalimar'
]

async def check():
    async with AsyncSession(impersonate='chrome') as s:
        for name in TEST_NAMES:
            enc = urllib.parse.quote_plus(name)
            url = f'https://fragflex.com/search/suggest.json?q={enc}&resources[type]=product'
            r = await s.get(url)
            if r.status_code == 200:
                data = r.json()
                prods = data.get('resources', {}).get('results', {}).get('products', [])
                if prods:
                    p = prods[0]
                    t = p.get('title')
                    img = p.get('image')
                    print(f"{name} -> {t} | Img: {img}")
                else:
                    print(f"{name} -> 0 results on FragFlex")
            else:
                print(f"{name} -> HTTP {r.status_code}")

if __name__ == '__main__':
    asyncio.run(check())
