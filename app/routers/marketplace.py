from fastapi import APIRouter, HTTPException
from app.models.schemas import MicrobiomeListingRequest, MicrobiomeListing, CarbonCreditListing
from datetime import datetime
import uuid

router = APIRouter()

# In-memory store for demo (use MongoDB/PostgreSQL in production)
microbiome_listings = []
carbon_credit_listings = []

# Fixed demo listing IDs so Buy/Rent actions work consistently across page reloads
_FIXED_MICROBIOME = [
    {
        "listing_id":            "listing_mys_001",
        "farmer_id":             "farmer_001",
        "farm_location":         "Mysuru, Karnataka",
        "soil_score":            91.5,
        "available_quantity_kg": 50,
        "price_per_month":       4500,
        "description":           "Premium organic microbiome from 10-year no-till farm. High diversity bacteria culture, excellent for rice and wheat.",
        "created_at":            "2025-06-01T10:00:00",
        "is_active":             True
    },
    {
        "listing_id":            "listing_pune_002",
        "farmer_id":             "farmer_002",
        "farm_location":         "Pune, Maharashtra",
        "soil_score":            85.2,
        "available_quantity_kg": 30,
        "price_per_month":       3200,
        "description":           "Drought-resistant microbiome blend, perfect for dry regions. Proven 20% yield improvement in field trials.",
        "created_at":            "2025-06-05T08:30:00",
        "is_active":             True
    },
    {
        "listing_id":            "listing_cbe_003",
        "farmer_id":             "farmer_003",
        "farm_location":         "Coimbatore, Tamil Nadu",
        "soil_score":            88.7,
        "available_quantity_kg": 75,
        "price_per_month":       5000,
        "description":           "Nitrogen-fixing bacteria from certified organic farm. Reduces fertilizer dependency by 30%.",
        "created_at":            "2025-06-08T09:00:00",
        "is_active":             True
    },
]

_FIXED_CREDITS = [
    {
        "listing_id":        "credit_mys_001",
        "farmer_id":         "farmer_001",
        "token_amount":      25.0,
        "price_per_token_inr": 2400,
        "total_value_inr":   60000,
        "co2_tons":          25.0,
        "verified":          True,
        "farm_location":     "Mysuru, Karnataka",
        "created_at":        "2025-06-10T00:00:00"
    },
    {
        "listing_id":        "credit_nash_002",
        "farmer_id":         "farmer_002",
        "token_amount":      10.0,
        "price_per_token_inr": 2600,
        "total_value_inr":   26000,
        "co2_tons":          10.0,
        "verified":          True,
        "farm_location":     "Nashik, Maharashtra",
        "created_at":        "2025-06-12T00:00:00"
    },
    {
        "listing_id":        "credit_cbe_003",
        "farmer_id":         "farmer_003",
        "token_amount":      40.0,
        "price_per_token_inr": 2200,
        "total_value_inr":   88000,
        "co2_tons":          40.0,
        "verified":          True,
        "farm_location":     "Coimbatore, Tamil Nadu",
        "created_at":        "2025-06-14T00:00:00"
    },
]


@router.post("/microbiome/list", response_model=MicrobiomeListing)
async def create_microbiome_listing(request: MicrobiomeListingRequest):
    """
    Farmer lists their healthy soil microbiomes for rent.
    Only farms with score >= 80 can list.
    """
    if request.soil_score < 80:
        raise HTTPException(
            status_code=400,
            detail="Soil score must be 80+ to list microbiomes. Improve your soil health first!"
        )

    listing = MicrobiomeListing(
        listing_id             = str(uuid.uuid4()),
        farmer_id              = request.farmer_id,
        farm_location          = request.farm_location,
        soil_score             = request.soil_score,
        available_quantity_kg  = request.available_quantity_kg,
        price_per_month        = request.price_per_month,
        description            = request.description,
        created_at             = datetime.utcnow(),
        is_active              = True
    )
    microbiome_listings.append(listing)
    return listing


