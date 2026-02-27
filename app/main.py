"""
SoilChain FastAPI Backend
==========================
Run: uvicorn main:app --reload --port 8000

Install deps first:
  pip install fastapi uvicorn python-multipart tensorflow pydantic pymongo
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.routers import soil, tokens, marketplace

app = FastAPI(
    title="SoilChain API",
    description="Blockchain-Verified Soil Health Marketplace — AI + Web3",
    version="1.0.0"
)

# CORS must be added before routes and static mounts
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # In production: restrict to your domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(soil.router,        prefix="/api/soil",        tags=["Soil Scan"])
app.include_router(tokens.router,      prefix="/api/tokens",      tags=["SoilTokens"])
app.include_router(marketplace.router, prefix="/api/marketplace", tags=["Marketplace"])

# Serve the frontend HTML app at /app
_BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.get("/app")
def serve_app():
    html_path = os.path.join(_BASE_DIR, "..", "soilchain_app.html")
    if not os.path.exists(html_path):
        html_path = os.path.join(_BASE_DIR, "soilchain_app.html")
    return FileResponse(html_path)


@app.get("/")
def root():
    return {
        "project": "SoilChain",
        "status":  "live",
        "app":     "Open http://127.0.0.1:8000/app in your browser",
        "docs":    "/docs",
        "endpoints": {
            "scan":        "POST /api/soil/scan",
            "scan_image":  "POST /api/soil/scan-with-image",
            "mint":        "POST /api/tokens/mint",
            "marketplace": "GET  /api/marketplace/microbiome/listings",
            "carbon":      "GET  /api/marketplace/carbon-credits",
        }
    }


@app.get("/health")
def health():
    return {"status": "ok"}
