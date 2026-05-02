from fastapi import APIRouter, HTTPException
from app.models.schemas import EmissionEstimateRequest, EmissionEstimateResponse
from app.services.emission_service import calculate_required_credits, match_with_supply
from app.services.token_engine import get_total_available_tokens

router = APIRouter()

@router.post("/estimate", response_model=EmissionEstimateResponse)
async def estimate_emission_offset(request: EmissionEstimateRequest):
    """
    Connect real-world carbon emissions to SoilChain's carbon credit supply.
    """
    try:
        # 1. Calculate required credits
        req_data = calculate_required_credits(request.co2_emissions)
        
        # 2. Fetch available supply (simulated from token engine)
        available_supply = get_total_available_tokens()
        
        # 3. Match supply with requirement
        match_data = match_with_supply(req_data["credits_required"], available_supply)
        
        return EmissionEstimateResponse(
            event=request.event_name,
            co2_emissions=request.co2_emissions,
            credits_required=match_data["credits_required"],
            available_credits=match_data["credits_available"],
            fulfillment_ratio=match_data["fulfillment_ratio"],
            status=match_data["status"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
