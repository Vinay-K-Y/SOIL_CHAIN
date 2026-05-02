"""
Water Carbon Efficiency Service
===============================
Calculates the Irrigation Carbon Efficiency Score (ICES).
Water is treated as a regulator of carbon capture efficiency, not a carbon source.
"""

from typing import Dict

# Optimal soil moisture ranges per crop
OPTIMAL_MOISTURE = {
    "rice": (0.6, 0.8),
    "wheat": (0.4, 0.6),
    "maize": (0.5, 0.7),
    "default": (0.4, 0.7)
}

def calculate_water_efficiency(water_used_liters: float, soil_moisture: float, ndvi_value: float, crop_type: str) -> Dict:
    """
    Computes ICES (Irrigation Carbon Efficiency Score).
    Now supports metadata for transparency.
    """
    # ... logic stays same ...
    moisture_range = OPTIMAL_MOISTURE.get(crop_type.lower(), OPTIMAL_MOISTURE["default"])
    min_opt, max_opt = moisture_range
    
    if min_opt <= soil_moisture <= max_opt:
        moisture_score = 1.0
    else:
        if soil_moisture < min_opt:
            deviation = min_opt - soil_moisture
        else:
            deviation = soil_moisture - max_opt
        moisture_score = max(0.0, 1.0 - deviation)
        
    if water_used_liters <= 0:
        efficiency = 0.0
    else:
        efficiency = ndvi_value / water_used_liters
        
    ices = efficiency * moisture_score
    ices = max(0.0, min(1.0, ices))
    
    return {
        "water_efficiency": round(efficiency, 6),
        "moisture_score": round(moisture_score, 4),
        "ices_score": round(ices, 6),
        "data_source": "user_input",
        "confidence_score": 0.7,
        "verification_status": "UNVERIFIED"
    }

def calculate_water_tokens(ices_score: float) -> float:
    """
    Converts ICES score into tokens.
    Formula: tokens = ices_score * 20
    """
    return round(ices_score * 20, 2)
