import asyncio
import os
import sys
from urllib.parse import urlparse
from sqlalchemy import text, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import engine, async_session_maker
from models.schema import Retailer, PriceObservation, FragranceDNA

DOMAIN_RETAILER_MAP = {
    "reblscents.com": ("ReblScents", "https://reblscents.com"),
    "banadirfragrance.com": ("Banadir Fragrance", "https://banadirfragrance.com"),
    "perfumeonline.ca": ("PerfumeOnline.com", "https://perfumeonline.com"),
    "perfumeonline.com": ("PerfumeOnline.com", "https://perfumeonline.com"),
    "shoparomatix.com": ("ShopAromatix", "https://shoparomatix.com"),
    "jomashop.com": ("Jomashop", "https://jomashop.com"),
    "aurafragrance.com": ("Aura Fragrance", "https://www.aurafragrance.com"),
    "macys.com": ("Macys", "https://www.macys.com"),
    "fragflex.com": ("FragFlex", "https://fragflex.com"),
    "labelleperfumes.com": ("Labelle Perfumes", "https://labelleperfumes.com"),
    "bestbrandsperfume.com": ("Best Brands Perfume", "https://bestbrandsperfume.com"),
    "tripletraders.com": ("Triple Traders", "https://tripletraders.com"),
    "aromaconcepts.com": ("Aroma Concepts", "https://www.aromaconcepts.com"),
    "giftexpress.com": ("Gift Express", "https://www.giftexpress.com"),
    "anaustore.com": ("Anau Store", "https://anaustore.com"),
    "lrlux.com": ("LR Lux", "https://lrlux.com"),
    "beautyhouse.com": ("Beauty House", "https://beautyhouse.com"),
    "fragranceshop.com": ("Fragrance Shop", "https://fragranceshop.com"),
    "theperfumespot.com": ("The Perfume Spot", "https://theperfumespot.com"),
    "fragrancenet.com": ("FragranceNet", "https://www.fragrancenet.com"),
    "sephora.com": ("Sephora", "https://www.sephora.com"),
}

# Curated high-res imagery for popular fragrances
FRAGRANCE_IMAGES = {
    "aventus": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
    "aventus cologne": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
    "baccarat rouge 540": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=800&auto=format&fit=crop&q=80",
    "angels' share": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
    "sauvage elixir": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
    "layton": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
    "althaïr": "https://images.unsplash.com/photo-1616949755610-8c9bbc08f138?w=800&auto=format&fit=crop&q=80",
    "althair": "https://images.unsplash.com/photo-1616949755610-8c9bbc08f138?w=800&auto=format&fit=crop&q=80",
    "delina": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
    "khamrah": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
    "asad": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
    "club de nuit intense man": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
    "grand soir": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
    "bleu de chanel": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
    "y eau de parfum": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
    "myslf": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=800&auto=format&fit=crop&q=80",
    "le male le parfum": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
    "ultra male": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
    "spicebomb extreme": "https://images.unsplash.com/photo-1616949755610-8c9bbc08f138?w=800&auto=format&fit=crop&q=80",
    "the most wanted": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
    "ombré leather": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
    "tobacco vanille": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
    "oud wood": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=800&auto=format&fit=crop&q=80",
    "naxos": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
    "erba pura": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
    "hacivat": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
    "ani": "https://images.unsplash.com/photo-1616949755610-8c9bbc08f138?w=800&auto=format&fit=crop&q=80",
    "oud for greatness": "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80",
    "bianco latte": "https://images.unsplash.com/photo-1592945403244-b3fbafd7f539?w=800&auto=format&fit=crop&q=80",
    "gris charnel": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
    "hawas": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80",
    "9pm": "https://images.unsplash.com/photo-1588405748880-12d1d2a59f75?w=800&auto=format&fit=crop&q=80",
    "explorer": "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80",
    "supremacy silver": "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80"
}

