"""
Air Carbon Estimation Service
==============================
Estimates biomass growth and carbon capture using NDVI (Normalized Difference Vegetation Index)
as a proxy for vegetation growth.
"""

import random
from typing import Dict

# Crop factors for biomass estimation
CROP_FACTORS = {
    "rice": 1.2,
    "wheat": 1.0,
    "maize": 1.1,
    "trees": 1.5,
    "default": 1.0
}

from app.integrations.ndvi_real import get_real_ndvi

def calculate_air_carbon(ndvi_start: float, ndvi_end: float, area_hectares: float, crop_type: str, metadata: Dict = None) -> Dict:
    """
    Computes biomass growth and carbon captured based on NDVI change.
    Now supports metadata for transparency from the real satellite integration.
    """
    delta_ndvi = ndvi_end - ndvi_start
    delta_ndvi = max(0, delta_ndvi)
    
    crop_factor = CROP_FACTORS.get(crop_type.lower(), CROP_FACTORS["default"])
    biomass = delta_ndvi * area_hectares * crop_factor
    carbon = biomass * 0.45
    
    # Base response
    res = {
        "biomass_growth": round(biomass, 4),
        "air_carbon_captured": round(carbon, 4),
        "data_source": "satellite_proxy",
        "confidence_score": 0.65,
        "verification_status": "PARTIAL"
    }
    
    # Merge metadata if provided (from real NDVI fetch)
    if metadata:
        res.update({
            "data_source": metadata.get("data_source", res["data_source"]),
            "confidence_score": metadata.get("confidence_score", res["confidence_score"]),
            "verification_status": metadata.get("verification_status", res["verification_status"]),
            "satellite_metadata": metadata
        })
        
    return res

def get_ndvi(lat: float, lon: float, start_date: str, end_date: str) -> Dict:
    """
    Fetches NDVI values using the real integration layer.
    """
    return get_real_ndvi(lat, lon, start_date, end_date)

def calculate_air_tokens(carbon: float) -> float:
    """
    Converts captured carbon into tokens.
    """
    return round(carbon * 10, 2)
