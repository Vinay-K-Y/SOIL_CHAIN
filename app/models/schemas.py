from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SoilScanRequest(BaseModel):
    farmer_id: str
    farm_location: str
    latitude: float
    longitude: float
    # IoT sensor readings (can be mocked for demo)
    ph: Optional[float] = None
    nitrogen: Optional[float] = None   # mg/kg
    phosphorus: Optional[float] = None # mg/kg
    potassium: Optional[float] = None  # mg/kg
    moisture: Optional[float] = None   # percentage

class SoilHealthScore(BaseModel):
    score: float = Field(..., ge=0, le=100, description="Soil health score 0-100")
    grade: str  # A, B, C, D
    ph_status: str
    nutrient_status: str
    microbiome_diversity: float
    carbon_sequestration_tons: float
    recommendations: list[str]

class SoilScanResponse(BaseModel):
    scan_id: str
    farmer_id: str
    farm_location: str
    timestamp: datetime
    soil_health: SoilHealthScore
    eligible_for_token: bool
    estimated_token_reward: float
    nft_metadata_uri: Optional[str] = None

class TokenMintRequest(BaseModel):
    scan_id:        str
    farmer_id:      str
    wallet_address: str
    token_amount:   Optional[float] = None   # actual amount from scan result

class TokenMintResponse(BaseModel):
    transaction_hash: str
    token_amount: float
    nft_certificate_id: str
    polygon_explorer_url: str

class MicrobiomeListingRequest(BaseModel):
    farmer_id: str
    farm_location: str
    soil_score: float
    available_quantity_kg: float
    price_per_month: float  # in INR
    description: str

class MicrobiomeListing(BaseModel):
    listing_id: str
    farmer_id: str
    farm_location: str
    soil_score: float
    available_quantity_kg: float
    price_per_month: float
    description: str
    created_at: datetime
    is_active: bool

class CarbonCreditListing(BaseModel):
    listing_id: str
    farmer_id: str
    token_amount: float
    price_per_token_inr: float
    total_value_inr: float
    co2_tons: float
    verified: bool
    created_at: datetime
