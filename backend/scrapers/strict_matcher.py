import re
from urllib.parse import urlparse

# Common sibling / flanker disqualifiers for iconic houses
HOUSE_SIBLINGS = {
    "parfums de marly": [
        "delina", "pegasus", "herod", "byerley", "darley", "galloway",
        "carlisle", "sedley", "greenley", "althair", "oajan", "haltane",
        "valaya", "athalia", "oriana", "meliora", "cassili", "palatine",
        "kalan", "habdan", "godolphin", "akaster", "nisean", "hamdani"
    ],
    "creed": [
        "viking", "silver mountain water", "green irish tweed", "millesime imperial",
        "virgin island water", "royal oud", "delphinus", "centaurus", "queen of silk",
        "carmina", "wind flowers", "spring flower", "love in white", "love in black",
        "erofla", "himalaya", "original vetiver", "original santal", "bois du portugal",
        "royal mayfair", "royal water", "tabarome", "neroli sauvage", "acqua fiorentina",
        "fleurs de jardinia", "sublime vanille", "spice and wood", "pure white cologne"
    ],
    "tom ford": [
        "tobacco vanille", "oud wood", "lost cherry", "bitter peach", "soleil blanc",
        "black orchid", "grey vetiver", "ombre leather", "noir extreme", "tuscan leather",
        "neroli portofino", "fucking fabulous", "costa azzurra", "rose prick", "electric cherry",
        "cherry smoke", "ebene fume", "bois marocain", "vanille fatale", "beau de jour"
    ],
    "dior": [
        "sauvage", "fahrenheit", "dior homme", "eau sauvage", "poison", "hypnotic poison",
        "pure poison", "midnight poison", "jadore", "miss dior", "dune", "higher"
    ],
    "chanel": [
        "bleu de chanel", "allure homme sport", "allure homme", "egoiste", "platinum egoiste",
        "antaeus", "pour monsieur", "coco mademoiselle", "coco noir", "chance", "gabrielle",
        "no 5", "no 19", "cristalle"
    ],
    "xerjoff": [
        "naxos", "erba pura", "alexandria", "torino21", "torino22", "renaissance", "zefiro",
        "40 knots", "mefisto", "casamorati", "italica", "bouquet ideale", "lirica", "decas",
        "soprano", "opera", "acciento", "laylati", "muse", "more than words", "golden dalla"
    ],
    "maison francis kurkdjian": [
        "baccarat rouge 540", "grand soir", "oud satin mood", "gentle fluidity", "amyris",
        "aqua universalis", "aqua celestia", "aqua vitae", "724", "l'homme a la rose", "petit matin"
    ],
    "kilian": [
        "angels' share", "apple brandy", "roses on ice", "straight to heaven", "black phantom",
        "love don't be shy", "good girl gone bad", "vodka on the rocks", "intoxicated", "moonlight in heaven"
    ],
    "yves saint laurent": [
        "myslf", "libre", "black opium", "opium", "mon paris", "paris",
        "l'homme", "la nuit de l'homme", "kouros", "rive gauche", "body kouros",
        "jazz", "manifesto", "elle", "saharienne", "tuxedo", "babycat",
        "caban", "trench", "caftan", "blouse", "jumpsuit", "grain de poudre"
    ]
}

SAMPLE_DISQUALIFIERS = [
    "sample", "vial", "decant", "pocket spray", "travel spray", "mini",
    "rollerball", "atomizer", "oil 12 ml", "oil 6 ml", "perfume oil",
    "body oil", "shower gel", "deodorant", "aftershave", "lotion",
    "soap", "candle", "body spray", "mist", "hair mist", "set with round makeup bag"
]

CLONE_HOUSE_DISQUALIFIERS = [
    "banadirfragrance", "banadir", "inspired by", "our version of",
    "impression of", "dupe of", "type of", "clone of", "smells like",
    "twist of"
]