async def run_migration():
    print("=== STARTING MIGRATION: RETAILERS & FRAGRANCE IMAGERY ===")
    
    # 1. Add image_url column to fragrance_dna if missing
    async with engine.begin() as conn:
        print("Ensuring column 'image_url' exists in fragrance_dna...")
        await conn.execute(text("ALTER TABLE fragrance_dna ADD COLUMN IF NOT EXISTS image_url TEXT;"))
    
    async with async_session_maker() as session:
        # 2. Fix Retailers and Price Observations
        print("Migrating Price Observations to proper Retailers...")
        retailers_res = await session.execute(select(Retailer))
        existing_retailers = {r.normalized_name: r for r in retailers_res.scalars().all()}
        
        # Helper to get or create retailer
        async def get_or_create(norm_name, display_name, web_url):
            if norm_name in existing_retailers:
                r = existing_retailers[norm_name]
                if r.name == "Unknown":
                    r.name = display_name
                    r.website_url = web_url
                    await session.flush()
                return r
            new_r = Retailer(name=display_name, normalized_name=norm_name, website_url=web_url)
            session.add(new_r)
            await session.flush()
            existing_retailers[norm_name] = new_r
            return new_r

        prices_res = await session.execute(select(PriceObservation))
        prices = prices_res.scalars().all()
        print(f"Checking {len(prices)} price observations...")
        
        updated_count = 0
        for p in prices:
            if not p.source_url:
                continue
            parsed = urlparse(p.source_url)
            domain = parsed.netloc.lower().replace("www.", "")
            
            if domain in DOMAIN_RETAILER_MAP:
                disp_name, web_url = DOMAIN_RETAILER_MAP[domain]
                norm = domain.split(".")[0].replace("-", "_")
            elif domain:
                parts = domain.split(".")
                disp_name = parts[0].capitalize()
                web_url = f"https://{domain}"
                norm = parts[0].lower().replace("-", "_")
            else:
                continue
                
            ret = await get_or_create(norm, disp_name, web_url)
            if p.retailer_id != ret.retailer_id:
                p.retailer_id = ret.retailer_id
                updated_count += 1

        print(f"Re-linked {updated_count} price observations to specific retailers!")
        
        # 3. Clean up the 'Unknown' retailer if it exists and remove unneeded entries
        unknown_r = existing_retailers.get("unknown")
        if unknown_r:
            # Check if any price observations still use it
            res = await session.execute(select(PriceObservation).filter_by(retailer_id=unknown_r.retailer_id))
            remaining = res.scalars().all()
            if not remaining:
                await session.delete(unknown_r)
                print("Removed orphaned 'Unknown' retailer record.")

        # 4. Populate image URLs for fragrances
        print("Populating high quality fragrance images...")
        dnas_res = await session.execute(select(FragranceDNA))
        dnas = dnas_res.scalars().all()
        
        images_set = 0
        for dna in dnas:
            name_lower = dna.canonical_name.lower().strip()
            # Match directly or by keyword
            matched_img = None
            if name_lower in FRAGRANCE_IMAGES:
                matched_img = FRAGRANCE_IMAGES[name_lower]
            else:
                for k, img in FRAGRANCE_IMAGES.items():
                    if k in name_lower:
                        matched_img = img
                        break
            
            if matched_img and not dna.image_url:
                dna.image_url = matched_img
                images_set += 1
            elif not dna.image_url:
                # Provide a high-quality luxury perfume photography default based on segment
                if str(dna.market_segment).lower() == "niche":
                    dna.image_url = "https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80"
                elif str(dna.market_segment).lower() == "clone":
                    dna.image_url = "https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80"
                else:
                    dna.image_url = "https://images.unsplash.com/photo-1523293182086-7651a899d37f?w=800&auto=format&fit=crop&q=80"
                images_set += 1

        print(f"Updated {images_set} fragrances with product photography URLs.")
        await session.commit()
        print("=== MIGRATION SUCCESSFULLY COMPLETED ===")

if __name__ == "__main__":
    asyncio.run(run_migration())
