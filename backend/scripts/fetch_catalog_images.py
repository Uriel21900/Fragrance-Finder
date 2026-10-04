import asyncio
import sys
import urllib.parse
from curl_cffi.requests import AsyncSession

sys.stdout.reconfigure(encoding='utf-8')

# Target fragrances needing genuine pictures and gender verification
TARGETS = [
    # Canonical & top designer/niche
    ('Acqua di Gio', 'Giorgio Armani', 'masculine'),
    ('Acqua di Gioia', 'Giorgio Armani', 'feminine'),
    ('Acqua Di Gio Profondo', 'Giorgio Armani', 'masculine'),
    ('Acqua Di Gio Parfum', 'Giorgio Armani', 'masculine'),
    ('Light Blue', 'Dolce & Gabbana', 'feminine'),
    ('Light Blue pour Homme', 'Dolce & Gabbana', 'masculine'),
    ('Bleu de Chanel', 'Chanel', 'masculine'),
    ('Sauvage', 'Dior', 'masculine'),
    ('Sauvage Elixir', 'Dior', 'masculine'),
    ('Miss Dior', 'Dior', 'feminine'),
    ('J\'adore', 'Dior', 'feminine'),
    ('Hypnotic Poison', 'Dior', 'feminine'),
    ('Fahrenheit', 'Dior', 'masculine'),
    ('Dior Homme Intense', 'Dior', 'masculine'),
    ('Coco Mademoiselle', 'Chanel', 'feminine'),
    ('Chance Eau Tendre', 'Chanel', 'feminine'),
    ('Allure Homme Sport', 'Chanel', 'masculine'),
    ('Sycomore', 'Chanel', 'unisex'),
    ('Eros', 'Versace', 'masculine'),
    ('Eros Flame', 'Versace', 'masculine'),
    ('Eros Pour Femme', 'Versace', 'feminine'),
    ('Bright Crystal', 'Versace', 'feminine'),
    ('Crystal Noir', 'Versace', 'feminine'),
    ('Dylan Blue Pour Homme', 'Versace', 'masculine'),
    ('Dylan Blue Pour Femme', 'Versace', 'feminine'),
    ('Spicebomb', 'Viktor & Rolf', 'masculine'),
    ('Spicebomb Extreme', 'Viktor & Rolf', 'masculine'),
    ('Flowerbomb', 'Viktor & Rolf', 'feminine'),
    ('Daisy', 'Marc Jacobs', 'feminine'),
    ('Chloé Eau de Parfum', 'Chloé', 'feminine'),
    ('Delina', 'Parfums de Marly', 'feminine'),
    ('Delina Exclusif', 'Parfums de Marly', 'feminine'),
    ('Layton', 'Parfums de Marly', 'masculine'),
    ('Herod', 'Parfums de Marly', 'masculine'),
    ('Pegasus', 'Parfums de Marly', 'masculine'),
    ('Greenley', 'Parfums de Marly', 'masculine'),
    ('Percival', 'Parfums de Marly', 'masculine'),
    ('Haltane', 'Parfums de Marly', 'masculine'),
    ('Althair', 'Parfums de Marly', 'masculine'),
    ('Oriana', 'Parfums de Marly', 'feminine'),
    ('Valaya', 'Parfums de Marly', 'feminine'),
    ('Carnal Flower', 'Frederic Malle', 'feminine'),
    ('Portrait of a Lady', 'Frederic Malle', 'feminine'),
    ('Musc Ravageur', 'Frederic Malle', 'unisex'),
    ('Blackberry & Bay', 'Jo Malone', 'unisex'),
    ('Wood Sage & Sea Salt', 'Jo Malone', 'unisex'),
    ('English Pear & Freesia', 'Jo Malone', 'feminine'),
    ('Peony & Blush Suede', 'Jo Malone', 'feminine'),
    ('Lost Cherry', 'Tom Ford', 'unisex'),
    ('Tobacco Vanille', 'Tom Ford', 'unisex'),
    ('Oud Wood', 'Tom Ford', 'unisex'),
    ('Bitter Peach', 'Tom Ford', 'unisex'),
    ('Neroli Portofino', 'Tom Ford', 'unisex'),
    ('Black Orchid', 'Tom Ford', 'unisex'),
    ('Noir Extreme', 'Tom Ford', 'masculine'),
    ('Grey Vetiver', 'Tom Ford', 'masculine'),
    ('Shalimar', 'Guerlain', 'feminine'),
    ('Mon Guerlain', 'Guerlain', 'feminine'),
    ('L\'Homme Ideal', 'Guerlain', 'masculine'),
    ('Opium', 'Yves Saint Laurent', 'feminine'),
    ('Black Opium', 'Yves Saint Laurent', 'feminine'),
    ('Libre', 'Yves Saint Laurent', 'feminine'),
    ('Y Eau de Parfum', 'Yves Saint Laurent', 'masculine'),
    ('La Nuit de L\'Homme', 'Yves Saint Laurent', 'masculine'),
    ('Angels\' Share', 'Kilian', 'unisex'),
    ('Apple Brandy on the Rocks', 'Kilian', 'unisex'),
    ('Love Don\'t Be Shy', 'Kilian', 'feminine'),
    ('Grand Soir', 'Maison Francis Kurkdjian', 'unisex'),
    ('Baccarat Rouge 540', 'Maison Francis Kurkdjian', 'unisex'),
    ('Gentle Fluidity Silver', 'Maison Francis Kurkdjian', 'masculine'),
    ('Gentle Fluidity Gold', 'Maison Francis Kurkdjian', 'feminine'),
    ('Alien', 'Mugler', 'feminine'),
    ('Angel', 'Mugler', 'feminine'),
    ('A*Men', 'Mugler', 'masculine'),
    ('Ambre Narguilé', 'Hermès', 'unisex'),
    ('Terre d\'Hermès', 'Hermès', 'masculine'),
    ('H24', 'Hermès', 'masculine'),
    ('Twilly d\'Hermès', 'Hermès', 'feminine'),
    ('L\'Interdit', 'Givenchy', 'feminine'),
    ('Gentleman Givenchy', 'Givenchy', 'masculine'),
    ('Santal 33', 'Le Labo', 'unisex'),
    ('The Noir 29', 'Le Labo', 'unisex'),
    ('Another 13', 'Le Labo', 'unisex'),
    ('Encre Noire', 'Lalique', 'masculine'),
    ('Wonderwood', 'Comme des Garçons', 'masculine'),
    ('Tam Dao', 'Diptyque', 'unisex'),
    ('Philosykos', 'Diptyque', 'unisex'),
    ('Bleecker Street', 'Bond No. 9', 'unisex'),
    ('The Scent of Peace for Him', 'Bond No. 9', 'masculine'),
    ('The Scent of Peace for Her', 'Bond No. 9', 'feminine'),
    ('La Vie Est Belle', 'Lancôme', 'feminine'),
    ('Idôle', 'Lancôme', 'feminine'),
    ('By the Fireplace', 'Maison Margiela Replica', 'unisex'),
    ('Jazz Club', 'Maison Margiela Replica', 'masculine'),
    ('Chocolate Greedy', 'Montale', 'unisex'),
    ('Intense Cafe', 'Montale', 'unisex'),
    ('Arabians Tonka', 'Montale', 'unisex'),
    ('Whiff of Waffle Cone', 'Imaginary Authors', 'unisex'),
    ('Lira', 'Xerjoff', 'feminine'),
    ('Naxos', 'Xerjoff', 'unisex'),
    ('Erba Pura', 'Xerjoff', 'unisex'),
    ('Cheirosa 62', 'Sol de Janeiro', 'feminine'),
    ('Cheirosa 68', 'Sol de Janeiro', 'feminine'),
    ('Cheirosa 71', 'Sol de Janeiro', 'feminine'),
    ('Cheirosa 59', 'Sol de Janeiro', 'feminine'),
    ('CK One', 'Calvin Klein', 'unisex'),
    ('CK Be', 'Calvin Klein', 'unisex'),
    ('Eternity for Men', 'Calvin Klein', 'masculine'),
    ('Eternity for Women', 'Calvin Klein', 'feminine'),
    ('Artisan Pure', 'John Varvatos', 'masculine'),
    ('Aventus', 'Creed', 'masculine'),
    ('Aventus for Her', 'Creed', 'feminine'),
    ('Aventus Cologne', 'Creed', 'masculine'),
    ('Absolu Aventus', 'Creed', 'masculine'),
    ('Green Irish Tweed', 'Creed', 'masculine'),
    ('Silver Mountain Water', 'Creed', 'unisex'),
    ('Millesime Imperial', 'Creed', 'unisex'),
    ('Virgin Island Water', 'Creed', 'unisex'),
    ('Viking', 'Creed', 'masculine'),
    ('Royal Oud', 'Creed', 'masculine'),
    ('Original Santal', 'Creed', 'unisex'),
    ('Love in White', 'Creed', 'feminine'),
    ('Wind Flowers', 'Creed', 'feminine'),
    ('Carmina', 'Creed', 'feminine'),
    ('Invictus', 'Paco Rabanne', 'masculine'),
    ('1 Million', 'Paco Rabanne', 'masculine'),
    ('Lady Million', 'Paco Rabanne', 'feminine'),
    ('Olympea', 'Paco Rabanne', 'feminine'),
    ('Phantom', 'Paco Rabanne', 'masculine'),
    ('Bad Boy', 'Carolina Herrera', 'masculine'),
    ('Good Girl', 'Carolina Herrera', 'feminine'),
    ('Le Male', 'Jean Paul Gaultier', 'masculine'),
    ('Le Male Le Parfum', 'Jean Paul Gaultier', 'masculine'),
    ('Le Male Elixir', 'Jean Paul Gaultier', 'masculine'),
    ('Ultra Male', 'Jean Paul Gaultier', 'masculine'),
    ('Classique', 'Jean Paul Gaultier', 'feminine'),
    ('La Belle', 'Jean Paul Gaultier', 'feminine'),
    ('Scandal', 'Jean Paul Gaultier', 'feminine'),
    ('Explorer', 'Montblanc', 'masculine'),
    ('Legend', 'Montblanc', 'masculine'),
    ('The Most Wanted', 'Azzaro', 'masculine'),
    ('Wanted by Night', 'Azzaro', 'masculine'),
    ('Wanted Girl', 'Azzaro', 'feminine'),
    ('Uomo Born In Roma', 'Valentino', 'masculine'),
    ('Donna Born In Roma', 'Valentino', 'feminine'),
    ('Luna Rossa Carbon', 'Prada', 'masculine'),
    ('Luna Rossa Ocean', 'Prada', 'masculine'),
    ('Luna Rossa Black', 'Prada', 'masculine'),
    ('Paradoxe', 'Prada', 'feminine'),
    ('Khamrah', 'Lattafa', 'unisex'),
    ('Asad', 'Lattafa', 'masculine'),
    ('Yara', 'Lattafa', 'feminine'),
    ('Yara Tous', 'Lattafa', 'feminine'),
    ('Oud for Glory (Bade\'e Al Oud)', 'Lattafa', 'unisex'),
    ('Honor & Glory', 'Lattafa', 'unisex'),
    ('Fakhar Black', 'Lattafa', 'masculine'),
    ('Fakhar Rose', 'Lattafa', 'feminine'),
    ('Nebras', 'Lattafa', 'unisex'),
    ('9pm', 'Afnan', 'masculine'),
    ('9am Dive', 'Afnan', 'unisex'),
    ('Turathi Blue', 'Afnan', 'masculine'),
    ('Supremacy Not Only Intense', 'Afnan', 'masculine'),
    ('Supremacy in Oud', 'Afnan', 'unisex'),
    ('Club De Nuit Intense Man', 'Armaf', 'masculine'),
    ('Club De Nuit Intense Woman', 'Armaf', 'feminine'),
    ('Club De Nuit Milestone', 'Armaf', 'unisex'),
    ('Club De Nuit Sillage', 'Armaf', 'unisex'),
    ('Club De Nuit Untold', 'Armaf', 'unisex'),
    ('Club De Nuit Iconic', 'Armaf', 'masculine'),
    ('Amber Oud Gold Edition', 'Al Haramain', 'unisex'),
    ('Amber Oud Tobacco Edition', 'Al Haramain', 'unisex'),
    ('Amber Oud Rouge', 'Al Haramain', 'unisex'),
    ('L\'Aventure', 'Al Haramain', 'masculine'),
    ('Detour Noir', 'Al Haramain', 'masculine'),
    ('The Tux', 'Maison Alhambra', 'masculine'),
    ('Woody Oud', 'Maison Alhambra', 'unisex'),
    ('Tobacco Touch', 'Maison Alhambra', 'unisex'),
    ('Amber & Leather', 'Maison Alhambra', 'masculine'),
    ('Bright Peach', 'Maison Alhambra', 'unisex'),
    ('Porto Neroli', 'Maison Alhambra', 'unisex'),
    ('Kismet Angel', 'Maison Alhambra', 'unisex'),
    ('Salvo', 'Maison Alhambra', 'masculine'),
]

