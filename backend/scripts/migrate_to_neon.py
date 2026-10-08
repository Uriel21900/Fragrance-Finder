import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select, text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.schema import (
    Base, Brand, FragranceDNA, Concentration, FragranceLine, 
    FragranceProduct, ProductVariant, Retailer, PriceObservation, 
    DNARelationship
)

from dotenv import load_dotenv
load_dotenv("backend/.env")
load_dotenv(".env")

LOCAL_DB_URL = os.getenv("LOCAL_DATABASE_URL", "postgresql+asyncpg://user:password@localhost:5433/fragrance_finder")
raw_neon = os.getenv("DATABASE_URL", "")
if not raw_neon:
    raw_neon = "postgresql+asyncpg://dummy:dummy@localhost:5432/dummy"
if raw_neon.startswith("postgres://"):
    raw_neon = raw_neon.replace("postgres://", "postgresql+asyncpg://", 1)
elif raw_neon.startswith("postgresql://") and "+asyncpg" not in raw_neon:
    raw_neon = raw_neon.replace("postgresql://", "postgresql+asyncpg://", 1)
if "sslmode=require" in raw_neon:
    raw_neon = raw_neon.replace("sslmode=require", "ssl=require")

NEON_DB_URL = raw_neon

local_engine = create_async_engine(LOCAL_DB_URL, echo=False)
local_session = async_sessionmaker(local_engine, expire_on_commit=False)

neon_engine = create_async_engine(NEON_DB_URL, echo=False)
neon_session = async_sessionmaker(neon_engine, expire_on_commit=False)

