import asyncio
import httpx
from database import async_session_maker
from models.schema import FragranceDNA, FragranceLine, FragranceProduct, ProductVariant, PriceObservation, Retailer
from sqlalchemy import select
from sqlalchemy.orm import selectinload

fragrances_to_check = [
    "Cumin Fleur d'Amandier Cèdre",
    "Vanilla",
    "Le Musc & La Peau",
    "Hours Sapphire Scents Eau de Parfum",
    "Club De Nuit Sillage",
    "A Kiss from a Rose",
    "° for Women",
    "Enigma",
    "Percival",
    "Avenue Maïssa Eau de Parfum",
    "Sauvage Elixir",
    "A Man of Ultra - Spacium Cut Back (スペシウム カット バック) A Man of Ultra",
    "pm pour Femme",
    "Crepusculum Mirabile",
    "A Shot Of Muguet & Cedar"
]

async def check_url(url):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            headers = {'User-Agent': 'Mozilla/5.0'}
            resp = await client.head(url, headers=headers, follow_redirects=True)
            # Many retailers block headless/bots and return 403. We consider 200, 301, 302, 403 as "exists".
            if resp.status_code in [200, 403]:
                return True
            # if HEAD fails, try GET
            resp = await client.get(url, headers=headers, follow_redirects=True)
            return resp.status_code in [200, 403]
    except Exception:
        return False

async def main():
    async with async_session_maker() as s:
        for name in fragrances_to_check:
            print(f"\\n--- Verifying: {name} ---")
            
            stmt = select(FragranceDNA).options(selectinload(FragranceDNA.origin_brand)).where(FragranceDNA.canonical_name == name)
            res = await s.execute(stmt)
            dnas = res.scalars().all()
            
            if not dnas:
                print("RESULT: MISSING_FROM_DB")
                continue
                
            dna = dnas[0]
            
            # Check Clones/Dupes
            if dna.is_dupe:
                if dna.inspired_by:
                    print(f"DUPE_CHECK: OK (Inspired by: {dna.inspired_by})")
                else:
                    print("DUPE_CHECK: FAILED (is_dupe=True but inspired_by is null)")
            else:
                print("DUPE_CHECK: N/A (Not a dupe)")
                
            # Get Prices
            line_stmt = select(FragranceLine).where(FragranceLine.dna_id == dna.dna_id)
            lines = (await s.execute(line_stmt)).scalars().all()
            
            prices_found = 0
            urls_valid = 0
            urls_failed = 0
            
            for line in lines:
                prod_stmt = select(FragranceProduct).where(FragranceProduct.line_id == line.line_id)
                prods = (await s.execute(prod_stmt)).scalars().all()
                for prod in prods:
                    var_stmt = select(ProductVariant).where(ProductVariant.product_id == prod.product_id)
                    vars_ = (await s.execute(var_stmt)).scalars().all()
                    for v in vars_:
                        obs_stmt = select(PriceObservation).where(PriceObservation.variant_id == v.variant_id)
                        obs_list = (await s.execute(obs_stmt)).scalars().all()
                        for obs in obs_list:
                            prices_found += 1
                            if obs.price_amount <= 0:
                                print(f"PRICE_WARNING: Zero/Negative price detected (${obs.price_amount})")
                                
                            is_valid = await check_url(obs.source_url)
                            if is_valid:
                                urls_valid += 1
                            else:
                                urls_failed += 1
                                print(f"URL_WARNING: Invalid or unreachable URL ({obs.source_url})")
                                
            print(f"PRICE_CHECK: Found {prices_found} price observations.")
            if prices_found > 0:
                print(f"URL_CHECK: {urls_valid} valid, {urls_failed} failed.")
            
            if prices_found == 0:
                print("RESULT: NO_PRICES_FOUND")
            elif urls_failed > 0:
                print("RESULT: URLS_FAILED")
            else:
                print("RESULT: SUCCESS")

if __name__ == "__main__":
    asyncio.run(main())
