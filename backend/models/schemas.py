from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class PriceObservationResponse(BaseModel):
    price_observation_id: str
    retailer_name: str
    currency_code: str
    price_amount: float
    source_url: str
    captured_at: datetime
    volume_ml: Optional[float] = None
    package_type: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class VariantResponse(BaseModel):
    variant_id: str
    volume_ml: float
    package_type: str
    prices: List[PriceObservationResponse] = []

    model_config = ConfigDict(from_attributes=True)

class CloneResponse(BaseModel):
    dna_id: str
    brand_name: str
    canonical_name: str
    image_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class FragranceResponse(BaseModel):
    dna_id: str
    brand_name: str
    canonical_name: str
    market_segment: str
    first_release_year: Optional[int] = None
    is_dupe: bool = False
    inspired_by: Optional[str] = None
    influencer_mentions: Optional[str] = None
    image_url: Optional[str] = None
    variants: List[VariantResponse] = []
    clones: List[CloneResponse] = []

    model_config = ConfigDict(from_attributes=True)

class AlertCreate(BaseModel):
    email: str
    dna_id: str
    target_price: float

class BrandResponse(BaseModel):
    name: str

class DealResponse(BaseModel):
    fragrance: FragranceResponse
    retailer_name: str
    original_price: float
    sale_price: float
    source_url: str
