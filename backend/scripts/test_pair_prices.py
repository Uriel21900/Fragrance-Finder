import asyncio
from curl_cffi.requests import AsyncSession

NAMES = [
    'Dolce & Gabbana Light Blue For Man',
    'Dolce & Gabbana Light Blue For Woman',
    'Giorgio Armani Acqua Di Gio For Man',
    'Giorgio Armani Acqua Di Gioia For Woman',
    'Versace Eros For Man',
    'Versace Eros Femme For Woman',
    'Viktor Rolf Spicebomb Extreme For Man',
    'Viktor Rolf Flowerbomb Extreme Intense For Woman',
    'Carolina Herrera CH Bad Boy',
    'Carolina Herrera Good Girl For Woman',
    'Rabanne 1 Million For Man',
    'Jean Paul Gaultier Le Male',
    'Jean Paul Gaultier La Belle'
]

async def main():
    async with AsyncSession(impersonate='chrome') as s:
        for n in NAMES:
            r = await s.get(f'https://fragflex.com/search/suggest.json?q={n}&resources[type]=product')
            if r.status_code == 200:
                prods = r.json().get('resources', {}).get('results', {}).get('products', [])
                if prods:
                    p = prods[0]
                    title = p.get('title')
                    price = p.get('price')
                    img = p.get('image')
                    print(f"{n} -> {title} | ${price} | {img}")

if __name__ == '__main__':
    asyncio.run(main())
