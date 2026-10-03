from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Sequence, Any

from database import get_db
from models.schema import FragranceDNA, Brand, FragranceLine, FragranceProduct, ProductVariant, PriceObservation, Retailer, DNARelationship, FragranceAlert
from models.schemas import FragranceResponse, VariantResponse, PriceObservationResponse, CloneResponse, AlertCreate, BrandResponse, DealResponse
from redis_client import get_redis
from es_client import get_es
import json

router = APIRouter(prefix="/api")

from urllib.parse import urlparse
from scrapers.strict_matcher import is_url_valid_for_fragrance, clean_source_url

async def _build_fragrance_response(db: AsyncSession, dnas: Sequence[FragranceDNA]) -> List[FragranceResponse]:
    response_data = []
    
    for dna in dnas:
        brand_name = dna.origin_brand.name if dna.origin_brand else "Unknown Brand"
        
        line_stmt = select(FragranceLine).where(FragranceLine.dna_id == dna.dna_id)
        lines = (await db.execute(line_stmt)).scalars().all()
        
        variants_resp = []
        for line in lines:
            prod_stmt = select(FragranceProduct).where(FragranceProduct.line_id == line.line_id)
            products = (await db.execute(prod_stmt)).scalars().all()
            
            for prod in products:
                var_stmt = select(ProductVariant).where(ProductVariant.product_id == prod.product_id)
                variants = (await db.execute(var_stmt)).scalars().all()
                
                for var in variants:
                    price_stmt = (
                        select(PriceObservation, Retailer.name.label("retailer_name"), Retailer.website_url)
                        .outerjoin(Retailer, PriceObservation.retailer_id == Retailer.retailer_id)
                        .where(PriceObservation.variant_id == var.variant_id)
                    )
                    price_rows = (await db.execute(price_stmt)).all()
                    
                    # Keep unique store offers per URL / retailer, selecting latest capture
                    latest_prices = {}
                    for row in price_rows:
                        obs, r_name, r_url = row
                        if not obs.source_url:
                            continue
                        
                        # Validate that retailer link matches the target fragrance (prevents showing Viking under Aventus, Delina under Layton)
                        if not is_url_valid_for_fragrance(obs.source_url, str(dna.canonical_name), brand_name, bool(dna.is_dupe), price=float(obs.price_amount) if obs.price_amount else None):
                            continue
                            
                        clean_u = clean_source_url(obs.source_url)
                        if not r_name or r_name == "Unknown":
                            domain = urlparse(clean_u).netloc.lower().replace("www.", "")
                            r_name = domain.capitalize() if domain else "Retailer"
                        
                        key = (r_name, clean_u)
                        if key not in latest_prices or obs.captured_at > latest_prices[key][0].captured_at:
                            latest_prices[key] = (obs, r_name, clean_u)
                    
                    price_resps = []
                    var_any: Any = var
                    for (obs, r_name, clean_u) in latest_prices.values():
                        price_resps.append(PriceObservationResponse(
                            price_observation_id=str(obs.price_observation_id),
                            retailer_name=r_name,
                            currency_code=obs.currency_code,
                            price_amount=float(obs.price_amount),
                            source_url=clean_u,
                            captured_at=obs.captured_at,
                            volume_ml=float(var_any.volume_ml) if var_any.volume_ml else None,
                            package_type=str(var_any.package_type) if var_any.package_type else None
                        ))
                    
                    variants_resp.append(VariantResponse(
                        variant_id=str(var_any.variant_id),
                        volume_ml=float(var_any.volume_ml),
                        package_type=str(var_any.package_type),
                        prices=price_resps
                    ))
                    
        # Fetch clones
        clones_resp = []
        rel_stmt = (
            select(DNARelationship, FragranceDNA, Brand)
            .join(FragranceDNA, DNARelationship.source_dna_id == FragranceDNA.dna_id)
            .join(Brand, FragranceDNA.origin_brand_id == Brand.brand_id)
            .where(DNARelationship.target_dna_id == dna.dna_id)
        )
        rel_rows = (await db.execute(rel_stmt)).all()
        for rel, clone_dna_raw, clone_brand_raw in rel_rows:
            clone_dna: Any = clone_dna_raw
            clone_brand: Any = clone_brand_raw
            clones_resp.append(CloneResponse(
                dna_id=str(clone_dna.dna_id),
                brand_name=str(clone_brand.name),
                canonical_name=str(clone_dna.canonical_name),
                image_url=clone_dna.image_url
            ))
                    
        dna_any: Any = dna
        response_data.append(FragranceResponse(
            dna_id=str(dna_any.dna_id),
            brand_name=brand_name,
            canonical_name=str(dna_any.canonical_name),
            market_segment=str(dna_any.market_segment.value if hasattr(dna_any.market_segment, 'value') else dna_any.market_segment),
            first_release_year=int(dna_any.first_release_year) if dna_any.first_release_year is not None else None,
            is_dupe=bool(dna_any.is_dupe),
            inspired_by=str(dna_any.inspired_by) if dna_any.inspired_by else None,
            influencer_mentions=str(dna_any.influencer_mentions) if dna_any.influencer_mentions else None,
            image_url=str(dna_any.image_url) if dna_any.image_url else None,
            variants=variants_resp,
            clones=clones_resp
        ))
        
    return response_data

