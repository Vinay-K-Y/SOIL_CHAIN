from fastapi import APIRouter, HTTPException
from app.models.schemas import TotalCarbonRequest, TotalCarbonResponse
from app.services.soil_analysis import analyze_soil
from app.services.air_carbon import calculate_air_carbon, calculate_air_tokens
from app.services.water_carbon import calculate_water_efficiency, calculate_water_tokens
from app.services.token_engine import calculate_total_tokens as compute_weighted_tokens
from datetime import datetime

router = APIRouter()

@router.post("/total-carbon", response_model=TotalCarbonResponse)
async def get_total_carbon_report(request: TotalCarbonRequest):
    """
    Combined endpoint to calculate Soil, Air, and Water carbon/tokens in one go.
    Uses the weighted token engine for consistency.
    """
    try:
        # 1. Soil Carbon
        soil_res = analyze_soil(request.soil_scan)
        soil_tokens = soil_res.estimated_token_reward
        
        # 2. Air Carbon
        air_results = calculate_air_carbon(
            ndvi_start=request.air_carbon.ndvi_start,
            ndvi_end=request.air_carbon.ndvi_end,
            area_hectares=request.air_carbon.area,
            crop_type=request.air_carbon.crop_type
        )
        air_tokens = calculate_air_tokens(air_results["air_carbon_captured"])
        from app.models.schemas import AirCarbonResponse
        air_res = AirCarbonResponse(
            biomass_growth=air_results["biomass_growth"],
            air_carbon_captured=air_results["air_carbon_captured"],
            tokens=air_tokens
        )
        
        # 3. Water Carbon Efficiency
        water_results = calculate_water_efficiency(
            water_used_liters=request.water_carbon.water_used_liters,
            soil_moisture=request.water_carbon.soil_moisture,
            ndvi_value=request.water_carbon.ndvi_value,
            crop_type=request.water_carbon.crop_type
        )
        water_tokens = calculate_water_tokens(water_results["ices_score"])
        from app.models.schemas import WaterCarbonResponse
        water_res = WaterCarbonResponse(
            water_efficiency=water_results["water_efficiency"],
            moisture_score=water_results["moisture_score"],
            ices_score=water_results["ices_score"],
            tokens=water_tokens
        )
        
        # Total (Weighted)
        token_data = compute_weighted_tokens(soil_tokens, air_tokens, water_tokens)
        
        return TotalCarbonResponse(
            farmer_id=request.farmer_id,
            soil_carbon=soil_res,
            air_carbon=air_res,
            water_carbon=water_res,
            total_tokens=token_data["total_tokens"],
            timestamp=datetime.utcnow()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