async def migrate():
    print("=== MIGRATING DATA FROM LOCAL POSTGRES TO NEON CLOUD DATABASE ===")
    
    # 1. Create tables in Neon
    async with neon_engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS citext;"))
        print("Creating schema/tables in Neon...")
        await conn.run_sync(Base.metadata.create_all)
        print("Schema created successfully!")

    async with local_session() as src_sess:
        async with neon_session() as dest_sess:
            # Transfer Brands
            brands = (await src_sess.execute(select(Brand))).scalars().all()
            print(f"Transferring {len(brands)} Brands...")
            for b in brands:
                dest_sess.add(Brand(
                    brand_id=b.brand_id,
                    name=b.name,
                    normalized_name=b.normalized_name,
                    country_code=b.country_code,
                    website_url=b.website_url,
                    founded_year=b.founded_year
                ))
            await dest_sess.commit()

            # Transfer Concentrations
            concs = (await src_sess.execute(select(Concentration))).scalars().all()
            print(f"Transferring {len(concs)} Concentrations...")
            for c in concs:
                dest_sess.add(Concentration(
                    concentration_id=c.concentration_id,
                    code=c.code,
                    display_name=c.display_name,
                    sort_order=c.sort_order,
                    min_oil_pct=c.min_oil_pct,
                    max_oil_pct=c.max_oil_pct
                ))
            await dest_sess.commit()

            # Transfer FragranceDNAs
            dnas = (await src_sess.execute(select(FragranceDNA))).scalars().all()
            print(f"Transferring {len(dnas)} Fragrance DNAs...")
            for d in dnas:
                dest_sess.add(FragranceDNA(
                    dna_id=d.dna_id,
                    canonical_name=d.canonical_name,
                    normalized_name=d.normalized_name,
                    sort_key=d.sort_key,
                    origin_brand_id=d.origin_brand_id,
                    market_segment=d.market_segment,
                    first_release_year=d.first_release_year,
                    canonical_description=d.canonical_description,
                    is_original_dna=d.is_original_dna,
                    is_dupe=d.is_dupe,
                    inspired_by=d.inspired_by,
                    influencer_mentions=d.influencer_mentions,
                    image_url=d.image_url
                ))
            await dest_sess.commit()

            # Transfer FragranceLines
            lines = (await src_sess.execute(select(FragranceLine))).scalars().all()
            print(f"Transferring {len(lines)} Fragrance Lines...")
            for l in lines:
                dest_sess.add(FragranceLine(
                    line_id=l.line_id,
                    brand_id=l.brand_id,
                    dna_id=l.dna_id,
                    name=l.name,
                    normalized_name=l.normalized_name,
                    release_year=l.release_year,
                    discontinued_year=l.discontinued_year,
                    marketing_gender=l.marketing_gender,
                    description=l.description
                ))
            await dest_sess.commit()

            # Transfer FragranceProducts
            prods = (await src_sess.execute(select(FragranceProduct))).scalars().all()
            print(f"Transferring {len(prods)} Fragrance Products...")
            for p in prods:
                dest_sess.add(FragranceProduct(
                    product_id=p.product_id,
                    line_id=p.line_id,
                    concentration_id=p.concentration_id,
                    formulation_version=p.formulation_version,
                    release_year=p.release_year,
                    discontinued_year=p.discontinued_year,
                    perfumer_credit_text=p.perfumer_credit_text,
                    is_limited_edition=p.is_limited_edition,
                    is_active=p.is_active
                ))
            await dest_sess.commit()

            # Transfer ProductVariants
            vars = (await src_sess.execute(select(ProductVariant))).scalars().all()
            print(f"Transferring {len(vars)} Product Variants...")
            for v in vars:
                dest_sess.add(ProductVariant(
                    variant_id=v.variant_id,
                    product_id=v.product_id,
                    volume_ml=v.volume_ml,
                    package_type=v.package_type,
                    barcode=v.barcode,
                    sku=v.sku,
                    is_refill=v.is_refill,
                    is_active=v.is_active
                ))
            await dest_sess.commit()

            # Transfer Retailers
            retailers = (await src_sess.execute(select(Retailer))).scalars().all()
            print(f"Transferring {len(retailers)} Retailers...")
            for r in retailers:
                dest_sess.add(Retailer(
                    retailer_id=r.retailer_id,
                    name=r.name,
                    normalized_name=r.normalized_name,
                    website_url=r.website_url,
                    country_code=r.country_code,
                    is_marketplace=r.is_marketplace
                ))
            await dest_sess.commit()

            # Transfer DNARelationships (Clones)
            rels = (await src_sess.execute(select(DNARelationship))).scalars().all()
            print(f"Transferring {len(rels)} Clone DNA Relationships...")
            for rel in rels:
                dest_sess.add(DNARelationship(
                    dna_relationship_id=rel.dna_relationship_id,
                    source_dna_id=rel.source_dna_id,
                    target_dna_id=rel.target_dna_id,
                    relationship_type=rel.relationship_type,
                    similarity_score=rel.similarity_score,
                    confidence_score=rel.confidence_score,
                    evidence_url=rel.evidence_url,
                    evidence_note=rel.evidence_note,
                    asserted_by=rel.asserted_by,
                    valid_from=rel.valid_from,
                    valid_to=rel.valid_to
                ))
            await dest_sess.commit()

            # Transfer PriceObservations in batches of 500
            prices = (await src_sess.execute(select(PriceObservation))).scalars().all()
            print(f"Transferring {len(prices)} Price Observations...")
            batch_size = 500
            for i in range(0, len(prices), batch_size):
                batch = prices[i:i + batch_size]
                for pr in batch:
                    dest_sess.add(PriceObservation(
                        price_observation_id=pr.price_observation_id,
                        variant_id=pr.variant_id,
                        retailer_id=pr.retailer_id,
                        observed_at=pr.observed_at,
                        price_amount=pr.price_amount,
                        currency_code=pr.currency_code,
                        shipping_amount=pr.shipping_amount,
                        tax_included=pr.tax_included,
                        availability=pr.availability,
                        condition=pr.condition,
                        source_url=pr.source_url,
                        source_hash=pr.source_hash,
                        captured_at=pr.captured_at
                    ))
                await dest_sess.commit()

    print("=== MIGRATION TO NEON COMPLETED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(migrate())
