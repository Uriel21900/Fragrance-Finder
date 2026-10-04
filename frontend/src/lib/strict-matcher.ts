/**
 * Strict Fragrance Matcher for Next.js API Routes (frontend/src/lib/strict-matcher.ts)
 * Ported from backend/scrapers/strict_matcher.py
 * Prevents cross-brand sibling mismatches (e.g. Delina for Layton, Viking for Aventus).
 */

export const HOUSE_SIBLINGS: Record<string, string[]> = {
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
};

export const SAMPLE_DISQUALIFIERS = [
  "sample", "vial", "decant", "pocket spray", "travel spray", "mini",
  "rollerball", "atomizer", "oil 12 ml", "oil 6 ml", "perfume oil",
  "body oil", "shower gel", "deodorant", "aftershave", "lotion",
  "soap", "candle", "body spray", "mist", "hair mist", "set with round makeup bag"
];

export function cleanSourceUrl(rawUrl: string): string {
  try {
    const parsed = new URL(rawUrl);
    return `${parsed.protocol}//${parsed.host}${parsed.pathname}`;
  } catch {
    return rawUrl.split("?")[0];
  }
}

export function isStrictMatch(
  candidateTitle: string,
  candidateUrl: string,
  candidatePrice?: number | null,
  targetBrand: string = "",
  targetFragrance: string = "",
  isDupeTarget: boolean = false,
  requireFullBottle: boolean = true,
  targetGender: string = ""
): boolean {
  let cleanTitle = candidateTitle.toLowerCase();
  let slug = candidateUrl.toLowerCase();
  try {
    const parsed = new URL(candidateUrl);
    slug = parsed.pathname.toLowerCase();
  } catch {
    slug = candidateUrl.toLowerCase().split("?")[0];
  }
  if (cleanTitle.startsWith("http://") || cleanTitle.startsWith("https://")) {
    try {
      cleanTitle = new URL(cleanTitle).pathname.toLowerCase();
    } catch {
      cleanTitle = cleanTitle.split("?")[0];
    }
  }

  const brandLower = targetBrand.toLowerCase();
  const fragLower = targetFragrance.toLowerCase();

  // Rule 0: Gender Specificity Check (prevent cross-gender mismatches like Aventus For Her appearing under Men's Aventus)
  const genderLower = targetGender.toLowerCase();
  const isTargetMasculine = genderLower === 'masculine' || genderLower === 'men' || genderLower === 'him' || (!genderLower && (fragLower.includes('pour homme') || fragLower.includes('for men') || fragLower === 'aventus' || fragLower === 'eros' || fragLower === 'spicebomb'));
  const isTargetFeminine = genderLower === 'feminine' || genderLower === 'women' || genderLower === 'her' || (!genderLower && (fragLower.includes('pour femme') || fragLower.includes('for women') || fragLower.includes('for her') || fragLower === 'flowerbomb' || fragLower === 'acqua di gioia'));

  const femaleTokens = [
    "for-her", "for-women", "for-woman", "pour-femme", "woman", "women",
    "femme", "ladies", "womens", "her-edp", "her-edt"
  ];
  const maleTokens = [
    "for-him", "for-men", "for-man", "pour-homme", "homme", "mens"
  ];

  if (isTargetMasculine) {
    for (const ft of femaleTokens) {
      const regex = new RegExp(`(?:^|[/-_\\s])${ft}(?:[/-_\\s]|$)`, "i");
      if (regex.test(slug) || regex.test(cleanTitle)) {
        return false;
      }
    }
  } else if (isTargetFeminine) {
    for (const mt of maleTokens) {
      const regex = new RegExp(`(?:^|[/-_\\s])${mt}(?:[/-_\\s]|$)`, "i");
      if (regex.test(slug) || regex.test(cleanTitle)) {
        return false;
      }
    }
  }

  // Rule 1: Full bottle checks
  if (requireFullBottle) {
    for (const disq of SAMPLE_DISQUALIFIERS) {
      if (cleanTitle.includes(disq) || slug.includes(disq)) {
        return false;
      }
    }
  }

  // Rule 3: Brand presence check
  const brandAliases: Record<string, string[]> = {
    "parfums de marly": ["pdm", "parfums de marly", "parfums-de-marly"],
    "maison francis kurkdjian": ["mfk", "francis kurkdjian", "kurkdjian", "maison francis kurkdjian"],
    "yves saint laurent": ["ysl", "yves saint laurent", "saint laurent"],
    "creed": ["creed"],
    "tom ford": ["tom ford", "tom-ford"],
    "dior": ["dior", "christian dior"],
    "chanel": ["chanel"],
    "xerjoff": ["xerjoff", "casamorati", "xj 1861"],
    "kilian": ["kilian", "by kilian"]
  };

  const targetAliases = brandAliases[brandLower] || [brandLower];
  const brandFound = targetAliases.some(alias => cleanTitle.includes(alias) || slug.includes(alias.replace(/ /g, "-")));
  const isSpecialTarget = (fragLower.includes('aventus') && (slug.includes('aventus') || cleanTitle.includes('aventus'))) ||
                          slug.includes('banadirfragrance') ||
                          cleanTitle.includes('banadirfragrance');

  if (!brandFound && !isDupeTarget && !isSpecialTarget) {
    return false;
  }

  // Rule 4: Fragrance name tokens check - MUST appear in cleanTitle or clean slug (NEVER query string!)
  const stopWords = new Set([
    "eau", "de", "parfum", "edp", "edt", "cologne", "for", "men", "women",
    "man", "woman", "spray", "natural", "pour", "homme", "femme", "flacon",
    "perfume", "extrait", "royal", "essence", "elixir", "by", "vaporisateur"
  ]);

  const rawTokens = fragLower
    .replace(/[^\w\s]/g, " ")
    .split(/\s+/)
    .filter(t => t.length > 0 && !stopWords.has(t));

  if (rawTokens.length === 0) {
    rawTokens.push(fragLower);
  }

  for (const tok of rawTokens) {
    if (tok.length <= 2) {
      // Word boundary check for single letters/short tokens (e.g. 'y' in YSL Y)
      const regex = new RegExp(`\\b${tok}\\b`, "i");
      const slugRegex = new RegExp(`(?:^|[/-])${tok}(?:[/-]|$)`, "i");
      if (!regex.test(cleanTitle) && !slugRegex.test(slug)) {
        return false;
      }
    } else {
      if (!cleanTitle.includes(tok) && !slug.includes(tok)) {
        return false;
      }
    }
  }

  const primaryToken = rawTokens[0];
  const primarySlug = primaryToken.replace(/'/g, "");
  if (primarySlug.length <= 2) {
    const slugRegex = new RegExp(`(?:^|[/-])${primarySlug}(?:[/-]|$)`, "i");
    if (!slugRegex.test(slug)) {
      return false;
    }
  } else {
    if (!slug.includes(primarySlug)) {
      return false;
    }
  }

  // Rule 5: Negative Sibling / Flanker Filtering
  for (const [house, siblings] of Object.entries(HOUSE_SIBLINGS)) {
    if (brandLower.includes(house) || targetAliases.some(a => brandLower.includes(a))) {
      for (const sib of siblings) {
        if (!fragLower.includes(sib)) {
          const sibSlug = sib.replace(/ /g, "-");
          const sibRegex = new RegExp(`\\b${sib}\\b`, "i");
          if (sibRegex.test(cleanTitle) || slug.includes(sibSlug)) {
            return false;
          }
        }
      }
    }
  }

  // Clone line flanker exclusions:
  if (fragLower.includes("untold")) {
    if (slug.includes("sillage") || slug.includes("intense") || slug.includes("milestone") || slug.includes("precieux") || slug.includes("iconic")) {
      return false;
    }
  }
  if (fragLower.includes("the tux")) {
    if (slug.includes("the-one") || slug.includes("salvo") || slug.includes("fire-place") || slug.includes("the-myth")) {
      return false;
    }
  }
  if (fragLower.includes("detour noir")) {
    if (slug.includes("amber-oud") || slug.includes("aqua-dubai")) {
      return false;
    }
  }
  if (fragLower.includes("asad") && !fragLower.includes("zanzibar")) {
    if (slug.includes("zanzibar") || slug.includes("amethyst") || slug.includes("qaed-al-fursan")) {
      return false;
    }
  }
  if (fragLower.includes("khamrah") && !fragLower.includes("dukhan") && !fragLower.includes("qahwa")) {
    if (slug.includes("dukhan") || slug.includes("qaed-al-fursan")) {
      return false;
    }
  }

  // Flanker conflicts
  if (!fragLower.includes("exclusif") && (cleanTitle.includes("exclusif") || slug.includes("exclusif"))) {
    return false;
  }
  if (!fragLower.includes("absolu") && (cleanTitle.includes("absolu") || slug.includes("absolu"))) {
    return false;
  }
  if (!fragLower.includes("cologne") && (cleanTitle.includes("cologne") || slug.includes("-cologne")) && !cleanTitle.includes("eau de cologne")) {
    return false;
  }

  // Rule 6: Price plausibility for authentic bottles
  if (requireFullBottle && !isDupeTarget && candidatePrice !== undefined && candidatePrice !== null) {
    const nicheHouses = ["creed", "parfums de marly", "tom ford", "xerjoff", "kilian", "maison francis kurkdjian", "roja"];
    if (nicheHouses.some(h => brandLower.includes(h))) {
      if (candidatePrice < 60.0 && !slug.includes("banadirfragrance")) {
        return false;
      }
    }
    const designerHouses = ["dior", "chanel", "yves saint laurent", "hermes", "guerlain"];
    if (designerHouses.some(h => brandLower.includes(h))) {
      if (candidatePrice < 40.0) {
        return false;
      }
    }
  }

  return true;
}
