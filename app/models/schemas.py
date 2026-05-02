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
    # Transparency Fields
    data_source: str = "user_input"
    confidence_score: float = 0.8
    verification_status: str = "UNVERIFIED"

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

class AirCarbonRequest(BaseModel):
    ndvi_start: float
    ndvi_end: float
    area: float
    crop_type: str

class AirCarbonResponse(BaseModel):
    biomass_growth: float
    air_carbon_captured: float
    tokens: float
    status: str = "success"
    # Transparency Fields
    data_source: str = "mock"
    confidence_score: float = 0.6
    verification_status: str = "UNVERIFIED"

class WaterCarbonRequest(BaseModel):
    water_used_liters: float
    soil_moisture: float
    ndvi_value: float
    crop_type: str

class WaterCarbonResponse(BaseModel):
    water_efficiency: float
    moisture_score: float
    ices_score: float
    tokens: float
    status: str = "success"
    # Transparency Fields
    data_source: str = "user_input"
    confidence_score: float = 0.7
    verification_status: str = "UNVERIFIED"

class TotalTokensResponse(BaseModel):
    soil_tokens: float
    air_tokens: float
    water_tokens: float
    total_tokens: float
    farmer_id: str

class TotalCarbonRequest(BaseModel):
    farmer_id: str
    soil_scan: SoilScanRequest
    air_carbon: AirCarbonRequest
    water_carbon: WaterCarbonRequest

class TotalCarbonResponse(BaseModel):
    farmer_id: str
    soil_carbon: SoilScanResponse
    air_carbon: AirCarbonResponse
    water_carbon: WaterCarbonResponse
    total_tokens: float
    timestamp: datetime

class UnifiedMintRequest(BaseModel):
    farmer_id: str
    wallet_address: str
    soil_input: SoilScanRequest
    air_input: AirCarbonRequest
    water_input: WaterCarbonRequest

class UnifiedMintResponse(BaseModel):
    farmer_id: str
    transaction_hash: str
    soil_tokens: float
    air_tokens: float
    water_tokens: float
    total_tokens: float
    nft_certificate_id: str
    polygon_explorer_url: str
    timestamp: datetime
    # Transparency Fields
    verification_status: str = "PARTIAL"
    blockchain_status: str = "SIMULATED"
