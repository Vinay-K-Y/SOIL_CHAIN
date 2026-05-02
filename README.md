# SoilChain Backend API

## Setup & Run

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Then open: http://localhost:8000/docs (Swagger UI — all endpoints interactive)

## Verifiable Carbon System (MRV Upgrade)

SoilChain has been upgraded to a **Digital MRV (Measurement, Reporting, and Verification)** system, ensuring transparency and trust in carbon credit generation.

### Key Features:
- **Unified Token Minting**: Integrates Soil, Air, and Water carbon capture into a single weighted token pipeline.
- **Weighted Formula**: `Total = (Soil * 1.0) + (Air * 0.7) + (Water * 0.5)` to prioritize long-term sequestration.
- **Transparency Metadata**: Every calculation returns a `data_source`, `confidence_score`, and `verification_status`.
- **Satellite NDVI Integration**: Real-world vegetation tracking using Sentinel Hub API with a robust proxy fallback.
- **Blockchain Trust Layers**: Support for both real Polygon Amoy minting and simulated demonstration modes.
- **ICES Score**: Irrigation Carbon Efficiency Score to track water-based carbon capture regulation.

## Project Structure

```
soilchain/
├── app/
│   ├── main.py                  # FastAPI app entry point
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   ├── routers/
│   │   ├── soil.py              # POST /api/soil/scan
│   │   ├── tokens.py            # POST /api/tokens/mint
│   │   └── marketplace.py      # Microbiome + Carbon Credit APIs
│   └── services/
│       └── soil_analysis.py     # AI scoring engine (plug in CNN here)
└── requirements.txt
```

## Key Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/soil/scan` | Analyze soil from sensor data |
| POST | `/api/soil/scan-with-image` | Analyze soil from image + sensors |
| GET  | `/api/soil/history/{farmer_id}` | Scan history |
| POST | `/api/tokens/mint` | Mint SoilTokens on Polygon |
| GET  | `/api/tokens/balance/{wallet}` | Token balance |
| GET  | `/api/marketplace/microbiome/listings` | Browse microbiome listings |
| POST | `/api/marketplace/microbiome/rent/{id}` | Rent a microbiome |
| GET  | `/api/marketplace/carbon-credits` | Browse carbon credits |
| POST | `/api/marketplace/carbon-credits/buy/{id}` | Buy carbon credits |

## Next Steps

1. **Plug in your CNN model** in `services/soil_analysis.py` — replace the formula with TensorFlow/PyTorch inference
2. **Connect MongoDB** for persistent scan history
3. **Integrate Web3.py** in `routers/tokens.py` for real Polygon transactions
4. **Add JWT auth** for farmer/corporate login
