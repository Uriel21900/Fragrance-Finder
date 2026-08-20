CREATE EXTENSION IF NOT EXISTS citext;
CREATE EXTENSION IF NOT EXISTS btree_gist;

CREATE TYPE fragrance_market_segment AS ENUM (
  'designer', 'niche', 'clone', 'indie', 'celebrity', 'private_label'
);

CREATE TYPE fragrance_gender_marketing AS ENUM (
  'masculine', 'feminine', 'unisex', 'genderless'
);

CREATE TYPE relation_type AS ENUM (
  'inspired_by',
  'clone_of',
  'dupe_of',
  'reinterpretation_of',
  'flanker_of',
  'reformulation_of'
);

CREATE TYPE price_condition AS ENUM (
  'new', 'tester', 'used', 'decant', 'sample'
);

CREATE TABLE brand (
  brand_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name                citext NOT NULL,
  normalized_name     text NOT NULL,
  country_code        char(2),
  website_url         text,
  founded_year        smallint CHECK (founded_year BETWEEN 1600 AND 2100),
  created_at          timestamptz NOT NULL DEFAULT now(),
  updated_at          timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT uq_brand_normalized_name UNIQUE (normalized_name)
);

-- The enduring olfactory concept / canonical scent identity.
CREATE TABLE fragrance_dna (
  dna_id                  uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  canonical_name          text NOT NULL,
  normalized_name         text NOT NULL,
  origin_brand_id         uuid REFERENCES brand(brand_id),
  market_segment          fragrance_market_segment NOT NULL,
  first_release_year      smallint CHECK (first_release_year BETWEEN 1800 AND 2100),
  canonical_description   text,
  is_original_dna         boolean NOT NULL DEFAULT true,
  created_at              timestamptz NOT NULL DEFAULT now(),
  updated_at              timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT uq_dna_identity UNIQUE (origin_brand_id, normalized_name)
);

-- A named commercial line / release family, e.g. "Dior Sauvage".
CREATE TABLE fragrance_line (
  line_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  brand_id             uuid NOT NULL REFERENCES brand(brand_id),
  dna_id               uuid NOT NULL REFERENCES fragrance_dna(dna_id),
  name                 text NOT NULL,
  normalized_name      text NOT NULL,
  release_year         smallint CHECK (release_year BETWEEN 1800 AND 2100),
  discontinued_year    smallint CHECK (
    discontinued_year IS NULL OR discontinued_year >= release_year
  ),
  marketing_gender     fragrance_gender_marketing,
  description          text,
  created_at           timestamptz NOT NULL DEFAULT now(),
  updated_at           timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT uq_line_per_brand UNIQUE (brand_id, normalized_name)
);

CREATE TABLE concentration (
  concentration_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  code                 citext NOT NULL UNIQUE, -- EDT, EDP, Parfum, Extrait, etc.
  display_name         text NOT NULL,
  sort_order           smallint NOT NULL,
  min_oil_pct          numeric(5,2),
  max_oil_pct          numeric(5,2),
  
  CONSTRAINT ck_concentration_range CHECK (
    min_oil_pct IS NULL OR max_oil_pct IS NULL OR min_oil_pct <= max_oil_pct
  )
);

-- One sellable formula/concentration under a line.
CREATE TABLE fragrance_product (
  product_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  line_id                 uuid NOT NULL REFERENCES fragrance_line(line_id),
  concentration_id        uuid REFERENCES concentration(concentration_id),
  formulation_version     text NOT NULL DEFAULT 'original',
  release_year            smallint CHECK (release_year BETWEEN 1800 AND 2100),
  discontinued_year       smallint CHECK (
    discontinued_year IS NULL OR discontinued_year >= release_year
  ),
  perfumer_credit_text    text,
  is_limited_edition      boolean NOT NULL DEFAULT false,
  is_active               boolean NOT NULL DEFAULT true,
  created_at              timestamptz NOT NULL DEFAULT now(),
  updated_at              timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT uq_product_formula UNIQUE (
    line_id, concentration_id, formulation_version
  )
);

-- Exact commercial package / SKU, e.g. 100 ml EDP spray.
CREATE TABLE product_variant (
  variant_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  product_id            uuid NOT NULL REFERENCES fragrance_product(product_id),
  volume_ml             numeric(8,2) NOT NULL CHECK (volume_ml > 0),
  package_type          text NOT NULL DEFAULT 'spray',
  barcode               text,
  sku                   text,
  is_refill             boolean NOT NULL DEFAULT false,
  is_active             boolean NOT NULL DEFAULT true,

  CONSTRAINT uq_variant UNIQUE (product_id, volume_ml, package_type, is_refill),
  CONSTRAINT uq_variant_barcode UNIQUE (barcode)
);

