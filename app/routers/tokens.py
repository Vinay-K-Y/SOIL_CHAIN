from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    TokenMintRequest, TokenMintResponse, TotalTokensResponse,
    UnifiedMintRequest, UnifiedMintResponse,
    AirCarbonResponse, WaterCarbonResponse
)
from app.services.soil_analysis import analyze_soil
from app.services.air_carbon import calculate_air_carbon, calculate_air_tokens
from app.services.water_carbon import calculate_water_efficiency, calculate_water_tokens
from app.services.token_engine import calculate_total_tokens as compute_weighted_tokens
from app.integrations.blockchain import mint_tokens_on_chain
from datetime import datetime
import uuid

router = APIRouter()

@router.post("/mint", response_model=UnifiedMintResponse)
async def mint_unified_tokens(request: UnifiedMintRequest):
    """
    Unifies Soil, Air, and Water token calculations and mints them as a single combined value.
    Now integrates with real blockchain and NDVI layers for verification.
    """
    try:
        # 1. Soil Token Calculation
        soil_res = analyze_soil(request.soil_input)
        soil_tokens = soil_res.estimated_token_reward
        
        # 2. Air Token Calculation (uses satellite proxy)
        ndvi_data = get_ndvi(request.soil_input.latitude, request.soil_input.longitude, "2024-01-01", "2024-06-01")
        air_results = calculate_air_carbon(
            ndvi_start=request.air_input.ndvi_start,
            ndvi_end=request.air_input.ndvi_end,
            area_hectares=request.air_input.area,
            crop_type=request.air_input.crop_type,
            metadata=ndvi_data
        )
        air_tokens = calculate_air_tokens(air_results["air_carbon_captured"])
        air_res = AirCarbonResponse(
            biomass_growth=air_results["biomass_growth"],
            air_carbon_captured=air_results["air_carbon_captured"],
            tokens=air_tokens,
            data_source=air_results["data_source"],
            confidence_score=air_results["confidence_score"],
            verification_status=air_results["verification_status"]
        )
        
        # 3. Water Token Calculation (uses manual input)
        water_results = calculate_water_efficiency(
            water_used_liters=request.water_input.water_used_liters,
            soil_moisture=request.water_input.soil_moisture,
            ndvi_value=request.water_input.ndvi_value,
            crop_type=request.water_input.crop_type
        )
        water_tokens = calculate_water_tokens(water_results["ices_score"])
        water_res = WaterCarbonResponse(
            water_efficiency=water_results["water_efficiency"],
            moisture_score=water_results["moisture_score"],
            ices_score=water_results["ices_score"],
            tokens=water_tokens,
            data_source=water_results["data_source"],
            confidence_score=water_results["confidence_score"],
            verification_status=water_results["verification_status"]
        )
        
        # 4. Weighted Total Calculation
        token_data = compute_weighted_tokens(soil_tokens, air_tokens, water_tokens)
        
        # 5. Real/Simulated Blockchain Minting
        bc_res = mint_tokens_on_chain(request.wallet_address, token_data["total_tokens"])
        
        return UnifiedMintResponse(
            farmer_id=request.farmer_id,
            transaction_hash=bc_res["transaction_hash"],
            soil_tokens=token_data["soil_tokens"],
            air_tokens=token_data["air_tokens"],
            water_tokens=token_data["water_tokens"],
            total_tokens=token_data["total_tokens"],
            nft_certificate_id=str(uuid.uuid4()),
            polygon_explorer_url=bc_res["explorer_url"],
            timestamp=datetime.utcnow(),
            verification_status="PARTIAL",
            blockchain_status=bc_res["blockchain_status"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/balance/{wallet_address}")
async def get_token_balance(wallet_address: str):
    """
    Get SoilToken balance for a wallet.
    In production: calls ERC-20 balanceOf() on Polygon Amoy.
    """
    return {
        "wallet_address":          wallet_address,
        "soil_token_balance":      42.5,
        "token_value_inr":         42.5 * 2500,   # 1 token ≈ ₹2500
        "nft_certificates":        3,
        "total_co2_sequestered_tons": 42.5
    }


@router.get("/price")
async def get_token_price():
    """Get current SoilToken market price."""
    return {
        "price_inr":           2500,
        "price_usd":           30.12,
        "24h_change_percent":  2.3,
        "market_cap_inr":      12500000,
        "total_supply":        5000,
        "circulating_supply":  3200
    }
