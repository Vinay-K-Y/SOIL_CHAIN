from fastapi import APIRouter, HTTPException
from app.models.schemas import MicrobiomeListingRequest, MicrobiomeListing, CarbonCreditListing
from datetime import datetime
import uuid

router = APIRouter()

microbiome_listings = []
carbon_credit_listings = []

# ── Track live state in memory ─────────────────────────
_listing_qty = {
    "listing_mys_001":  50,
    "listing_pune_002": 30,
    "listing_cbe_003":  75,
}
_sold_credits = set()

_FIXED_MICROBIOME = [
    {"listing_id":"listing_mys_001","farmer_id":"farmer_001","farm_location":"Mysuru, Karnataka","soil_score":91.5,"available_quantity_kg":50,"price_per_month":4500,"description":"Premium organic microbiome from 10-year no-till farm. High diversity bacteria culture, excellent for rice and wheat.","created_at":"2025-06-01T10:00:00","is_active":True},
    {"listing_id":"listing_pune_002","farmer_id":"farmer_002","farm_location":"Pune, Maharashtra","soil_score":85.2,"available_quantity_kg":30,"price_per_month":3200,"description":"Drought-resistant microbiome blend, perfect for dry regions. Proven 20% yield improvement in field trials.","created_at":"2025-06-05T08:30:00","is_active":True},
    {"listing_id":"listing_cbe_003","farmer_id":"farmer_003","farm_location":"Coimbatore, Tamil Nadu","soil_score":88.7,"available_quantity_kg":75,"price_per_month":5000,"description":"Nitrogen-fixing bacteria from certified organic farm. Reduces fertilizer dependency by 30%.","created_at":"2025-06-08T09:00:00","is_active":True},
]

_FIXED_CREDITS = [
    {"listing_id":"credit_mys_001","farmer_id":"farmer_001","token_amount":25.0,"price_per_token_inr":2400,"total_value_inr":60000,"co2_tons":25.0,"verified":True,"farm_location":"Mysuru, Karnataka","created_at":"2025-06-10T00:00:00"},
    {"listing_id":"credit_nash_002","farmer_id":"farmer_002","token_amount":10.0,"price_per_token_inr":2600,"total_value_inr":26000,"co2_tons":10.0,"verified":True,"farm_location":"Nashik, Maharashtra","created_at":"2025-06-12T00:00:00"},
    {"listing_id":"credit_cbe_003","farmer_id":"farmer_003","token_amount":40.0,"price_per_token_inr":2200,"total_value_inr":88000,"co2_tons":40.0,"verified":True,"farm_location":"Coimbatore, Tamil Nadu","created_at":"2025-06-14T00:00:00"},
]


@router.post("/microbiome/list", response_model=MicrobiomeListing)
async def create_microbiome_listing(request: MicrobiomeListingRequest):
    if request.soil_score < 80:
        raise HTTPException(status_code=400, detail="Soil score must be 80+ to list microbiomes.")
    listing = MicrobiomeListing(
        listing_id=str(uuid.uuid4()), farmer_id=request.farmer_id,
        farm_location=request.farm_location, soil_score=request.soil_score,
        available_quantity_kg=request.available_quantity_kg,
        price_per_month=request.price_per_month, description=request.description,
        created_at=datetime.utcnow(), is_active=True
    )
    microbiome_listings.append(listing)
    return listing


@router.get("/microbiome/listings")
async def get_microbiome_listings(min_score: float = 80.0, max_price: float = None):
    active = [l for l in microbiome_listings if l.soil_score >= min_score and l.is_active]
    if max_price:
        active = [l for l in active if l.price_per_month <= max_price]
    fixed_with_qty = []
    for l in _FIXED_MICROBIOME:
        item = dict(l)
        item["available_quantity_kg"] = _listing_qty.get(l["listing_id"], l["available_quantity_kg"])
        if item["available_quantity_kg"] > 0:
            fixed_with_qty.append(item)
    return {"total": len(active) + len(fixed_with_qty), "listings": [l.dict() for l in active] + fixed_with_qty}


@router.post("/microbiome/rent/{listing_id}")
async def rent_microbiome(listing_id: str, buyer_farmer_id: str, duration_months: int = 3):
    price = 4500
    for l in _FIXED_MICROBIOME:
        if l["listing_id"] == listing_id:
            price = l["price_per_month"]
            current_qty = _listing_qty.get(listing_id, l["available_quantity_kg"])
            if current_qty < 10:
                raise HTTPException(status_code=400, detail="Insufficient quantity available")
            _listing_qty[listing_id] = current_qty - 10
            break
    return {
        "rental_id": str(uuid.uuid4()), "listing_id": listing_id,
        "buyer_farmer_id": buyer_farmer_id, "duration_months": duration_months,
        "total_cost_inr": price * duration_months, "quantity_kg": 10,
        "remaining_qty": _listing_qty.get(listing_id, 0),
        "smart_contract_address": "0x" + uuid.uuid4().hex,
        "delivery_expected_days": 7, "status": "confirmed",
        "polygon_explorer_url": f"https://amoy.polygonscan.com/tx/0x{uuid.uuid4().hex}",
        "message": "Payment locked in smart contract. Microbiome delivered in 7 days via biochar packaging."
    }


@router.get("/carbon-credits")
async def get_carbon_credit_listings():
    available_fixed = [c for c in _FIXED_CREDITS if c["listing_id"] not in _sold_credits]
    available_user  = [c for c in carbon_credit_listings if c["listing_id"] not in _sold_credits]
    all_listings = available_user + available_fixed
    return {"total": len(all_listings), "listings": all_listings}


@router.post("/carbon-credits/list")
async def list_carbon_credits(farmer_id: str, token_amount: float,
                               price_per_token_inr: float, farm_location: str, scan_id: str):
    listing = {
        "listing_id": f"credit_{scan_id[:8]}", "farmer_id": farmer_id,
        "token_amount": token_amount, "price_per_token_inr": price_per_token_inr,
        "total_value_inr": token_amount * price_per_token_inr, "co2_tons": token_amount,
        "verified": True, "farm_location": farm_location,
        "created_at": datetime.utcnow().isoformat()
    }
    carbon_credit_listings.append(listing)
    return listing


@router.post("/carbon-credits/buy/{listing_id}")
async def buy_carbon_credits(listing_id: str, buyer_company: str, quantity_tokens: float):
    if listing_id in _sold_credits:
        raise HTTPException(status_code=400, detail="These credits have already been purchased")
    price_per_token = 2500
    for l in _FIXED_CREDITS + carbon_credit_listings:
        if l["listing_id"] == listing_id:
            price_per_token = l["price_per_token_inr"]
            break
    _sold_credits.add(listing_id)
    total = quantity_tokens * price_per_token
    tx_hash = "0x" + uuid.uuid4().hex
    return {
        "purchase_id": str(uuid.uuid4()), "listing_id": listing_id,
        "buyer_company": buyer_company, "tokens_purchased": quantity_tokens,
        "co2_offset_tons": quantity_tokens, "total_paid_inr": total,
        "farmer_receives_inr": round(total * 0.9, 2),
        "platform_fee_inr": round(total * 0.1, 2),
        "transaction_hash": tx_hash,
        "polygon_explorer_url": f"https://amoy.polygonscan.com/tx/{tx_hash}",
        "certificate_url": f"https://soilchain.io/certificates/{uuid.uuid4()}",
        "status": "completed",
        "message": f"NFT certificate issued on Polygon Amoy. Farmer receives ₹{round(total*0.9):,} (90%) directly."
    }
