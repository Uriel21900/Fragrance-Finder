import json
from pydantic import BaseModel, Field
from typing import Optional
from crawl4ai.extraction_strategy import LLMExtractionStrategy
from crawl4ai import LLMConfig

class ValidationResult(BaseModel):
    title: str = Field(description="The name of the fragrance product")
    price: float = Field(description="The numeric price of the product")
    url: str = Field(description="The absolute URL to the product. EXTRACT THIS EXACTLY from the markdown links. DO NOT INVENT OR GUESS URLS. If missing, leave empty.")
    is_match: bool = Field(description="True if the raw title is definitely the target brand and search term. False if it is a different brand or fragrance.")
    volume_ml: Optional[float] = Field(description="The volume in milliliters (ml). E.g. 100. If only oz is given, convert to ml (1 oz = 30 ml).")
    concentration: str = Field(description="The concentration of the fragrance (e.g. EDT, EDP, Parfum, Extrait). Use 'Unknown' if not specified.")
    sort_key: str = Field(description="The canonical name of the fragrance modified for alphabetical sorting (e.g. 'Le Male' -> 'Male, Le').")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0 that this matches the target fragrance.")
    validation_issues: list[str] = Field(description="Any issues found, such as missing volume, or uncertainty about the match.")
    is_dupe: bool = Field(description="True if this fragrance is a known clone, dupe, or 'inspired by' another designer fragrance. Example: Lattafa Asad is a dupe.", default=False)
    inspired_by: Optional[str] = Field(description="If is_dupe is true, the designer target fragrance this is cloning. Example: 'Dior Sauvage Elixir'.", default=None)

def get_llm_strategy(target_brand: str, search_term: str) -> LLMExtractionStrategy:
    prompt = f"""
    You are an expert fragrance data validator and extractor.
    Target Brand: {target_brand}
    Target Fragrance: {search_term}
    
    Task:
    Extract a list of fragrance products from the provided text/markdown.
    For each product:
    1. Extract title, price (as a float), and url. YOU MUST EXTRACT THE URL EXACTLY AS WRITTEN IN THE MARKDOWN LINKS. DO NOT HALLUCINATE OR INVENT URLS. IF THERE IS NO URL, LEAVE IT EMPTY.
    2. Determine if the Raw Scraped Title is actually the Target Fragrance. 
       - If it is a completely different brand, is_match MUST be false.
       - If it is a different fragrance line, is_match MUST be false.
    3. Extract the volume in ML.
    4. Extract the concentration (EDT, EDP, Parfum, Extrait).
    5. Generate a sort_key by stripping leading articles from the Target Fragrance.
    6. CLONE MAPPING: If the target fragrance is a known clone (e.g., from Lattafa, Armaf, Afnan), set is_dupe=True and set inspired_by to the name of the designer fragrance it clones.
    """
    
    return LLMExtractionStrategy(
        llm_config=LLMConfig(
            provider="openai/dolphin-llama3:latest",
            api_token="ollama",
            base_url="http://localhost:11434/v1"
        ),
        schema=ValidationResult.model_json_schema(),
        extraction_type="schema",
        instruction=prompt,
    )