FEATURED_POPULAR_NAMES = [
    "Aventus",
    "Baccarat Rouge 540",
    "Angels' Share",
    "Layton",
    "Tobacco Vanille",
    "Sauvage Elixir",
    "Detour Noir",
    "Club De Nuit Intense Man",
    "Khamrah",
    "Asad",
    "9pm",
    "The Tux",
    "Club De Nuit Untold"
]

@router.get("/trending", response_model=List[FragranceResponse])
@router.get("/newest", response_model=List[FragranceResponse])
async def get_trending(db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    # Check cache first
    cached = await redis.get("trending_v3")
    if cached:
        return [FragranceResponse.model_validate(c) for c in json.loads(cached)]
        
    # Fetch curated popular flagship fragrances first
    stmt = (
        select(FragranceDNA)
        .options(selectinload(FragranceDNA.origin_brand))
        .where(FragranceDNA.canonical_name.in_(FEATURED_POPULAR_NAMES))
    )
    result = await db.execute(stmt)
    dnas = result.scalars().all()
    
    # Sort according to FEATURED_POPULAR_NAMES order
    dna_map = {str(d.canonical_name): d for d in dnas}
    sorted_dnas = [dna_map[name] for name in FEATURED_POPULAR_NAMES if name in dna_map]
    
    # If fewer than 8, fallback to any fragrances with images
    if len(sorted_dnas) < 8:
        extra_stmt = (
            select(FragranceDNA)
            .options(selectinload(FragranceDNA.origin_brand))
            .where(FragranceDNA.image_url.isnot(None))
            .limit(16)
        )
        extra_dnas = (await db.execute(extra_stmt)).scalars().all()
        for ed in extra_dnas:
            if ed.dna_id not in [sd.dna_id for sd in sorted_dnas]:
                sorted_dnas.append(ed)
    
    responses = await _build_fragrance_response(db, sorted_dnas[:16])
    
    # Store in cache for 30 minutes
    await redis.setex("trending_v3", 1800, json.dumps([r.model_dump(mode="json") for r in responses]))
    
    return responses

@router.get("/search", response_model=List[FragranceResponse])
async def search_fragrances(q: str = "", brand: str = "", db: AsyncSession = Depends(get_db), es=Depends(get_es)):
    if not q and not brand:
        return []
        
    must_clauses = []
    if q:
        must_clauses.append({
            "multi_match": {
                "query": q,
                "fields": ["canonical_name^2", "brand_name"],
                "fuzziness": "AUTO"
            }
        })
    if brand:
        must_clauses.append({
            "match": {
                "brand_name": brand
            }
        })
        
    es_query = {
        "query": {
            "bool": {
                "must": must_clauses
            }
        },
        "size": 10
    }
    
    res = await es.search(index="fragrances", body=es_query)
    hits = res["hits"]["hits"]
    
    if not hits:
        return []
        
    dna_ids = [hit["_id"] for hit in hits]
    
    # Fetch full details from DB based on ES results
    stmt = (
        select(FragranceDNA)
        .options(selectinload(FragranceDNA.origin_brand))
        .where(FragranceDNA.dna_id.in_(dna_ids))
    )
    result = await db.execute(stmt)
    dnas = result.scalars().all()
    
    # Preserve ES sorting order
    dna_dict = {str(dna.dna_id): dna for dna in dnas}
    sorted_dnas = [dna_dict[dna_id] for dna_id in dna_ids if dna_id in dna_dict]
    
    return await _build_fragrance_response(db, sorted_dnas)

@router.get("/fragrance/{dna_id}", response_model=FragranceResponse)
async def get_fragrance(dna_id: str, db: AsyncSession = Depends(get_db)):
    stmt = (
        select(FragranceDNA)
        .options(selectinload(FragranceDNA.origin_brand))
        .where(FragranceDNA.dna_id == dna_id)
    )
    result = await db.execute(stmt)
    dna = result.scalar_one_or_none()
    
    if not dna:
        raise HTTPException(status_code=404, detail="Fragrance not found")
        
    responses = await _build_fragrance_response(db, [dna])
    return responses[0]

@router.post("/alerts/subscribe")
async def subscribe_alert(alert: AlertCreate, db: AsyncSession = Depends(get_db)):
    # Check if fragrance exists
    result = await db.execute(select(FragranceDNA).where(FragranceDNA.dna_id == alert.dna_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Fragrance not found")
        
    new_alert = FragranceAlert(
        email=alert.email,
        dna_id=alert.dna_id,
        target_price=alert.target_price
    )
    db.add(new_alert)
    await db.commit()
    
    return {"message": "Alert created successfully"}

@router.get("/trending/influencers", response_model=List[FragranceResponse])
async def get_influencer_trending(db: AsyncSession = Depends(get_db)):
    stmt = (
        select(FragranceDNA)
        .options(selectinload(FragranceDNA.origin_brand))
        .where(FragranceDNA.influencer_mentions.isnot(None))
        .order_by(FragranceDNA.first_release_year.desc().nulls_last())
        .limit(20)
    )
    result = await db.execute(stmt)
    dnas = result.scalars().all()
    return await _build_fragrance_response(db, dnas)

@router.get("/brands", response_model=List[BrandResponse])
async def get_brands(db: AsyncSession = Depends(get_db)):
    stmt = select(Brand.name).order_by(Brand.name.asc())
    result = await db.execute(stmt)
    brands = result.scalars().all()
    return [{"name": b} for b in brands]

@router.get("/alerts/deals", response_model=List[DealResponse])
async def get_deals(db: AsyncSession = Depends(get_db)):
    # Fetch recent active deals (mocked or real)
    # We will query price observations marked as 'sale' or with a specific comment, or just fetch the newest ones.
    # For now, let's fetch the absolute lowest prices across the DB.
    # Actually, we can fetch prices < 100 for popular fragrances, or just random ones.
    # Let's just fetch the 10 most recent price observations.
    stmt = (
        select(PriceObservation, Retailer.name.label("retailer_name"), ProductVariant, FragranceDNA)
        .join(Retailer, PriceObservation.retailer_id == Retailer.retailer_id)
        .join(ProductVariant, PriceObservation.variant_id == ProductVariant.variant_id)
        .join(FragranceProduct, ProductVariant.product_id == FragranceProduct.product_id)
        .join(FragranceLine, FragranceProduct.line_id == FragranceLine.line_id)
        .join(FragranceDNA, FragranceLine.dna_id == FragranceDNA.dna_id)
        .options(selectinload(FragranceDNA.origin_brand))
        .order_by(PriceObservation.captured_at.desc())
        .limit(10)
    )
    result = await db.execute(stmt)
    rows = result.all()
    
    deals = []
    # Fetch fragrance responses for these DNAs
    if rows:
        dnas = [row[3] for row in rows]
        frag_responses = await _build_fragrance_response(db, dnas)
        frag_dict = {f.dna_id: f for f in frag_responses}
        
        for obs, r_name, var, dna in rows:
            deals.append(DealResponse(
                fragrance=frag_dict[str(dna.dna_id)],
                retailer_name=r_name,
                original_price=float(obs.price_amount) * 1.3, # mock original price
                sale_price=float(obs.price_amount),
                source_url=obs.source_url
            ))
            
    return deals
