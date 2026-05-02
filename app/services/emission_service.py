"""
Emission Service
================
Connects real-world carbon emissions to SoilChain's carbon credit generation system.
Converts emissions -> required credits -> match with farmer-generated credits.
"""

from typing import Dict

def calculate_required_credits(co2_tons: float) -> Dict:
    """
    1 carbon credit = 1 ton CO2
    """
    return {
        "co2_emissions": co2_tons,
        "credits_required": co2_tons,
        "unit": "tons CO2"
    }

def match_with_supply(credits_required: float, available_tokens: float) -> Dict:
    """
    Calculates the fulfillment ratio between required credits and available supply.
    """
    if credits_required <= 0:
        fulfillment = 1.0
    else:
        fulfillment = min(available_tokens / credits_required, 1.0)

    return {
        "credits_required": credits_required,
        "credits_available": available_tokens,
        "fulfillment_ratio": round(fulfillment, 4),
        "status": "FULLY_OFFSET" if fulfillment >= 1.0 else "PARTIAL_OFFSET"
    }
