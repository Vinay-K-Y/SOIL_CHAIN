"""
Unified Token Engine Service
==============================
Unifies token calculations from Soil, Air, and Water modules.
Applies weighting factors to produce a single final token value.
"""

from typing import Dict

def calculate_total_tokens(soil_tokens: float, air_tokens: float, water_tokens: float) -> Dict[str, float]:
    """
    Applies the weighted formula to unify carbon tokens.
    
    Formula:
    total_tokens = (soil_tokens * 1.0) + (air_tokens * 0.7) + (water_tokens * 0.5)
    """
    total = (soil_tokens * 1.0) + (air_tokens * 0.7) + (water_tokens * 0.5)
    
    return {
        "soil_tokens": round(soil_tokens, 2),
        "air_tokens": round(air_tokens, 2),
        "water_tokens": round(water_tokens, 2),
        "total_tokens": round(total, 2)
    }