-- Original-to-clone graph mapping
CREATE TABLE dna_relationship (
  dna_relationship_id       uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  source_dna_id             uuid NOT NULL REFERENCES fragrance_dna(dna_id),
  target_dna_id             uuid NOT NULL REFERENCES fragrance_dna(dna_id),
  relationship_type         relation_type NOT NULL,
  similarity_score          numeric(5,4) CHECK (
    similarity_score IS NULL
    OR similarity_score BETWEEN 0 AND 1
  ),
  confidence_score          numeric(5,4) NOT NULL DEFAULT 0.50 CHECK (
    confidence_score BETWEEN 0 AND 1
  ),
  evidence_url              text,
  evidence_note             text,
  asserted_by               text,
  valid_from                date,
  valid_to                  date,
  created_at                timestamptz NOT NULL DEFAULT now(),
  updated_at                timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT ck_no_self_relationship CHECK (source_dna_id <> target_dna_id),
  CONSTRAINT ck_relationship_dates CHECK (
    valid_to IS NULL OR valid_from IS NULL OR valid_to >= valid_from
  ),
  CONSTRAINT uq_dna_relationship UNIQUE (
    source_dna_id, target_dna_id, relationship_type
  )
);

CREATE INDEX ix_dna_relationship_source
  ON dna_relationship (source_dna_id, relationship_type);

CREATE INDEX ix_dna_relationship_target
  ON dna_relationship (target_dna_id, relationship_type);

-- Track evidence for "inspired by" claims
CREATE TABLE dna_relationship_evidence (
  evidence_id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  dna_relationship_id      uuid NOT NULL
                           REFERENCES dna_relationship(dna_relationship_id)
                           ON DELETE CASCADE,
  source_type              text NOT NULL, -- brand, retailer, reviewer, editorial
  source_url               text,
  quoted_claim             text,
  submitted_by_user_id     uuid,
  reviewed_at              timestamptz,
  accepted                 boolean NOT NULL DEFAULT false,
  created_at               timestamptz NOT NULL DEFAULT now()
);

-- Notes and accords
CREATE TABLE note (
  note_id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name                   citext NOT NULL UNIQUE,
  normalized_name        text NOT NULL UNIQUE,
  note_family            text,  -- citrus, floral, woody, musk, gourmand
  description            text
);

CREATE TYPE note_stage AS ENUM ('top', 'heart', 'base', 'accord');

CREATE TABLE product_note (
  product_id             uuid NOT NULL REFERENCES fragrance_product(product_id)
                         ON DELETE CASCADE,
  note_id                uuid NOT NULL REFERENCES note(note_id),
  stage                  note_stage NOT NULL,
  prominence             smallint CHECK (prominence BETWEEN 1 AND 10),
  source_url             text,
  
  PRIMARY KEY (product_id, note_id, stage)
);

CREATE INDEX ix_product_note_note
  ON product_note (note_id, product_id);

-- Historical pricing and observations
CREATE TABLE retailer (
  retailer_id            uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name                   citext NOT NULL,
  normalized_name        text NOT NULL UNIQUE,
  website_url            text,
  country_code           char(2),
  is_marketplace         boolean NOT NULL DEFAULT false
);

CREATE TABLE price_observation (
  price_observation_id   uuid DEFAULT gen_random_uuid(),
  variant_id             uuid NOT NULL REFERENCES product_variant(variant_id),
  retailer_id            uuid REFERENCES retailer(retailer_id),
  observed_at            timestamptz NOT NULL DEFAULT now(),
  currency_code          char(3) NOT NULL,
  price_amount           numeric(12,2) NOT NULL CHECK (price_amount >= 0),
  shipping_amount        numeric(12,2) CHECK (
    shipping_amount IS NULL OR shipping_amount >= 0
  ),
  tax_included           boolean,
  availability           text,
  condition              price_condition NOT NULL DEFAULT 'new',
  source_url             text NOT NULL,
  source_hash            text,
  captured_at            timestamptz NOT NULL DEFAULT now(),

  -- Must include partition key in the composite primary key
  PRIMARY KEY (price_observation_id, observed_at)
) PARTITION BY RANGE (observed_at);

CREATE INDEX ix_price_observation_variant_time
  ON price_observation (variant_id, observed_at DESC);

CREATE INDEX ix_price_observation_retailer_time
  ON price_observation (retailer_id, observed_at DESC);

-- Example Partition
CREATE TABLE price_observation_2026_08
  PARTITION OF price_observation
  FOR VALUES FROM ('2026-08-01') TO ('2026-09-01');

-- Curated validity table for non-overlapping price intervals
CREATE TABLE variant_price_period (
  price_period_id         uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  variant_id              uuid NOT NULL REFERENCES product_variant(variant_id),
  retailer_id             uuid NOT NULL REFERENCES retailer(retailer_id),
  condition               price_condition NOT NULL DEFAULT 'new',
  currency_code           char(3) NOT NULL,
  price_amount            numeric(12,2) NOT NULL CHECK (price_amount >= 0),
  shipping_amount         numeric(12,2) CHECK (
    shipping_amount IS NULL OR shipping_amount >= 0
  ),
  valid_during            tstzrange NOT NULL,
  
  -- Foreign key requires both composite columns to map to the partitioned table
  derived_from_observation_id uuid,
  derived_from_observed_at timestamptz,

  CONSTRAINT ck_price_period_nonempty CHECK (NOT isempty(valid_during)),

  CONSTRAINT fk_price_period_observation 
    FOREIGN KEY (derived_from_observation_id, derived_from_observed_at) 
    REFERENCES price_observation(price_observation_id, observed_at),

  CONSTRAINT ex_variant_retailer_price_period
  EXCLUDE USING gist (
    variant_id WITH =,
    retailer_id WITH =,
    condition WITH =,
    currency_code WITH =,
    valid_during WITH &&
  )
);