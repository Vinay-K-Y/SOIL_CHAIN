"""
SoilChain Soil Router
=======================
Endpoints:
  POST /api/soil/scan              — sensor-only analysis
  POST /api/soil/scan-with-image   — CNN + sensor fusion (image upload)
  GET  /api/soil/history/{id}      — scan history for a farmer
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from app.models.schemas import SoilScanRequest, SoilScanResponse
from app.services.soil_analysis import analyze_soil
import uuid

router = APIRouter()


@router.post("/scan", response_model=SoilScanResponse)
async def scan_soil(request: SoilScanRequest):
    """
    Analyse soil health from IoT sensor data (no image).
    Returns a Soil Health Score + token eligibility.
    """
    try:
        return analyze_soil(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan-with-image", response_model=SoilScanResponse)
async def scan_soil_with_image(
    farmer_id:   str   = Form(...),
    farm_location: str = Form(...),
    latitude:    float = Form(...),
    longitude:   float = Form(...),
    ph:          float = Form(None),
    nitrogen:    float = Form(None),
    phosphorus:  float = Form(None),
    potassium:   float = Form(None),
    moisture:    float = Form(None),
    image: UploadFile = File(...)
):
    """
    Analyse soil health from a smartphone image + optional IoT sensor data.
    The image is passed through the MobileNetV2 CNN for visual classification.
    CNN result is fused with sensor readings (40% CNN / 60% sensors).
    """
    # Read image bytes and pass to CNN pipeline
    image_bytes = await image.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Image file is empty.")

    print(f"📷 Image received: {image.filename}  ({len(image_bytes):,} bytes)")

    request = SoilScanRequest(
        farmer_id     = farmer_id,
        farm_location = farm_location,
        latitude      = latitude,
        longitude     = longitude,
        ph            = ph,
        nitrogen      = nitrogen,
        phosphorus    = phosphorus,
        potassium     = potassium,
        moisture      = moisture,
    )

    try:
        return analyze_soil(request, image_bytes=image_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{farmer_id}")
async def get_scan_history(farmer_id: str):
    """
    Get all past soil scans for a farmer.
    In production: query MongoDB/PostgreSQL with farmer_id index.
    """
    return {
        "farmer_id":   farmer_id,
        "total_scans": 3,
        "scans": [
            {"scan_id": str(uuid.uuid4()), "date": "2025-01-15", "score": 72.5, "grade": "B"},
            {"scan_id": str(uuid.uuid4()), "date": "2025-03-20", "score": 78.0, "grade": "B"},
            {"scan_id": str(uuid.uuid4()), "date": "2025-06-10", "score": 83.5, "grade": "A"},
        ],
        "trend": "improving",
    }