@router.get("/microbiome/listings")
async def get_microbiome_listings(min_score: float = 80.0, max_price: float = None):
    """
    Browse available microbiome listings. Filter by score and price.
    Returns user-created listings first, then fixed demo listings.
    """
    active = [l for l in microbiome_listings if l.soil_score >= min_score and l.is_active]
    if max_price:
        active = [l for l in active if l.price_per_month <= max_price]

    # Merge user listings with fixed demo listings
    all_listings = [l.dict() for l in active] + _FIXED_MICROBIOME
    return {"total": len(all_listings), "listings": all_listings}


@router.post("/microbiome/rent/{listing_id}")
async def rent_microbiome(listing_id: str, buyer_farmer_id: str, duration_months: int = 3):
    """
    Rent a microbiome. Smart contract handles payment escrow in production.
    """
    # Find price from fixed or dynamic listings
    price = 4500  # default
    for l in _FIXED_MICROBIOME:
        if l["listing_id"] == listing_id:
            price = l["price_per_month"]
            break

    return {
        "rental_id":               str(uuid.uuid4()),
        "listing_id":              listing_id,
        "buyer_farmer_id":         buyer_farmer_id,
        "duration_months":         duration_months,
        "total_cost_inr":          price * duration_months,
        "smart_contract_address":  "0x" + uuid.uuid4().hex,
        "delivery_expected_days":  7,
        "status":                  "confirmed",
        "polygon_explorer_url":    f"https://amoy.polygonscan.com/tx/0x{uuid.uuid4().hex}",
        "message": "Payment locked in smart contract. Microbiome delivered in 7 days via biochar packaging."
    }


@router.get("/carbon-credits")
async def get_carbon_credit_listings():
    """
    Browse carbon credits available for purchase by corporations.
    Returns fixed demo listings plus any user-minted credits.
    """
    all_listings = carbon_credit_listings + _FIXED_CREDITS
    return {"total": len(all_listings), "listings": all_listings}


@router.post("/carbon-credits/list")
async def list_carbon_credits(
    farmer_id: str,
    token_amount: float,
    price_per_token_inr: float,
    farm_location: str,
    scan_id: str
):
    """Farmer lists their minted SoilTokens as carbon credits for sale."""
    listing = {
        "listing_id":          f"credit_{scan_id[:8]}",
        "farmer_id":           farmer_id,
        "token_amount":        token_amount,
        "price_per_token_inr": price_per_token_inr,
        "total_value_inr":     token_amount * price_per_token_inr,
        "co2_tons":            token_amount,
        "verified":            True,
        "farm_location":       farm_location,
        "created_at":          datetime.utcnow().isoformat()
    }
    carbon_credit_listings.append(listing)
    return listing


@router.post("/carbon-credits/buy/{listing_id}")
async def buy_carbon_credits(listing_id: str, buyer_company: str, quantity_tokens: float):
    """
    Corporate buyer purchases carbon credits.
    Smart contract handles settlement on Polygon Amoy.
    """
    # Find price from fixed listings
    price_per_token = 2500
    for l in _FIXED_CREDITS:
        if l["listing_id"] == listing_id:
            price_per_token = l["price_per_token_inr"]
            break

    tx_hash = "0x" + uuid.uuid4().hex
    return {
        "purchase_id":          str(uuid.uuid4()),
        "listing_id":           listing_id,
        "buyer_company":        buyer_company,
        "tokens_purchased":     quantity_tokens,
        "co2_offset_tons":      quantity_tokens,
        "total_paid_inr":       quantity_tokens * price_per_token,
        "transaction_hash":     tx_hash,
        "polygon_explorer_url": f"https://amoy.polygonscan.com/tx/{tx_hash}",
        "certificate_url":      f"https://soilchain.io/certificates/{uuid.uuid4()}",
        "status":               "completed",
        "message":              "NFT certificate issued on Polygon Amoy. Farmer receives 90% directly."
    }
