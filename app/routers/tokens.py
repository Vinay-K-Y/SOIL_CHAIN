from fastapi import APIRouter, HTTPException
from app.models.schemas import TokenMintRequest, TokenMintResponse
import uuid

router = APIRouter()

@router.post("/mint", response_model=TokenMintResponse)
async def mint_soil_tokens(request: TokenMintRequest):
    """
    Mint SoilTokens (ERC-20) and NFT certificate (ERC-721) on Polygon Amoy.
    In production: calls smart contract via Web3.py / ethers.js.
    Token amount is based on CO2 sequestered — passed in from the scan result.
    """
    tx_hash = "0x" + uuid.uuid4().hex + uuid.uuid4().hex[:24]
    nft_id  = str(uuid.uuid4())

    # Use the token amount from the request (based on actual scan CO2 data)
    # Falls back to 4.2 only if not provided
    token_amount = request.token_amount if request.token_amount else 4.2

    return TokenMintResponse(
        transaction_hash     = tx_hash,
        token_amount         = token_amount,
        nft_certificate_id   = nft_id,
        # Fixed: Polygon Mumbai is deprecated — use Amoy testnet
        polygon_explorer_url = f"https://amoy.polygonscan.com/tx/{tx_hash}"
    )


@router.get("/balance/{wallet_address}")
async def get_token_balance(wallet_address: str):
    """
    Get SoilToken balance for a wallet.
    In production: calls ERC-20 balanceOf() on Polygon Amoy.
    """
    return {
        "wallet_address":          wallet_address,
        "soil_token_balance":      42.5,
        "token_value_inr":         42.5 * 2500,   # 1 token ≈ ₹2500
        "nft_certificates":        3,
        "total_co2_sequestered_tons": 42.5
    }


@router.get("/price")
async def get_token_price():
    """Get current SoilToken market price."""
    return {
        "price_inr":           2500,
        "price_usd":           30.12,
        "24h_change_percent":  2.3,
        "market_cap_inr":      12500000,
        "total_supply":        5000,
        "circulating_supply":  3200
    }
