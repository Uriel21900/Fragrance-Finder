export interface Price {
  price_observation_id: string;
  retailer_name: string;
  currency_code: string;
  price_amount: number;
  source_url: string;
  captured_at: string;
  volume_ml?: number;
  package_type?: string;
}

export interface FragranceVariant {
  variant_id: string;
  volume_ml: number;
  package_type: string;
  prices: Price[];
}

export interface Clone {
  dna_id: string;
  brand_name: string;
  canonical_name: string;
  image_url?: string;
}

export interface FragranceData {
  dna_id: string;
  brand_name: string;
  canonical_name: string;
  market_segment: string;
  gender?: string;
  first_release_year?: number;
  influencer_mentions?: string;
  is_dupe?: boolean;
  inspired_by?: string;
  image_url?: string;
  variants: FragranceVariant[];
  clones?: Clone[];
}

export interface BrandData {
  name: string;
}

export interface DealData {
  fragrance: FragranceData;
  retailer_name: string;
  original_price: number;
  sale_price: number;
  source_url: string;
}
