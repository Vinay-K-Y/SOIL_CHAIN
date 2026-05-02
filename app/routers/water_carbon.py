from fastapi import APIRouter, HTTPException
from app.models.schemas import WaterCarbonRequest, WaterCarbonResponse
from app.services.water_carbon import calculate_water_efficiency, calculate_water_tokens

router = APIRouter()

@router.post("/estimate", response_model=WaterCarbonResponse)
async def estimate_water_carbon_efficiency(request: WaterCarbonRequest):
    """
    Estimate Irrigation Carbon Efficiency Score (ICES) and tokens.
    
    Water acts as a regulator of carbon capture efficiency rather than a source.
    """
    try:
        results = calculate_water_efficiency(
            water_used_liters=request.water_used_liters,
            soil_moisture=request.soil_moisture,
            ndvi_value=request.ndvi_value,
            crop_type=request.crop_type
        )
        
        tokens = calculate_water_tokens(results["ices_score"])
        
        return WaterCarbonResponse(
            water_efficiency=results["water_efficiency"],
            moisture_score=results["moisture_score"],
            ices_score=results["ices_score"],
            tokens=tokens
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