async def search_stores(targets):
    results = {}
    async with AsyncSession(impersonate='chrome') as s:
        for name, brand, gender in targets:
            # Query variations
            queries = [
                f"{brand} {name}",
                f"{name} {brand}",
                f"{brand} {name} For Men" if gender == 'masculine' else (f"{brand} {name} For Women" if gender == 'feminine' else f"{brand} {name}"),
                name
            ]
            found_img = None
            found_title = None
            
            for q in queries:
                enc = urllib.parse.quote_plus(q)
                # Fragflex
                try:
                    url = f'https://fragflex.com/search/suggest.json?q={enc}&resources[type]=product'
                    r = await s.get(url, timeout=5)
                    if r.status_code == 200:
                        prods = r.json().get('resources', {}).get('results', {}).get('products', [])
                        for p in prods:
                            title = p.get('title', '')
                            img = p.get('image')
                            if not img or 'no-image' in img:
                                continue
                            # Verify gender matching in title if possible
                            t_lower = title.lower()
                            if gender == 'masculine' and ('woman' in t_lower or 'pour femme' in t_lower or 'for her' in t_lower):
                                continue
                            if gender == 'feminine' and (('for man' in t_lower or 'pour homme' in t_lower or 'for him' in t_lower) and 'woman' not in t_lower and 'pour femme' not in t_lower):
                                continue
                            # Found match!
                            found_img = img
                            found_title = title
                            break
                    if found_img:
                        break
                except Exception:
                    pass

                # Beautyhouse
                if not found_img:
                    try:
                        url2 = f'https://beautyhouse.com/search/suggest.json?q={enc}&resources[type]=product'
                        r2 = await s.get(url2, timeout=5)
                        if r2.status_code == 200:
                            prods2 = r2.json().get('resources', {}).get('results', {}).get('products', [])
                            for p in prods2:
                                title = p.get('title', '')
                                img = p.get('image')
                                if not img or 'no-image' in img:
                                    continue
                                t_lower = title.lower()
                                if gender == 'masculine' and ('women' in t_lower or 'for her' in t_lower):
                                    continue
                                if gender == 'feminine' and ('for men' in t_lower and 'women' not in t_lower):
                                    continue
                                found_img = img
                                found_title = title
                                break
                    except Exception:
                        pass
                if found_img:
                    break

            results[(name, brand)] = {
                'gender': gender,
                'found_title': found_title,
                'image_url': found_img
            }
            status = f"✓ {found_title[:35]}" if found_img else "✗ NOT FOUND"
            print(f"[{gender.upper()[:3]}] {brand} - {name}: {status}")

    return results

if __name__ == '__main__':
    asyncio.run(search_stores(TARGETS))
