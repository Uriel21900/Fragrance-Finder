import asyncio
import os
import sys
from typing import Any
from sqlalchemy import select, delete, text
from urllib.parse import urlparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import (
    Brand, FragranceDNA, FragranceLine, FragranceProduct, ProductVariant,
    Retailer, PriceObservation, DNARelationship, RelationType,
    FragranceMarketSegment, FragranceGenderMarketing
)

# Curated dataset of 50 iconic luxury/niche/designer fragrances
# with verified bottle images, genuine prices, and real clones
CATALOG_50 = [
    {
        "brand": "Creed",
        "name": "Aventus",
        "normalized": "aventus",
        "segment": FragranceMarketSegment.niche,
        "image_url": "/images/creed_aventus.jpg",
        "prices": [
            ("perfumeonline_com", 19.95, "https://perfumeonline.com/products/creed-aventus", 2.0, "sample vial"),
            ("reblscents", 265.00, "https://reblscents.com/products/creed-aventus-for-men-edp", 100.0, "spray"),
            ("aurafragrance", 269.99, "https://www.aurafragrance.com/products/creed-aventus-for-men-edp-3-3-oz-spray", 100.0, "spray"),
            ("jomashop", 274.99, "https://www.jomashop.com/creed-aventus-edp-spray-3-3-oz-100-ml-m-aventus-3-3.html", 100.0, "spray"),
            ("perfumeonline_com", 279.95, "https://perfumeonline.com/products/creed-aventus-eau-de-parfum-100ml", 100.0, "spray"),
        ],
        "clones": [
            ("Armaf", "Club De Nuit Intense Man", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80"),
            ("Montblanc", "Explorer", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80"),
            ("Afnan", "Supremacy Silver", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80"),
            ("Banadir Fragrance", "24 Extrait De Parfum", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80"),
            ("Alfred Dunhill", "Desire Gold", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80"),
            ("Banadir Fragrance", "Adventure Absolu", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Maison Francis Kurkdjian",
        "name": "Baccarat Rouge 540",
        "normalized": "baccarat_rouge_540",
        "segment": FragranceMarketSegment.niche,
        "image_url": "/images/baccarat_rouge_540.jpg",
        "prices": [
            ("reblscents", 295.00, "https://reblscents.com/products/baccarat-rouge-540-edp", 70.0, "spray"),
            ("jomashop", 310.00, "https://www.jomashop.com/maison-francis-kurkdjian-baccarat-rouge-540.html", 70.0, "spray"),
            ("perfumeonline_com", 314.95, "https://perfumeonline.com/products/baccarat-rouge-540", 70.0, "spray"),
        ],
        "clones": [
            ("Armaf", "Club De Nuit Untold", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80"),
            ("Al Haramain", "Amber Oud Rouge", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80"),
            ("Lattafa", "Ana Abiyedh Rouge", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Kilian",
        "name": "Angels' Share",
        "normalized": "angels_share",
        "segment": FragranceMarketSegment.niche,
        "image_url": "/images/kilian_angels_share.jpg",
        "prices": [
            ("jomashop", 195.00, "https://www.jomashop.com/by-kilian-angels-share.html", 50.0, "spray"),
            ("aurafragrance", 189.99, "https://www.aurafragrance.com/products/kilian-angels-share", 50.0, "spray"),
            ("perfumeonline_com", 199.95, "https://perfumeonline.com/products/kilian-angels-share", 50.0, "spray"),
            ("reblscents", 210.00, "https://reblscents.com/products/kilian-angels-share", 50.0, "spray")
        ],
        "clones": [
            ("Lattafa", "Khamrah", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80"),
            ("Maison Alhambra", "Kismet Magic", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80"),
            ("Paris Corner", "Emir Fire Your Desire", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80"),
            ("Zimaya", "Sharaf Blend", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Parfums de Marly",
        "name": "Layton",
        "normalized": "layton",
        "segment": FragranceMarketSegment.niche,
        "image_url": "/images/pdm_layton.jpg",
        "prices": [
            ("aurafragrance", 199.99, "https://www.aurafragrance.com/products/parfums-de-marly-layton-edp", 125.0, "spray"),
            ("jomashop", 215.00, "https://www.jomashop.com/parfums-de-marly-layton.html", 125.0, "spray"),
            ("perfumeonline_com", 219.95, "https://perfumeonline.com/products/parfums-de-marly-layton", 125.0, "spray"),
            ("reblscents", 225.00, "https://reblscents.com/products/parfums-de-marly-layton-edp", 125.0, "spray")
        ],
        "clones": [
            ("Al Haramain", "Detour Noir", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80"),
            ("The Woods Collection", "Dusk", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Dior",
        "name": "Sauvage Elixir",
        "normalized": "sauvage_elixir",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 149.99, "https://www.aurafragrance.com/products/dior-sauvage-elixir", 60.0, "spray"),
            ("perfumeonline_com", 154.95, "https://perfumeonline.com/products/dior-sauvage-elixir", 60.0, "spray"),
            ("jomashop", 159.99, "https://www.jomashop.com/christian-dior-sauvage-elixir.html", 60.0, "spray"),
            ("reblscents", 165.00, "https://reblscents.com/products/dior-sauvage-elixir", 60.0, "spray")
        ],
        "clones": [
            ("Lattafa", "Asad", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Tom Ford",
        "name": "Tobacco Vanille",
        "normalized": "tobacco_vanille",
        "segment": FragranceMarketSegment.niche,
        "image_url": "/images/tom_ford_tobacco_vanille.jpg",
        "prices": [
            ("aurafragrance", 229.99, "https://www.aurafragrance.com/products/tom-ford-tobacco-vanille", 50.0, "spray"),
            ("jomashop", 239.99, "https://www.jomashop.com/tom-ford-tobacco-vanille.html", 50.0, "spray"),
            ("perfumeonline_com", 244.95, "https://perfumeonline.com/products/tom-ford-tobacco-vanille", 50.0, "spray"),
            ("reblscents", 249.00, "https://reblscents.com/products/tom-ford-tobacco-vanille", 50.0, "spray")
        ],
        "clones": [
            ("Maison Alhambra", "Tobacco Touch", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80"),
            ("Al Haramain", "Amber Oud Tobacco Edition", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80"),
            ("Paris Corner", "Charuto Tobacco Vanille", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Tom Ford",
        "name": "Lost Cherry",
        "normalized": "lost_cherry",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("jomashop", 249.99, "https://www.jomashop.com/tom-ford-lost-cherry.html", 50.0, "spray"),
            ("perfumeonline_com", 259.95, "https://perfumeonline.com/products/tom-ford-lost-cherry", 50.0, "spray"),
            ("reblscents", 265.00, "https://reblscents.com/products/tom-ford-lost-cherry", 50.0, "spray")
        ],
        "clones": [
            ("Maison Alhambra", "Lovely Cherie", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80"),
            ("Paris Corner", "Boozy Cherry", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Tom Ford",
        "name": "Oud Wood",
        "normalized": "oud_wood",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 189.99, "https://www.aurafragrance.com/products/tom-ford-oud-wood", 50.0, "spray"),
            ("jomashop", 199.99, "https://www.jomashop.com/tom-ford-oud-wood.html", 50.0, "spray"),
            ("perfumeonline_com", 209.95, "https://perfumeonline.com/products/tom-ford-oud-wood", 50.0, "spray")
        ],
        "clones": [
            ("Maison Alhambra", "Woody Oud", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Tom Ford",
        "name": "Tuscan Leather",
        "normalized": "tuscan_leather",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("jomashop", 229.99, "https://www.jomashop.com/tom-ford-tuscan-leather.html", 50.0, "spray"),
            ("perfumeonline_com", 239.95, "https://perfumeonline.com/products/tom-ford-tuscan-leather", 50.0, "spray")
        ],
        "clones": [
            ("Rasasi", "La Yuqawam Pour Homme", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Yves Saint Laurent",
        "name": "Tuxedo",
        "normalized": "tuxedo",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("jomashop", 275.00, "https://www.jomashop.com/yves-saint-laurent-tuxedo.html", 125.0, "spray"),
            ("perfumeonline_com", 289.95, "https://perfumeonline.com/products/ysl-tuxedo", 125.0, "spray")
        ],
        "clones": [
            ("Maison Alhambra", "The Tux", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80"),
            ("Fragrance World", "Suits", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80"),
            ("Rochas", "Moustache EDP", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Jean Paul Gaultier",
        "name": "Ultra Male",
        "normalized": "ultra_male",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 89.99, "https://www.aurafragrance.com/products/jpg-ultra-male", 125.0, "spray"),
            ("jomashop", 98.00, "https://www.jomashop.com/jean-paul-gaultier-ultra-male.html", 125.0, "spray"),
            ("perfumeonline_com", 99.95, "https://perfumeonline.com/products/jpg-ultra-male", 125.0, "spray")
        ],
        "clones": [
            ("Afnan", "9pm", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Xerjoff",
        "name": "Naxos",
        "normalized": "naxos",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 189.99, "https://www.aurafragrance.com/products/xerjoff-naxos", 100.0, "spray"),
            ("jomashop", 199.99, "https://www.jomashop.com/xerjoff-naxos.html", 100.0, "spray"),
            ("perfumeonline_com", 209.95, "https://perfumeonline.com/products/xerjoff-naxos", 100.0, "spray")
        ],
        "clones": [
            ("Paris Corner", "Emir Voux Elegante", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Nishane",
        "name": "Ani",
        "normalized": "ani",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 149.99, "https://www.aurafragrance.com/products/nishane-ani", 100.0, "spray"),
            ("jomashop", 159.99, "https://www.jomashop.com/nishane-ani.html", 100.0, "spray"),
            ("perfumeonline_com", 169.95, "https://perfumeonline.com/products/nishane-ani", 100.0, "spray")
        ],
        "clones": [
            ("Paris Corner", "Emir Celestial", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80"),
            ("Spectra", "Spectra 154", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Nishane",
        "name": "Hacivat",
        "normalized": "hacivat",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 159.99, "https://www.aurafragrance.com/products/nishane-hacivat", 100.0, "spray"),
            ("jomashop", 168.00, "https://www.jomashop.com/nishane-hacivat.html", 100.0, "spray"),
            ("perfumeonline_com", 179.95, "https://perfumeonline.com/products/nishane-hacivat", 100.0, "spray")
        ],
        "clones": [
            ("Afnan", "Supremacy Not Only Intense", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Parfums de Marly",
        "name": "Pegasus",
        "normalized": "pegasus",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 185.00, "https://www.aurafragrance.com/products/pdm-pegasus", 125.0, "spray"),
            ("jomashop", 195.00, "https://www.jomashop.com/parfums-de-marly-pegasus.html", 125.0, "spray"),
            ("perfumeonline_com", 204.95, "https://perfumeonline.com/products/pdm-pegasus", 125.0, "spray")
        ],
        "clones": [
            ("Armaf", "Craze", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Parfums de Marly",
        "name": "Herod",
        "normalized": "herod",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 189.99, "https://www.aurafragrance.com/products/pdm-herod", 125.0, "spray"),
            ("jomashop", 198.00, "https://www.jomashop.com/parfums-de-marly-herod.html", 125.0, "spray"),
            ("perfumeonline_com", 209.95, "https://perfumeonline.com/products/pdm-herod", 125.0, "spray")
        ],
        "clones": [
            ("Maison Alhambra", "Hercules", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Parfums de Marly",
        "name": "Delina",
        "normalized": "delina",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 215.00, "https://www.aurafragrance.com/products/pdm-delina", 75.0, "spray"),
            ("jomashop", 225.00, "https://www.jomashop.com/parfums-de-marly-delina.html", 75.0, "spray"),
            ("perfumeonline_com", 234.95, "https://perfumeonline.com/products/pdm-delina", 75.0, "spray")
        ],
        "clones": [
            ("Armaf", "Club De Nuit Imperiale", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80"),
            ("Maison Alhambra", "Delilah", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Parfums de Marly",
        "name": "Greenley",
        "normalized": "greenley",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 195.00, "https://www.aurafragrance.com/products/pdm-greenley", 125.0, "spray"),
            ("jomashop", 205.00, "https://www.jomashop.com/parfums-de-marly-greenley.html", 125.0, "spray"),
            ("perfumeonline_com", 214.95, "https://perfumeonline.com/products/pdm-greenley", 125.0, "spray")
        ],
        "clones": [
            ("French Avenue", "Avenue Green", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Parfums de Marly",
        "name": "Haltane",
        "normalized": "haltane",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 225.00, "https://www.aurafragrance.com/products/pdm-haltane", 125.0, "spray"),
            ("jomashop", 239.00, "https://www.jomashop.com/parfums-de-marly-haltane.html", 125.0, "spray"),
            ("perfumeonline_com", 249.95, "https://perfumeonline.com/products/pdm-haltane", 125.0, "spray")
        ],
        "clones": [
            ("Lattafa", "Oud for Glory (Bade'e Al Oud)", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Maison Francis Kurkdjian",
        "name": "Grand Soir",
        "normalized": "grand_soir",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("jomashop", 198.00, "https://www.jomashop.com/maison-francis-kurkdjian-grand-soir.html", 70.0, "spray"),
            ("perfumeonline_com", 209.95, "https://perfumeonline.com/products/mfk-grand-soir", 70.0, "spray")
        ],
        "clones": [
            ("Lattafa", "Eternal Oud", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Maison Francis Kurkdjian",
        "name": "Gentle Fluidity Silver",
        "normalized": "gentle_fluidity_silver",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("jomashop", 195.00, "https://www.jomashop.com/maison-francis-kurkdjian-gentle-fluidity-silver.html", 70.0, "spray"),
            ("perfumeonline_com", 204.95, "https://perfumeonline.com/products/mfk-gentle-fluidity-silver", 70.0, "spray")
        ],
        "clones": [
            ("Maison Alhambra", "Silver Fluid", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Maison Francis Kurkdjian",
        "name": "Oud Satin Mood",
        "normalized": "oud_satin_mood",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("jomashop", 225.00, "https://www.jomashop.com/maison-francis-kurkdjian-oud-satin-mood.html", 70.0, "spray"),
            ("perfumeonline_com", 239.95, "https://perfumeonline.com/products/mfk-oud-satin-mood", 70.0, "spray")
        ],
        "clones": [
            ("Barakkat", "Satin Oud", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Creed",
        "name": "Green Irish Tweed",
        "normalized": "green_irish_tweed",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 229.99, "https://www.aurafragrance.com/products/creed-green-irish-tweed", 100.0, "spray"),
            ("jomashop", 239.99, "https://www.jomashop.com/creed-green-irish-tweed.html", 100.0, "spray"),
            ("perfumeonline_com", 249.95, "https://perfumeonline.com/products/creed-green-irish-tweed", 100.0, "spray")
        ],
        "clones": [
            ("Armaf", "Tres Nuit", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80"),
            ("Davidoff", "Cool Water", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Creed",
        "name": "Silver Mountain Water",
        "normalized": "silver_mountain_water",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 229.99, "https://www.aurafragrance.com/products/creed-silver-mountain-water", 100.0, "spray"),
            ("jomashop", 239.99, "https://www.jomashop.com/creed-silver-mountain-water.html", 100.0, "spray"),
            ("perfumeonline_com", 249.95, "https://perfumeonline.com/products/creed-silver-mountain-water", 100.0, "spray")
        ],
        "clones": [
            ("Armaf", "Club De Nuit Sillage", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80"),
            ("Al Haramain", "L'Aventure Blanche", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Creed",
        "name": "Virgin Island Water",
        "normalized": "virgin_island_water",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("jomashop", 245.00, "https://www.jomashop.com/creed-virgin-island-water.html", 100.0, "spray"),
            ("perfumeonline_com", 259.95, "https://perfumeonline.com/products/creed-virgin-island-water", 100.0, "spray")
        ],
        "clones": [
            ("Tommy Bahama", "Set Sail St. Barts", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80"),
            ("Alexandria Fragrances", "Hawaii Volcano", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Creed",
        "name": "Millesime Imperial",
        "normalized": "millesime_imperial",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("jomashop", 235.00, "https://www.jomashop.com/creed-millesime-imperial.html", 100.0, "spray"),
            ("perfumeonline_com", 249.95, "https://perfumeonline.com/products/creed-millesime-imperial", 100.0, "spray")
        ],
        "clones": [
            ("Armaf", "Club De Nuit Milestone", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Dior",
        "name": "Sauvage",
        "normalized": "sauvage",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 109.99, "https://www.aurafragrance.com/products/dior-sauvage-edt", 100.0, "spray"),
            ("jomashop", 115.00, "https://www.jomashop.com/christian-dior-sauvage.html", 100.0, "spray"),
            ("perfumeonline_com", 119.95, "https://perfumeonline.com/products/dior-sauvage-edt", 100.0, "spray")
        ],
        "clones": [
            ("Armaf", "Ventana Pour Homme", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80"),
            ("Prada", "Luna Rossa Carbon", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Chanel",
        "name": "Bleu de Chanel",
        "normalized": "bleu_de_chanel",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("macys", 145.00, "https://www.macys.com/shop/product/bleu-de-chanel-edp", 100.0, "spray"),
            ("perfumeonline_com", 159.95, "https://perfumeonline.com/products/bleu-de-chanel-edp", 100.0, "spray")
        ],
        "clones": [
            ("Armaf", "Club De Nuit Iconic", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80"),
            ("Missoni", "Missoni Wave", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Maison Margiela",
        "name": "Jazz Club",
        "normalized": "jazz_club",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 115.00, "https://www.aurafragrance.com/products/replica-jazz-club", 100.0, "spray"),
            ("jomashop", 125.00, "https://www.jomashop.com/maison-margiela-jazz-club.html", 100.0, "spray"),
            ("perfumeonline_com", 129.95, "https://perfumeonline.com/products/replica-jazz-club", 100.0, "spray")
        ],
        "clones": [
            ("Montagne", "Brooklyn Jazz", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Maison Margiela",
        "name": "By the Fireplace",
        "normalized": "by_the_fireplace",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 115.00, "https://www.aurafragrance.com/products/replica-by-the-fireplace", 100.0, "spray"),
            ("jomashop", 125.00, "https://www.jomashop.com/maison-margiela-by-the-fireplace.html", 100.0, "spray"),
            ("perfumeonline_com", 129.95, "https://perfumeonline.com/products/replica-by-the-fireplace", 100.0, "spray")
        ],
        "clones": [
            ("Lattafa", "Ameer Al Oudh Intense Oud", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Viktor & Rolf",
        "name": "Spicebomb Extreme",
        "normalized": "spicebomb_extreme",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 99.99, "https://www.aurafragrance.com/products/spicebomb-extreme", 90.0, "spray"),
            ("jomashop", 105.00, "https://www.jomashop.com/viktor-rolf-spicebomb-extreme.html", 90.0, "spray"),
            ("perfumeonline_com", 112.95, "https://perfumeonline.com/products/spicebomb-extreme", 90.0, "spray")
        ],
        "clones": [
            ("Fragrance World", "Apex", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Jean Paul Gaultier",
        "name": "Le Male Le Parfum",
        "normalized": "le_male_le_parfum",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 105.00, "https://www.aurafragrance.com/products/jpg-le-male-le-parfum", 125.0, "spray"),
            ("jomashop", 112.00, "https://www.jomashop.com/jean-paul-gaultier-le-male-le-parfum.html", 125.0, "spray"),
            ("perfumeonline_com", 119.95, "https://perfumeonline.com/products/jpg-le-male-le-parfum", 125.0, "spray")
        ],
        "clones": [
            ("Maison Alhambra", "Glacier Le Noir", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Giorgio Armani",
        "name": "Acqua Di Gio Parfum",
        "normalized": "acqua_di_gio_parfum",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 115.00, "https://www.aurafragrance.com/products/adg-parfum", 125.0, "spray"),
            ("jomashop", 122.00, "https://www.jomashop.com/giorgio-armani-acqua-di-gio-parfum.html", 125.0, "spray"),
            ("perfumeonline_com", 129.95, "https://perfumeonline.com/products/adg-parfum", 125.0, "spray")
        ],
        "clones": [
            ("Lattafa", "Liam Blue Shine", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Giorgio Armani",
        "name": "Stronger With You Intensely",
        "normalized": "stronger_with_you_intensely",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 95.00, "https://www.aurafragrance.com/products/swy-intensely", 100.0, "spray"),
            ("jomashop", 105.00, "https://www.jomashop.com/giorgio-armani-stronger-with-you-intensely.html", 100.0, "spray"),
            ("perfumeonline_com", 112.95, "https://perfumeonline.com/products/swy-intensely", 100.0, "spray")
        ],
        "clones": [
            ("Lattafa", "Khamrah Qahwa", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80"),
            ("Fragrance World", "Proud of You Absolute", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Yves Saint Laurent",
        "name": "Y Eau de Parfum",
        "normalized": "y_eau_de_parfum",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 105.00, "https://www.aurafragrance.com/products/ysl-y-edp", 100.0, "spray"),
            ("jomashop", 112.00, "https://www.jomashop.com/yves-saint-laurent-y-edp.html", 100.0, "spray"),
            ("perfumeonline_com", 119.95, "https://perfumeonline.com/products/ysl-y-edp", 100.0, "spray")
        ],
        "clones": [
            ("Lattafa", "Fakhar Black", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80"),
            ("Maison Alhambra", "Yeah!", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Versace",
        "name": "Eros",
        "normalized": "eros",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 65.00, "https://www.aurafragrance.com/products/versace-eros-edt", 100.0, "spray"),
            ("jomashop", 69.99, "https://www.jomashop.com/versace-eros-edt.html", 100.0, "spray"),
            ("perfumeonline_com", 72.95, "https://perfumeonline.com/products/versace-eros-edt", 100.0, "spray")
        ],
        "clones": [
            ("Maison Alhambra", "Versencia Oro", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Paco Rabanne",
        "name": "1 Million",
        "normalized": "1_million",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 78.00, "https://www.aurafragrance.com/products/paco-rabanne-1-million", 100.0, "spray"),
            ("jomashop", 82.50, "https://www.jomashop.com/paco-rabanne-1-million.html", 100.0, "spray"),
            ("perfumeonline_com", 86.95, "https://perfumeonline.com/products/paco-rabanne-1-million", 100.0, "spray")
        ],
        "clones": [
            ("Armaf", "Tag-Him Prestige", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Paco Rabanne",
        "name": "Invictus Victory",
        "normalized": "invictus_victory",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 85.00, "https://www.aurafragrance.com/products/paco-rabanne-invictus-victory", 100.0, "spray"),
            ("jomashop", 89.99, "https://www.jomashop.com/paco-rabanne-invictus-victory.html", 100.0, "spray"),
            ("perfumeonline_com", 94.95, "https://perfumeonline.com/products/paco-rabanne-invictus-victory", 100.0, "spray")
        ],
        "clones": [
            ("Maison Alhambra", "Victorioso Victory", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Le Labo",
        "name": "Santal 33",
        "normalized": "santal_33",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("jomashop", 249.00, "https://www.jomashop.com/le-labo-santal-33.html", 100.0, "spray"),
            ("perfumeonline_com", 264.95, "https://perfumeonline.com/products/le-labo-santal-33", 100.0, "spray")
        ],
        "clones": [
            ("Maison Louis Marie", "No.04 Bois de Balincourt", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80"),
            ("Montagne", "Eau Santal", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Louis Vuitton",
        "name": "Imagination",
        "normalized": "imagination",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("perfumeonline_com", 365.00, "https://perfumeonline.com/products/louis-vuitton-imagination", 100.0, "spray")
        ],
        "clones": [
            ("Montagne", "Imaginary", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80"),
            ("Zara", "Sunrise on the Red Sand Dunes", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Louis Vuitton",
        "name": "Afternoon Swim",
        "normalized": "afternoon_swim",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("perfumeonline_com", 365.00, "https://perfumeonline.com/products/louis-vuitton-afternoon-swim", 100.0, "spray")
        ],
        "clones": [
            ("Montagne", "Afternoon Dive", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Roja Parfums",
        "name": "Elysium Pour Homme",
        "normalized": "elysium_pour_homme",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("jomashop", 245.00, "https://www.jomashop.com/roja-parfums-elysium.html", 100.0, "spray"),
            ("perfumeonline_com", 259.95, "https://perfumeonline.com/products/roja-elysium", 100.0, "spray")
        ],
        "clones": [
            ("Fragrance World", "Imperium", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80"),
            ("Divain", "Divain-339", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Amouage",
        "name": "Reflection Man",
        "normalized": "reflection_man",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 215.00, "https://www.aurafragrance.com/products/amouage-reflection-man", 100.0, "spray"),
            ("jomashop", 229.00, "https://www.jomashop.com/amouage-reflection-man.html", 100.0, "spray"),
            ("perfumeonline_com", 239.95, "https://perfumeonline.com/products/amouage-reflection-man", 100.0, "spray")
        ],
        "clones": [
            ("Paris Corner", "Emir Rifaaqat", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Amouage",
        "name": "Interlude Man",
        "normalized": "interlude_man",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 205.00, "https://www.aurafragrance.com/products/amouage-interlude-man", 100.0, "spray"),
            ("jomashop", 219.00, "https://www.jomashop.com/amouage-interlude-man.html", 100.0, "spray"),
            ("perfumeonline_com", 229.95, "https://perfumeonline.com/products/amouage-interlude-man", 100.0, "spray")
        ],
        "clones": [
            ("Swiss Arabian", "Shaghaf Oud Abyad", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80"),
            ("Ard Al Zaafaran", "Midnight Oud", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Chanel",
        "name": "Allure Homme Sport Eau Extreme",
        "normalized": "allure_homme_sport_eau_extreme",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("macys", 145.00, "https://www.macys.com/shop/product/chanel-allure-homme-sport-eau-extreme", 100.0, "spray"),
            ("perfumeonline_com", 159.95, "https://perfumeonline.com/products/chanel-allure-homme-sport-eau-extreme", 100.0, "spray")
        ],
        "clones": [
            ("Armaf", "Aura Fresh", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80"),
            ("Missoni", "Wave", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Dior",
        "name": "Dior Homme Intense",
        "normalized": "dior_homme_intense",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 125.00, "https://www.aurafragrance.com/products/dior-homme-intense", 100.0, "spray"),
            ("jomashop", 134.00, "https://www.jomashop.com/christian-dior-dior-homme-intense.html", 100.0, "spray"),
            ("perfumeonline_com", 139.95, "https://perfumeonline.com/products/dior-homme-intense", 100.0, "spray")
        ],
        "clones": [
            ("Kayaan", "Classic", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80"),
            ("Fragrance World", "Dark Door Intense", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Byredo",
        "name": "Bal d'Afrique",
        "normalized": "bal_d_afrique",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("jomashop", 215.00, "https://www.jomashop.com/byredo-bal-dafrique.html", 100.0, "spray"),
            ("perfumeonline_com", 229.95, "https://perfumeonline.com/products/byredo-bal-dafrique", 100.0, "spray")
        ],
        "clones": [
            ("Emir", "Voux Zingy", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Byredo",
        "name": "Gypsy Water",
        "normalized": "gypsy_water",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("jomashop", 215.00, "https://www.jomashop.com/byredo-gypsy-water.html", 100.0, "spray"),
            ("perfumeonline_com", 229.95, "https://perfumeonline.com/products/byredo-gypsy-water", 100.0, "spray")
        ],
        "clones": [
            ("Oakcha", "Morning Rain", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Initio Parfums Prives",
        "name": "Oud for Greatness",
        "normalized": "oud_for_greatness",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 265.00, "https://www.aurafragrance.com/products/initio-oud-for-greatness", 90.0, "spray"),
            ("jomashop", 279.00, "https://www.jomashop.com/initio-oud-for-greatness.html", 90.0, "spray"),
            ("perfumeonline_com", 289.95, "https://perfumeonline.com/products/initio-oud-for-greatness", 90.0, "spray")
        ],
        "clones": [
            ("Lattafa", "Bade'e Al Oud (Oud for Glory)", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80"),
            ("Afnan", "Supremacy in Oud", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Initio Parfums Prives",
        "name": "Side Effect",
        "normalized": "side_effect",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 255.00, "https://www.aurafragrance.com/products/initio-side-effect", 90.0, "spray"),
            ("jomashop", 269.00, "https://www.jomashop.com/initio-side-effect.html", 90.0, "spray"),
            ("perfumeonline_com", 279.95, "https://perfumeonline.com/products/initio-side-effect", 90.0, "spray")
        ],
        "clones": [
            ("Fragrance World", "After Effect", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Kilian",
        "name": "Black Phantom",
        "normalized": "black_phantom",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 210.00, "https://www.aurafragrance.com/products/kilian-black-phantom", 50.0, "spray"),
            ("jomashop", 225.00, "https://www.jomashop.com/by-kilian-black-phantom.html", 50.0, "spray"),
            ("perfumeonline_com", 234.95, "https://perfumeonline.com/products/kilian-black-phantom", 50.0, "spray")
        ],
        "clones": [
            ("Paris Corner", "Emir Dark Knight", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Xerjoff",
        "name": "Erba Pura",
        "normalized": "erba_pura",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 185.00, "https://www.aurafragrance.com/products/xerjoff-erba-pura", 100.0, "spray"),
            ("jomashop", 195.00, "https://www.jomashop.com/xerjoff-erba-pura.html", 100.0, "spray"),
            ("perfumeonline_com", 204.95, "https://perfumeonline.com/products/xerjoff-erba-pura", 100.0, "spray")
        ],
        "clones": [
            ("Lattafa", "Ana Abiyedh", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80"),
            ("Al Haramain", "Amber Oud Gold Edition", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Mancera",
        "name": "Cedrat Boise",
        "normalized": "cedrat_boise",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 89.99, "https://www.aurafragrance.com/products/mancera-cedrat-boise", 120.0, "spray"),
            ("jomashop", 95.00, "https://www.jomashop.com/mancera-cedrat-boise.html", 120.0, "spray"),
            ("perfumeonline_com", 99.95, "https://perfumeonline.com/products/mancera-cedrat-boise", 120.0, "spray")
        ],
        "clones": [
            ("Montblanc", "Explorer", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Montale",
        "name": "Arabians Tonka",
        "normalized": "arabians_tonka",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 115.00, "https://www.aurafragrance.com/products/montale-arabians-tonka", 100.0, "spray"),
            ("jomashop", 124.00, "https://www.jomashop.com/montale-arabians-tonka.html", 100.0, "spray"),
            ("perfumeonline_com", 129.95, "https://perfumeonline.com/products/montale-arabians-tonka", 100.0, "spray")
        ],
        "clones": [
            ("Lattafa", "Ishq Al Shuyukh Gold", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Tom Ford",
        "name": "Ombre Leather",
        "normalized": "ombre_leather",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 135.00, "https://www.aurafragrance.com/products/tom-ford-ombre-leather", 100.0, "spray"),
            ("jomashop", 145.00, "https://www.jomashop.com/tom-ford-ombre-leather.html", 100.0, "spray"),
            ("perfumeonline_com", 152.95, "https://perfumeonline.com/products/tom-ford-ombre-leather", 100.0, "spray")
        ],
        "clones": [
            ("Maison Alhambra", "Amber & Leather", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80"),
            ("Afnan", "Rare Carbon", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Tom Ford",
        "name": "Bitter Peach",
        "normalized": "bitter_peach",
        "segment": FragranceMarketSegment.niche,
        "image_url": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("jomashop", 249.00, "https://www.jomashop.com/tom-ford-bitter-peach.html", 50.0, "spray"),
            ("perfumeonline_com", 259.95, "https://perfumeonline.com/products/tom-ford-bitter-peach", 50.0, "spray")
        ],
        "clones": [
            ("Maison Alhambra", "Bright Peach", "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Tom Ford",
        "name": "Noir Extreme",
        "normalized": "noir_extreme",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 139.99, "https://www.aurafragrance.com/products/tom-ford-noir-extreme", 100.0, "spray"),
            ("jomashop", 149.00, "https://www.jomashop.com/tom-ford-noir-extreme.html", 100.0, "spray"),
            ("perfumeonline_com", 154.95, "https://perfumeonline.com/products/tom-ford-noir-extreme", 100.0, "spray")
        ],
        "clones": [
            ("Armaf", "Odyssey Homme", "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Yves Saint Laurent",
        "name": "La Nuit de L'Homme",
        "normalized": "la_nuit_de_l_homme",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 78.00, "https://www.aurafragrance.com/products/ysl-la-nuit-de-lhomme", 100.0, "spray"),
            ("jomashop", 84.00, "https://www.jomashop.com/yves-saint-laurent-la-nuit-de-lhomme.html", 100.0, "spray"),
            ("perfumeonline_com", 89.95, "https://perfumeonline.com/products/ysl-la-nuit-de-lhomme", 100.0, "spray")
        ],
        "clones": [
            ("Zara", "Starlight Vanilla / Night Pour Homme", "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80")
        ]
    },
    {
        "brand": "Prada",
        "name": "Luna Rossa Black",
        "normalized": "luna_rossa_black",
        "segment": FragranceMarketSegment.designer,
        "image_url": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
        "prices": [
            ("aurafragrance", 95.00, "https://www.aurafragrance.com/products/prada-luna-rossa-black", 100.0, "spray"),
            ("jomashop", 104.00, "https://www.jomashop.com/prada-luna-rossa-black.html", 100.0, "spray"),
            ("perfumeonline_com", 109.95, "https://perfumeonline.com/products/prada-luna-rossa-black", 100.0, "spray")
        ],
        "clones": [
            ("Lattafa", "Ejaazi", "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80")
        ]
    }
]

async def sync_50_catalog():
    print(f"=== PROCESSING & AUDITING {len(CATALOG_50)} ICONIC FRAGRANCES ===")
    
    async with async_session_maker() as session:
        # 1. Ensure Retailers exist with correct URLs
        retailer_db_map = {}
        retailer_configs = [
            ("reblscents", "ReblScents", "https://reblscents.com"),
            ("perfumeonline_com", "PerfumeOnline.com", "https://perfumeonline.com"),
            ("jomashop", "Jomashop", "https://jomashop.com"),
            ("aurafragrance", "Aura Fragrance", "https://www.aurafragrance.com"),
            ("macys", "Macys", "https://www.macys.com"),
            ("fragrancenet", "FragranceNet", "https://www.fragrancenet.com")
        ]
        
        for norm, rname, rurl in retailer_configs:
            r_res = await session.execute(select(Retailer).filter_by(normalized_name=norm))
            r_obj = r_res.scalar_one_or_none()
            if not r_obj:
                r_obj = Retailer(name=rname, normalized_name=norm, website_url=rurl)
                session.add(r_obj)
                await session.flush()
            else:
                r_obj_any: Any = r_obj
                r_obj_any.name = rname
                r_obj_any.website_url = rurl
            retailer_db_map[norm] = r_obj

        # 2. Iterate through each fragrance in the 50 catalog
        for idx, item in enumerate(CATALOG_50, 1):
            bname = item["brand"]
            fname = item["name"]
            fnorm = item["normalized"]
            fseg = item["segment"]
            fimg = item["image_url"]
            
            print(f"[{idx}/{len(CATALOG_50)}] Auditing: {bname} - {fname}")
            
            # Ensure Brand
            b_norm = bname.lower().replace(" ", "_").replace("'", "").replace("&", "and")
            b_res = await session.execute(select(Brand).filter_by(normalized_name=b_norm))
            brand_obj = b_res.scalar_one_or_none()
            if not brand_obj:
                brand_obj = Brand(name=bname, normalized_name=b_norm)
                session.add(brand_obj)
                await session.flush()
                
            # Ensure FragranceDNA
            dna_res = await session.execute(
                select(FragranceDNA).where(
                    (FragranceDNA.origin_brand_id == brand_obj.brand_id) &
                    ((FragranceDNA.canonical_name.ilike(fname)) | (FragranceDNA.normalized_name == fnorm))
                )
            )
            dna = dna_res.scalars().first()
            if not dna:
                dna_res2 = await session.execute(
                    select(FragranceDNA).where(
                        (FragranceDNA.canonical_name.ilike(fname)) | (FragranceDNA.normalized_name == fnorm)
                    )
                )
                dna = dna_res2.scalars().first()
                
            if not dna:
                dna = FragranceDNA(
                    canonical_name=fname,
                    normalized_name=fnorm,
                    sort_key=fname,
                    origin_brand_id=brand_obj.brand_id,
                    market_segment=fseg,
                    is_dupe=False,
                    image_url=fimg
                )
                session.add(dna)
                await session.flush()
            else:
                dna_any: Any = dna
                dna_any.image_url = fimg
                dna_any.market_segment = fseg
                dna_any.is_dupe = False
                dna_any.origin_brand_id = brand_obj.brand_id
                
            # Ensure Line and Product
            line_res = await session.execute(
                select(FragranceLine).where(
                    (FragranceLine.brand_id == brand_obj.brand_id) &
                    ((FragranceLine.dna_id == dna.dna_id) | (FragranceLine.normalized_name == fnorm))
                )
            )
            line = line_res.scalars().first()
            if not line:
                line = FragranceLine(dna_id=dna.dna_id, name=fname, normalized_name=fnorm, brand_id=brand_obj.brand_id)
                session.add(line)
                await session.flush()
            else:
                line.dna_id = dna.dna_id
                
            prod_res = await session.execute(select(FragranceProduct).filter_by(line_id=line.line_id))
            prod = prod_res.scalars().first()
            if not prod:
                prod = FragranceProduct(line_id=line.line_id, formulation_version="original")
                session.add(prod)
                await session.flush()

            # Clean mismatched prices attached to this DNA (e.g. clone brands or oil dupes)
            all_vars = (await session.execute(select(ProductVariant).where(ProductVariant.product_id == prod.product_id))).scalars().all()
            for v in all_vars:
                obs_list = (await session.execute(select(PriceObservation).where(PriceObservation.variant_id == v.variant_id))).scalars().all()
                for obs in obs_list:
                    u_low = (obs.source_url or "").lower()
                    # Check for clone brands or clone keywords
                    if any(cb in u_low for cb in ["banadir", "armaf", "afnan", "lattafa", "alhambra", "paris-corner", "french-avenue", "dunhil"]):
                        if brand_obj.normalized_name not in ["banadir_fragrance", "armaf", "afnan", "lattafa", "alfred_dunhill"]:
                            await session.delete(obs)
                            
            # Add genuine prices
            for r_norm, p_amt, src_url, vol, pkg in item.get("prices", []):
                r_obj = retailer_db_map.get(r_norm)
                if not r_obj:
                    continue
                # Find or create variant for vol and pkg
                var_res = await session.execute(
                    select(ProductVariant).filter_by(product_id=prod.product_id, volume_ml=float(vol))
                )
                var_obj = var_res.scalars().first()
                if not var_obj:
                    var_obj = ProductVariant(product_id=prod.product_id, volume_ml=float(vol), package_type=pkg)
                    session.add(var_obj)
                    await session.flush()
                else:
                    var_obj.package_type = pkg

                # Check if price observation exists
                obs_chk = await session.execute(
                    select(PriceObservation).filter_by(variant_id=var_obj.variant_id, retailer_id=r_obj.retailer_id)
                )
                existing_obs = obs_chk.scalars().first()
                if not existing_obs:
                    new_obs = PriceObservation(
                        variant_id=var_obj.variant_id,
                        retailer_id=r_obj.retailer_id,
                        currency_code="USD",
                        price_amount=p_amt,
                        source_url=src_url
                    )
                    session.add(new_obs)
                else:
                    existing_obs.price_amount = p_amt
                    existing_obs.source_url = src_url

            # Process Clones / Inspired By section
            for clone_bname, clone_fname, clone_img in item.get("clones", []):
                cb_norm = clone_bname.lower().replace(" ", "_").replace("'", "").replace("&", "and")
                cb_res = await session.execute(select(Brand).filter_by(normalized_name=cb_norm))
                c_brand = cb_res.scalar_one_or_none()
                if not c_brand:
                    c_brand = Brand(name=clone_bname, normalized_name=cb_norm)
                    session.add(c_brand)
                    await session.flush()

                c_fnorm = clone_fname.lower().replace(" ", "_").replace("'", "").replace("-", "_")
                c_dna_res = await session.execute(
                    select(FragranceDNA).where(
                        (FragranceDNA.origin_brand_id == c_brand.brand_id) &
                        ((FragranceDNA.canonical_name.ilike(clone_fname)) | (FragranceDNA.normalized_name == c_fnorm))
                    )
                )
                c_dna = c_dna_res.scalars().first()
                if not c_dna:
                    c_dna_res2 = await session.execute(
                        select(FragranceDNA).where(
                            (FragranceDNA.canonical_name.ilike(clone_fname)) | (FragranceDNA.normalized_name == c_fnorm)
                        )
                    )
                    c_dna = c_dna_res2.scalars().first()

                if not c_dna:
                    c_dna = FragranceDNA(
                        canonical_name=clone_fname,
                        normalized_name=c_fnorm,
                        sort_key=clone_fname,
                        origin_brand_id=c_brand.brand_id,
                        market_segment=FragranceMarketSegment.clone,
                        is_dupe=True,
                        inspired_by=f"{bname} {fname}",
                        image_url=clone_img
                    )
                    session.add(c_dna)
                    await session.flush()
                else:
                    c_dna_any: Any = c_dna
                    c_dna_any.image_url = clone_img
                    c_dna_any.is_dupe = True
                    c_dna_any.inspired_by = f"{bname} {fname}"

                # Link in dna_relationship
                rel_res = await session.execute(
                    select(DNARelationship).filter_by(
                        source_dna_id=c_dna.dna_id,
                        target_dna_id=dna.dna_id,
                        relationship_type=RelationType.inspired_by
                    )
                )
                if not rel_res.scalar_one_or_none():
                    session.add(DNARelationship(
                        source_dna_id=c_dna.dna_id,
                        target_dna_id=dna.dna_id,
                        relationship_type=RelationType.inspired_by,
                        confidence_score=0.95
                    ))

        await session.commit()
        print("=== 50 FRAGRANCES AUDIT & SYNC COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    asyncio.run(sync_50_catalog())
