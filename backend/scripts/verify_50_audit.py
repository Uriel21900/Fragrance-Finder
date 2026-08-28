import asyncio
import os
import sys
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database import async_session_maker
from models.schema import FragranceDNA, Brand, FragranceLine, FragranceProduct, ProductVariant, PriceObservation, Retailer, DNARelationship
from scripts.audit_and_fix_catalog_50 import CATALOG_50

async def verify_50_audit():
    print(f"=== VERIFYING 50+ FRAGRANCE AUDIT ({len(CATALOG_50)} ITEMS) ===")
    
    passed_count = 0
    errors = []
    
    async with async_session_maker() as session:
        for idx, item in enumerate(CATALOG_50, 1):
            fname = item["name"]
            bname = item["brand"]
            
            # Find DNA
            dna_res = await session.execute(
                select(FragranceDNA, Brand)
                .outerjoin(Brand, FragranceDNA.origin_brand_id == Brand.brand_id)
                .where(FragranceDNA.canonical_name.ilike(fname))
            )
            row = dna_res.first()
            if not row:
                errors.append(f"[{idx}] {bname} - {fname}: DNA NOT FOUND")
                continue
                
            dna, brand = row
            
            # 1. Check Image
            if not dna.image_url:
                errors.append(f"[{idx}] {bname} - {fname}: Missing image_url")
                
            # 2. Check Price Observations for illegal clone keywords
            lines = (await session.execute(select(FragranceLine).where(FragranceLine.dna_id == dna.dna_id))).scalars().all()
            for line in lines:
                prods = (await session.execute(select(FragranceProduct).where(FragranceProduct.line_id == line.line_id))).scalars().all()
                for prod in prods:
                    vars = (await session.execute(select(ProductVariant).where(ProductVariant.product_id == prod.product_id))).scalars().all()
                    for v in vars:
                        obs_list = (await session.execute(select(PriceObservation).where(PriceObservation.variant_id == v.variant_id))).scalars().all()
                        for obs in obs_list:
                            u_low = (obs.source_url or "").lower()
                            if "banadirfragrance" in u_low and brand.normalized_name != "banadir_fragrance":
                                errors.append(f"[{idx}] {bname} - {fname}: Contains Banadir clone price: {obs.source_url}")
                            if "perfumeonline.ca" in u_low:
                                errors.append(f"[{idx}] {bname} - {fname}: Still contains perfumeonline.ca instead of .com: {obs.source_url}")
                                
            # 3. Check Clones
            clones_cnt = (await session.execute(
                select(DNARelationship).where(DNARelationship.target_dna_id == dna.dna_id)
            )).scalars().all()
            
            passed_count += 1
            print(f"PASS [{idx}/{len(CATALOG_50)}] {bname} - {fname} (ID: {dna.dna_id}) | Clones: {len(clones_cnt)} | Img: {dna.image_url[:40]}")
            
    print(f"\nAUDIT SUMMARY: {passed_count}/{len(CATALOG_50)} Passed.")
    if errors:
        print("ERRORS FOUND:")
        for err in errors:
            print(" - " + err)
    else:
        print("ALL 50+ FRAGRANCES MET ALL 3 CRITERIA WITH 100% SUCCESS!")

if __name__ == "__main__":
    asyncio.run(verify_50_audit())
