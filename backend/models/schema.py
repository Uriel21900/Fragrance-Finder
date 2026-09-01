import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Date, Numeric, Text, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, ENUM, CITEXT
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# --- ENUMs ---
class FragranceMarketSegment(str, enum.Enum):
    designer = 'designer'
    niche = 'niche'
    clone = 'clone'
    indie = 'indie'
    celebrity = 'celebrity'
    private_label = 'private_label'

class FragranceGenderMarketing(str, enum.Enum):
    masculine = 'masculine'
    feminine = 'feminine'
    unisex = 'unisex'
    genderless = 'genderless'

class RelationType(str, enum.Enum):
    inspired_by = 'inspired_by'
    clone_of = 'clone_of'
    dupe_of = 'dupe_of'
    reinterpretation_of = 'reinterpretation_of'
    flanker_of = 'flanker_of'
    reformulation_of = 'reformulation_of'

class PriceCondition(str, enum.Enum):
    new = 'new'
    tester = 'tester'
    used = 'used'
    decant = 'decant'
    sample = 'sample'

class NoteStage(str, enum.Enum):
    top = 'top'
    heart = 'heart'
    base = 'base'
    accord = 'accord'

# --- Models ---
class Brand(Base):
    __tablename__ = 'brand'
    brand_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(CITEXT, nullable=False)
    normalized_name = Column(Text, nullable=False, unique=True)
    country_code = Column(String(2))
    website_url = Column(Text)
    founded_year = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class FragranceDNA(Base):
    __tablename__ = 'fragrance_dna'
    dna_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_name = Column(Text, nullable=False)
    normalized_name = Column(Text, nullable=False)
    sort_key = Column(Text, nullable=True)
    origin_brand_id = Column(UUID(as_uuid=True), ForeignKey('brand.brand_id'))
    market_segment = Column(ENUM(FragranceMarketSegment, name='fragrance_market_segment'), nullable=False)
    first_release_year = Column(Integer)
    canonical_description = Column(Text)
    is_original_dna = Column(Boolean, nullable=False, default=True)
    is_dupe = Column(Boolean, nullable=False, default=False, server_default='false')
    inspired_by = Column(Text, nullable=True)
    influencer_mentions = Column(Text)
    image_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    origin_brand = relationship("Brand", foreign_keys=[origin_brand_id])

    __table_args__ = (UniqueConstraint('origin_brand_id', 'normalized_name', name='uq_dna_identity'),)

class FragranceLine(Base):
    __tablename__ = 'fragrance_line'
    line_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    brand_id = Column(UUID(as_uuid=True), ForeignKey('brand.brand_id'), nullable=False)
    dna_id = Column(UUID(as_uuid=True), ForeignKey('fragrance_dna.dna_id'), nullable=False)
    name = Column(Text, nullable=False)
    normalized_name = Column(Text, nullable=False)
    release_year = Column(Integer)
    discontinued_year = Column(Integer)
    marketing_gender = Column(ENUM(FragranceGenderMarketing, name='fragrance_gender_marketing'))
    description = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (UniqueConstraint('brand_id', 'normalized_name', name='uq_line_per_brand'),)

class Concentration(Base):
    __tablename__ = 'concentration'
    concentration_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(CITEXT, nullable=False, unique=True)
    display_name = Column(Text, nullable=False)
    sort_order = Column(Integer, nullable=False)
    min_oil_pct = Column(Numeric(5, 2))
    max_oil_pct = Column(Numeric(5, 2))

class FragranceProduct(Base):
    __tablename__ = 'fragrance_product'
    product_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    line_id = Column(UUID(as_uuid=True), ForeignKey('fragrance_line.line_id'), nullable=False)
    concentration_id = Column(UUID(as_uuid=True), ForeignKey('concentration.concentration_id'))
    formulation_version = Column(Text, nullable=False, default='original')
    release_year = Column(Integer)
    discontinued_year = Column(Integer)
    perfumer_credit_text = Column(Text)
    is_limited_edition = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (UniqueConstraint('line_id', 'concentration_id', 'formulation_version', name='uq_product_formula'),)