def clean_source_url(raw_url: str) -> str:
    """Strip tracking and predictive search query parameters from URL."""
    parsed = urlparse(raw_url)
    clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    return clean

def is_strict_match(
    candidate_title: str,
    candidate_url: str,
    candidate_price: float | None = None,
    target_brand: str = "",
    target_fragrance: str = "",
    is_dupe_target: bool = False,
    require_full_bottle: bool = True,
    **kwargs
) -> tuple[bool, str]:
    """
    Validates that a retailer product title and URL strictly match the target fragrance.
    Returns (is_valid, reason).
    """
    target_brand = target_brand or kwargs.get("query_brand", "")
    target_fragrance = target_fragrance or kwargs.get("query_name", "")
    if candidate_price is None and "price" in kwargs and kwargs["price"] is not None:
        try:
            candidate_price = float(kwargs["price"])
        except (ValueError, TypeError):
            candidate_price = None
    if "is_dupe" in kwargs:
        is_dupe_target = bool(kwargs["is_dupe"])

    title_lower = candidate_title.lower()
    parsed_url = urlparse(candidate_url)
    slug = parsed_url.path.lower()
    
    brand_lower = target_brand.lower()
    frag_lower = target_fragrance.lower()

    # Rule A2: Full Bottle Validation
    if require_full_bottle:
        for s_disq in SAMPLE_DISQUALIFIERS:
            if s_disq in title_lower or s_disq in slug:
                return False, f"Sample/mini size disqualified: '{s_disq}' in product"
        
        # Check volume tokens if present
        vol_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:ml|oz|fl\s*oz)", title_lower)
        if vol_match:
            val = float(vol_match.group(1))
            if "oz" in title_lower and val < 1.0: # under 30ml
                return False, f"Volume too small for full bottle: {val} oz"
            elif "ml" in title_lower and val < 30.0:
                return False, f"Volume too small for full bottle: {val} ml"

    # Clone check on authentic targets
    if not is_dupe_target:
        for c_disq in CLONE_HOUSE_DISQUALIFIERS:
            if c_disq in title_lower or c_disq in slug:
                return False, f"Clone/imitation phrase disqualified: '{c_disq}' in authentic search"

    # Brand matching
    # Aliases
    brand_aliases = {
        "parfums de marly": ["parfums de marly", "pdm", "marly"],
        "maison francis kurkdjian": ["maison francis kurkdjian", "mfk", "kurkdjian"],
        "yves saint laurent": ["yves saint laurent", "ysl", "saint laurent"],
        "tom ford": ["tom ford"],
        "creed": ["creed"],
        "chanel": ["chanel"],
        "dior": ["dior", "christian dior"],
        "xerjoff": ["xerjoff", "casamorati", "sospiro"],
        "kilian": ["kilian", "by kilian"]
    }
    
    target_aliases = brand_aliases.get(brand_lower, [brand_lower])
    brand_in_title = any(alias in title_lower for alias in target_aliases)
    brand_in_slug = any(alias.replace(" ", "-") in slug or alias.replace(" ", "") in slug for alias in target_aliases)
    
    # If brand is completely missing from both title and slug, reject
    if not brand_in_title and not brand_in_slug:
        return False, f"Brand '{target_brand}' not found in title or slug"

    # Fragrance Name matching:
    # 1. Primary fragrance name tokens (ignoring stop words)
    stop_words = {"de", "la", "le", "les", "du", "the", "for", "men", "women", "eau", "parfum", "toilette", "edp", "edt"}
    raw_tokens = [w for w in re.sub(r"[^a-z0-9 ]", " ", frag_lower).split() if w not in stop_words and len(w) > 2]
    
    # Handle single-letter or short 1-2 char names like "Y", "K", "H24"
    if not raw_tokens:
        raw_tokens = [w for w in re.sub(r"[^a-z0-9 ]", " ", frag_lower).split() if w not in stop_words]

    # Every significant distinctive token must be present in the title
    for tok in raw_tokens:
        if len(tok) <= 2:
            # Word boundary check for single letters/short tokens so 'y' matches ' Y ' and not 'berry'
            if not re.search(rf"\b{re.escape(tok)}\b", title_lower):
                return False, f"Required fragrance token '{tok}' missing from title '{candidate_title}'"
        else:
            if tok not in title_lower:
                return False, f"Required fragrance token '{tok}' missing from title '{candidate_title}'"

    primary_token = raw_tokens[0]
    primary_slug_cand = primary_token.replace("'", "")
    if len(primary_slug_cand) <= 2:
        # Word boundary in slug e.g. -y- or /y- or -y$
        if not re.search(rf"(?:^|[/-]){re.escape(primary_slug_cand)}(?:[/-]|$)", slug):
            return False, f"Primary token '{primary_slug_cand}' missing from URL slug '{slug}'"
    else:
        if primary_slug_cand not in slug:
            return False, f"Primary token '{primary_slug_cand}' missing from URL slug '{slug}'"

    # Negative Sibling / Flanker Filtering:
    # Check known sibling fragrances for this house
    for house, siblings in HOUSE_SIBLINGS.items():
        if house in brand_lower or any(alias in brand_lower for alias in target_aliases):
            for sib in siblings:
                # If the sibling is NOT part of the target fragrance name
                if sib not in frag_lower:
                    sib_clean = sib.replace(" ", "-")
                    # Check if sibling is in title or slug
                    # Use word boundary or hyphen boundary
                    if re.search(rf"\b{re.escape(sib)}\b", title_lower) or sib_clean in slug:
                        return False, f"Sibling fragrance conflict: '{sib}' found in title or slug"

    # Flanker strictness:
    # If target does NOT contain 'exclusif', reject 'exclusif' (e.g. Layton vs Layton Exclusif)
    if "exclusif" not in frag_lower and ("exclusif" in title_lower or "exclusif" in slug):
        return False, "Flanker conflict: 'exclusif' found when target is standard edition"
        
    # If target does NOT contain 'absolu', reject 'absolu' (e.g. Aventus vs Absolu Aventus)
    if "absolu" not in frag_lower and ("absolu" in title_lower or "absolu" in slug):
        return False, "Flanker conflict: 'absolu' found when target is standard edition"

    # If target does NOT contain 'cologne', reject 'cologne' when target is EDP/Parfum (e.g. Aventus vs Aventus Cologne)
    if "cologne" not in frag_lower and ("cologne" in title_lower or "-cologne" in slug) and "eau de cologne" not in title_lower:
        return False, "Flanker conflict: 'cologne' found when target is standard edition"

    # Price plausibility for full bottles of luxury / niche fragrances
    if require_full_bottle and not is_dupe_target and candidate_price is not None:
        niche_luxury_houses = ["creed", "parfums de marly", "tom ford", "xerjoff", "kilian", "maison francis kurkdjian", "roja"]
        if any(h in brand_lower for h in niche_luxury_houses):
            if candidate_price < 60.0:
                return False, f"Price ${candidate_price:.2f} too low for full authentic bottle of {target_brand}"
        designer_luxury_houses = ["dior", "chanel", "yves saint laurent", "hermes", "guerlain"]
        if any(h in brand_lower for h in designer_luxury_houses):
            if candidate_price < 40.0:
                return False, f"Price ${candidate_price:.2f} too low for full authentic bottle of {target_brand}"

    return True, "Verified exact fragrance match"


def is_url_valid_for_fragrance(
    url: str,
    frag_name: str,
    brand_name: str,
    is_dupe: bool = False,
    price: float | None = None
) -> bool:
    """Helper for endpoints and scheduled scrapers to validate URLs using strict matcher rules."""
    matched, _ = is_strict_match(
        candidate_title=url,
        candidate_url=url,
        candidate_price=price,
        target_brand=brand_name,
        target_fragrance=frag_name,
        is_dupe_target=is_dupe,
        require_full_bottle=False if price is None else True
    )
    return matched

