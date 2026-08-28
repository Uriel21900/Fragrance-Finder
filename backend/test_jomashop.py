from scrapers.base import ScrapedProduct
from scrapers import Job, JomashopScraper

def test_dupe_validation():
    scraper = JomashopScraper()
    job = Job(target_brand="Creed", search_term="Aventus", correlation_id="test_1")
    
    print(f"Search Job: Brand='{job.target_brand}', Term='{job.search_term}'\n")
    
    # 1. LLM-validated dupe (Title doesn't contain 'Aventus')
    sp_dupe = ScrapedProduct(
        title="Club De Nuit Intense Man EDP",
        price=35.0,
        url="...",
        is_dupe=True,
        inspired_by="Creed Aventus",
        llm_validated=True
    )
    
    print("Test 1: LLM-Validated Dupe")
    print(f"Title: {sp_dupe.title}")
    print(f"Is Valid Match? {scraper.is_valid_match(sp_dupe, job)} (Expected: True)\n")
    
    # 2. Regular Regex-matched original (Not validated by LLM)
    sp_orig = ScrapedProduct(
        title="Creed Aventus EDP",
        price=350.0,
        url="...",
        is_dupe=False,
        llm_validated=False
    )
    
    print("Test 2: Standard Match (Regex Fallback)")
    print(f"Title: {sp_orig.title}")
    print(f"Is Valid Match? {scraper.is_valid_match(sp_orig, job)} (Expected: True)\n")
    
    # 3. Irrelevant match (No LLM, fails regex)
    sp_irr = ScrapedProduct(
        title="Dior Sauvage",
        price=120.0,
        url="...",
        is_dupe=False,
        llm_validated=False
    )
    
    print("Test 3: Irrelevant Match")
    print(f"Title: {sp_irr.title}")
    print(f"Is Valid Match? {scraper.is_valid_match(sp_irr, job)} (Expected: False)\n")

if __name__ == "__main__":
    test_dupe_validation()
