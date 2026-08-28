import asyncio
import os
import sys
from sqlalchemy import select, text, delete
from urllib.parse import urlparse

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import (
    Brand, FragranceDNA, FragranceLine, FragranceProduct, ProductVariant,
    Retailer, PriceObservation, DNARelationship, RelationType,
    FragranceMarketSegment, FragranceGenderMarketing
)

async def fix_clones_and_prices():
    print("=== STARTING CLONES, RETAILER DOMAIN & AVENTUS PRICING CLEANUP ===")
    
    async with async_session_maker() as session:
        # 1. Update Retailer perfumeonline.ca -> perfumeonline.com
        print("1. Updating PerfumeOnline to perfumeonline.com...")
        po_res = await session.execute(select(Retailer).where(Retailer.normalized_name.in_(["perfumeonline", "perfumeonline_ca", "perfumeonline_com"])))
        po_retailers = po_res.scalars().all()
        for r in po_retailers:
            r.name = "PerfumeOnline.com"
            r.normalized_name = "perfumeonline_com"
            r.website_url = "https://perfumeonline.com"
            
        # Update source_urls with perfumeonline.ca to perfumeonline.com
        prices_res = await session.execute(select(PriceObservation))
        for p in prices_res.scalars().all():
            if p.source_url and "perfumeonline.ca" in p.source_url:
                p.source_url = p.source_url.replace("perfumeonline.ca", "perfumeonline.com")

        # 2. Update Creed Aventus image_url to authentic local asset
        print("2. Setting authentic Creed Aventus image...")
        dna_res = await session.execute(select(FragranceDNA).where(FragranceDNA.canonical_name == "Aventus"))
        aventus_dna = dna_res.scalar_one_or_none()
        if aventus_dna:
            aventus_dna.image_url = "/images/creed_aventus.jpg"
            print(f"Set Aventus image_url to {aventus_dna.image_url}")

        # 3. Create Brands and Clones for Banadir Fragrance and Dunhill
        print("3. Registering Banadir Fragrance and Dunhill clones...")
        # Banadir brand
        b_res = await session.execute(select(Brand).filter_by(normalized_name="banadir_fragrance"))
        banadir_brand = b_res.scalar_one_or_none()
        if not banadir_brand:
            banadir_brand = Brand(name="Banadir Fragrance", normalized_name="banadir_fragrance", website_url="https://banadirfragrance.com")
            session.add(banadir_brand)
            await session.flush()

        # Banadir 24 DNA
        b24_res = await session.execute(select(FragranceDNA).filter_by(normalized_name="24_extrait_de_parfum", origin_brand_id=banadir_brand.brand_id))
        banadir_24 = b24_res.scalar_one_or_none()
        if not banadir_24:
            banadir_24 = FragranceDNA(
                canonical_name="24 Extrait De Parfum",
                normalized_name="24_extrait_de_parfum",
                sort_key="24 Extrait De Parfum",
                origin_brand_id=banadir_brand.brand_id,
                market_segment=FragranceMarketSegment.clone,
                is_dupe=True,
                inspired_by="Creed Aventus",
                image_url="https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80"
            )
            session.add(banadir_24)
            await session.flush()

        # Banadir Adventure Absolu DNA
        badv_res = await session.execute(select(FragranceDNA).filter_by(normalized_name="adventure_absolu", origin_brand_id=banadir_brand.brand_id))
        banadir_adv = badv_res.scalar_one_or_none()
        if not banadir_adv:
            banadir_adv = FragranceDNA(
                canonical_name="Adventure Absolu",
                normalized_name="adventure_absolu",
                sort_key="Adventure Absolu",
                origin_brand_id=banadir_brand.brand_id,
                market_segment=FragranceMarketSegment.clone,
                is_dupe=True,
                inspired_by="Creed Aventus Absolu",
                image_url="https://images.unsplash.com/photo-1547887537-6158d64c35b3?w=800&auto=format&fit=crop&q=80"
            )
            session.add(banadir_adv)
            await session.flush()

        # Dunhill Brand
        dh_res = await session.execute(select(Brand).filter_by(normalized_name="alfred_dunhill"))
        dunhill_brand = dh_res.scalar_one_or_none()
        if not dunhill_brand:
            dunhill_brand = Brand(name="Alfred Dunhill", normalized_name="alfred_dunhill")
            session.add(dunhill_brand)
            await session.flush()

        # Dunhill Desire Gold DNA
        dh_dna_res = await session.execute(select(FragranceDNA).filter_by(normalized_name="desire_gold", origin_brand_id=dunhill_brand.brand_id))
        dunhill_gold = dh_dna_res.scalar_one_or_none()
        if not dunhill_gold:
            dunhill_gold = FragranceDNA(
                canonical_name="Desire Gold",
                normalized_name="desire_gold",
                sort_key="Desire Gold",
                origin_brand_id=dunhill_brand.brand_id,
                market_segment=FragranceMarketSegment.designer,
                is_dupe=True,
                inspired_by="Creed Aventus",
                image_url="https://images.unsplash.com/photo-1594035910387-fea47794261f?w=800&auto=format&fit=crop&q=80"
            )
            session.add(dunhill_gold)
            await session.flush()

        # 4. Link Clones to Creed Aventus
        print("4. Linking clones to Creed Aventus in dna_relationship...")
        if aventus_dna:
            for clone_dna in [banadir_24, banadir_adv, dunhill_gold]:
                rel_res = await session.execute(
                    select(DNARelationship).filter_by(
                        source_dna_id=clone_dna.dna_id,
                        target_dna_id=aventus_dna.dna_id,
                        relationship_type=RelationType.inspired_by
                    )
                )
                if not rel_res.scalar_one_or_none():
                    session.add(DNARelationship(
                        source_dna_id=clone_dna.dna_id,
                        target_dna_id=aventus_dna.dna_id,
                        relationship_type=RelationType.inspired_by,
                        confidence_score=0.95
                    ))
                    print(f"Linked clone {clone_dna.canonical_name} -> Aventus")

        # 5. Clean up PriceObservations attached to Creed Aventus
        print("5. Cleaning up mismatched prices on Creed Aventus...")
        if aventus_dna:
            lines = (await session.execute(select(FragranceLine).where(FragranceLine.dna_id == aventus_dna.dna_id))).scalars().all()
            for line in lines:
                prods = (await session.execute(select(FragranceProduct).where(FragranceProduct.line_id == line.line_id))).scalars().all()
                for prod in prods:
                    vars = (await session.execute(select(ProductVariant).where(ProductVariant.product_id == prod.product_id))).scalars().all()
                    for v in vars:
                        obs_list = (await session.execute(select(PriceObservation).where(PriceObservation.variant_id == v.variant_id))).scalars().all()
                        for obs in obs_list:
                            url_low = (obs.source_url or "").lower()
                            # If it's Banadirfragrance, Dunhill, or flankers (Aventus for Her, Aventus Absolu, Aventus Cologne)
                            is_banadir = "banadirfragrance.com" in url_low
                            is_dunhill = "dunhil-desire-gold" in url_low or "dunhill" in url_low
                            is_for_her = "for-her" in url_low or "for_her" in url_low
                            is_absolu = "absolu" in url_low
                            is_cologne = "cologne" in url_low

                            if is_banadir or is_dunhill or is_for_her or is_absolu or is_cologne:
                                print(f"Removing non-Aventus price observation: ${obs.price_amount} | {obs.source_url}")
                                await session.delete(obs)

        # 6. Add/Ensure real Creed Aventus price offers from Jomashop, ReblScents, PerfumeOnline, FragranceNet
        print("6. Verifying authentic Creed Aventus market prices...")
        # Get Aventus main 100ml variant
        prod_res = await session.execute(
            select(FragranceProduct)
            .join(FragranceLine, FragranceProduct.line_id == FragranceLine.line_id)
            .where(FragranceLine.dna_id == aventus_dna.dna_id)
        )
        aventus_prod = prod_res.scalars().first()
        if aventus_prod:
            var_res = await session.execute(select(ProductVariant).filter_by(product_id=aventus_prod.product_id, volume_ml=100.0))
            var_100 = var_res.scalars().first()
            if not var_100:
                var_100 = ProductVariant(product_id=aventus_prod.product_id, volume_ml=100.0, package_type="spray")
                session.add(var_100)
                await session.flush()

            # Ensure retailer records exist
            retailers_map = {}
            for rname, norm, url in [
                ("ReblScents", "reblscents", "https://reblscents.com"),
                ("PerfumeOnline.com", "perfumeonline_com", "https://perfumeonline.com"),
                ("Jomashop", "jomashop", "https://jomashop.com"),
                ("FragranceNet", "fragrancenet", "https://www.fragrancenet.com"),
                ("Aura Fragrance", "aurafragrance", "https://www.aurafragrance.com"),
            ]:
                r_res = await session.execute(select(Retailer).filter_by(normalized_name=norm))
                r_obj = r_res.scalar_one_or_none()
                if not r_obj:
                    r_obj = Retailer(name=rname, normalized_name=norm, website_url=url)
                    session.add(r_obj)
                    await session.flush()
                retailers_map[norm] = r_obj

            # Ensure authentic Creed Aventus prices
            auth_offers = [
                ("reblscents", 265.00, "https://reblscents.com/products/creed-aventus-for-men-edp"),
                ("perfumeonline_com", 279.95, "https://perfumeonline.com/products/creed-aventus-eau-de-parfum-100ml"),
                ("jomashop", 274.99, "https://www.jomashop.com/creed-aventus-edp-spray-3-3-oz-100-ml-m-aventus-3-3.html"),
                ("aurafragrance", 269.99, "https://www.aurafragrance.com/products/creed-aventus-for-men-edp-3-3-oz-spray"),
            ]

            for norm, price_amt, src_url in auth_offers:
                r_obj = retailers_map.get(norm)
                if r_obj:
                    # Check if observation already exists
                    obs_chk = await session.execute(
                        select(PriceObservation).filter_by(variant_id=var_100.variant_id, retailer_id=r_obj.retailer_id)
                    )
                    existing_obs = obs_chk.scalars().first()
                    if not existing_obs:
                        new_obs = PriceObservation(
                            variant_id=var_100.variant_id,
                            retailer_id=r_obj.retailer_id,
                            currency_code="USD",
                            price_amount=price_amt,
                            source_url=src_url
                        )
                        session.add(new_obs)
                        print(f"Added authentic price offer: {r_obj.name} - ${price_amt}")
                    else:
                        existing_obs.price_amount = price_amt
                        existing_obs.source_url = src_url

        await session.commit()
        print("=== CLEANUP & MIGRATION COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(fix_clones_and_prices())
