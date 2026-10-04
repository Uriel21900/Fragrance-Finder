import asyncio
import urllib.parse
from curl_cffi.requests import AsyncSession

TEST_NAMES = [
    'Creed Aventus',
    'Creed Aventus for Her',
    'Creed Aventus Cologne',
    'Dior Sauvage',
    'Dior Sauvage Elixir',
    'Dior Miss Dior',
    'Dior Fahrenheit',
    'Acqua di Gio Pour Homme',
    'Acqua di Gioia',
    'Dolce Gabbana Light Blue Pour Homme',
    'Dolce Gabbana Light Blue Women',
    'Versace Eros Pour Homme',
    'Versace Eros Pour Femme',
    'Viktor Rolf Spicebomb',
    'Viktor Rolf Flowerbomb',
    'Montblanc Explorer',
    'Paco Rabanne Invictus',
    'Paco Rabanne 1 Million',
    'Carolina Herrera Bad Boy',
    'Carolina Herrera Good Girl',
    'Lattafa Asad',
    'Lattafa Khamrah',
    'Lattafa Yara',
    'Lattafa Oud for Glory',
    'Al Haramain Amber Oud Gold Edition',
    'Afnan 9pm',
    'Maison Alhambra The Tux',
    'Maison Alhambra Woody Oud'
]

async def check():
    async with AsyncSession(impersonate='chrome') as s:
        for name in TEST_NAMES:
            enc = urllib.parse.quote_plus(name)
            # Try Fragflex
            url_ff = f'https://fragflex.com/search/suggest.json?q={enc}&resources[type]=product'
            r = await s.get(url_ff)
            ff_title, ff_img = None, None
            if r.status_code == 200:
                data = r.json()
                prods = data.get('resources', {}).get('results', {}).get('products', [])
                if prods:
                    ff_title = prods[0].get('title')
                    ff_img = prods[0].get('image')

            # Try Beautyhouse
            url_bh = f'https://beautyhouse.com/search/suggest.json?q={enc}&resources[type]=product'
            r2 = await s.get(url_bh)
            bh_title, bh_img = None, None
            if r2.status_code == 200:
                data2 = r2.json()
                prods2 = data2.get('resources', {}).get('results', {}).get('products', [])
                if prods2:
                    bh_title = prods2[0].get('title')
                    bh_img = prods2[0].get('image')

            print(f"Query: {name}")
            if ff_img:
                print(f"   FragFlex: {ff_title} -> {ff_img}")
            if bh_img:
                print(f"   BeautyHouse: {bh_title} -> {bh_img}")
            if not ff_img and not bh_img:
                print("   NO MATCH")

if __name__ == '__main__':
    asyncio.run(check())