class ProductVariant(Base):
    __tablename__ = 'product_variant'
    variant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), ForeignKey('fragrance_product.product_id'), nullable=False)
    volume_ml = Column(Numeric(8, 2), nullable=False)
    package_type = Column(Text, nullable=False, default='spray')
    barcode = Column(Text, unique=True)
    sku = Column(Text)
    is_refill = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)

    __table_args__ = (UniqueConstraint('product_id', 'volume_ml', 'package_type', 'is_refill', name='uq_variant'),)

class DNARelationship(Base):
    __tablename__ = 'dna_relationship'
    dna_relationship_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_dna_id = Column(UUID(as_uuid=True), ForeignKey('fragrance_dna.dna_id'), nullable=False)
    target_dna_id = Column(UUID(as_uuid=True), ForeignKey('fragrance_dna.dna_id'), nullable=False)
    relationship_type = Column(ENUM(RelationType, name='relation_type'), nullable=False)
    similarity_score = Column(Numeric(5, 4))
    confidence_score = Column(Numeric(5, 4), nullable=False, default=0.50)
    evidence_url = Column(Text)
    evidence_note = Column(Text)
    asserted_by = Column(Text)
    valid_from = Column(Date)
    valid_to = Column(Date)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (UniqueConstraint('source_dna_id', 'target_dna_id', 'relationship_type', name='uq_dna_relationship'),)

class Note(Base):
    __tablename__ = 'note'
    note_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(CITEXT, nullable=False, unique=True)
    normalized_name = Column(Text, nullable=False, unique=True)
    note_family = Column(Text)
    description = Column(Text)

class ProductNote(Base):
    __tablename__ = 'product_note'
    product_id = Column(UUID(as_uuid=True), ForeignKey('fragrance_product.product_id', ondelete='CASCADE'), primary_key=True)
    note_id = Column(UUID(as_uuid=True), ForeignKey('note.note_id'), primary_key=True)
    stage = Column(ENUM(NoteStage, name='note_stage'), primary_key=True)
    prominence = Column(Integer)
    source_url = Column(Text)

class Retailer(Base):
    __tablename__ = 'retailer'
    retailer_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(CITEXT, nullable=False)
    normalized_name = Column(Text, nullable=False, unique=True)
    website_url = Column(Text)
    country_code = Column(String(2))
    is_marketplace = Column(Boolean, nullable=False, default=False)

# For PriceObservation, we omit SQLAlchemy's partition syntax for simplicity in prototyping
class PriceObservation(Base):
    __tablename__ = 'price_observation'
    price_observation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    variant_id = Column(UUID(as_uuid=True), ForeignKey('product_variant.variant_id'), nullable=False)
    retailer_id = Column(UUID(as_uuid=True), ForeignKey('retailer.retailer_id'))
    observed_at = Column(DateTime(timezone=True), primary_key=True, default=lambda: datetime.now(timezone.utc))
    currency_code = Column(String(3), nullable=False)
    price_amount = Column(Numeric(12, 2), nullable=False)
    shipping_amount = Column(Numeric(12, 2))
    tax_included = Column(Boolean)
    availability = Column(Text)
    condition = Column(ENUM(PriceCondition, name='price_condition'), nullable=False, default='new')
    source_url = Column(Text, nullable=False)
    source_hash = Column(Text)
    captured_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class FragranceAlert(Base):
    __tablename__ = 'fragrance_alert'
    alert_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(CITEXT, nullable=False)
    dna_id = Column(UUID(as_uuid=True), ForeignKey('fragrance_dna.dna_id', ondelete='CASCADE'), nullable=False)
    target_price = Column(Numeric(12, 2), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

class QuarantineReview(Base):
    __tablename__ = 'quarantine_reviews'
    review_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    clone_brand = Column(Text, nullable=False)
    clone_name = Column(Text, nullable=False)
    claimed_target = Column(Text, nullable=True)
    reason = Column(Text, nullable=False)
    confidence_score = Column(Numeric(5, 4), default=0.50)
    source_url = Column(Text, nullable=True)
    raw_payload = Column(Text, nullable=True)
    status = Column(Text, nullable=False, default='pending')
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

