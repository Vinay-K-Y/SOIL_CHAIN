"""
SoilChain Soil Analysis Service
=================================
Handles soil health scoring using:
  1. CNN model (image-based classification) — NOW ACTIVE
  2. IoT sensor fusion (pH, NPK, moisture)
  3. Blended score (40% CNN + 60% sensors) + token eligibility
"""

import os
import uuid
import json
import numpy as np
from datetime import datetime

try:
    import tensorflow as tf
except ImportError:
    tf = None

try:
    import cv2
except ImportError:
    cv2 = None

from app.models.schemas import SoilHealthScore, SoilScanResponse, SoilScanRequest

# ── Load model + class map once at startup ─────────────────────────────────
_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

_MODEL_PATH  = os.path.join(_BASE, 'models', 'soil_classifier.h5')
_PHASE2_PATH = os.path.join(_BASE, 'models', 'best_model_phase2.h5')
_CLASS_IDX   = os.path.join(_BASE, 'models', 'class_indices.json')

# Load best available model: final > phase2 > None
_model = None
if tf is not None:
    if os.path.exists(_MODEL_PATH):
        _model = tf.keras.models.load_model(_MODEL_PATH)
        print("[INFO] CNN model loaded: soil_classifier.h5")
    elif os.path.exists(_PHASE2_PATH):
        _model = tf.keras.models.load_model(_PHASE2_PATH)
        print("[INFO] CNN model loaded: best_model_phase2.h5 (fine-tuned)")
    else:
        print("[WARN] No trained model found - using sensor-only scoring.")
else:
    print("[WARN] TensorFlow not installed - using sensor-only scoring.")

# Load class index mapping from JSON, invert to {index: class_name}
_class_map = {0: 'degraded', 1: 'healthy', 2: 'moderate'}  # safe fallback
if os.path.exists(_CLASS_IDX):
    with open(_CLASS_IDX) as f:
        _class_map = {v: k for k, v in json.load(f).items()}

IMG_SIZE = (224, 224)


# ── CNN Inference ──────────────────────────────────────────────────────────

def _preprocess_image_bytes(image_bytes: bytes) -> np.ndarray:
    """Decode raw bytes → normalised (1, 224, 224, 3) float32 array."""
    if cv2 is None:
        raise ImportError("OpenCV (cv2) is required for image processing.")
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Could not decode image — unsupported format or corrupted file.")
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = cv2.resize(img, IMG_SIZE).astype(np.float32) / 255.0
    return np.expand_dims(img, axis=0)  # (1, 224, 224, 3)


def run_cnn_inference(image_bytes: bytes) -> dict | None:
    """
    Run CNN on raw image bytes. Returns None if model not loaded.
    Returns: {predicted_class, confidence, all_probabilities}
    """
    if _model is None:
        return None
    arr  = _preprocess_image_bytes(image_bytes)
    probs = _model.predict(arr, verbose=0)[0]
    idx  = int(np.argmax(probs))
    return {
        "predicted_class":    _class_map[idx],
        "confidence":         float(probs[idx]),
        "all_probabilities":  {_class_map[i]: float(p) for i, p in enumerate(probs)},
    }


# ── Sensor Scoring ─────────────────────────────────────────────────────────

def calculate_soil_score(ph, nitrogen, phosphorus, potassium, moisture) -> dict:
    """
    Calculates a 0–100 sensor-based soil health score.
    Thresholds aligned with ICAR / FAO agronomic guidelines.
    """
    score = 0
    recommendations = []
    ph_status = "Unknown"

    # pH  (ideal 6.0–7.5)
    if 6.0 <= ph <= 7.5:
        score += 25; ph_status = "Optimal"
    elif 5.5 <= ph < 6.0 or 7.5 < ph <= 8.0:
        score += 15; ph_status = "Acceptable"
        recommendations.append("Adjust pH toward 6.5 — use lime (acidic soil) or sulfur (alkaline soil)")
    else:
        score += 5; ph_status = "Critical"
        recommendations.append("Urgent pH correction needed — soil is too acidic/alkaline for most crops")

    # Nitrogen  (ideal 280–560 mg/kg)
    if 280 <= nitrogen <= 560:
        score += 25
    elif 140 <= nitrogen < 280:
        score += 15
        recommendations.append("Low nitrogen — consider legume cover crops or compost application")
    else:
        score += 8
        recommendations.append("Critically low nitrogen — apply organic matter or green manure")

    # Phosphorus  (ideal 25–50 mg/kg)
    if 25 <= phosphorus <= 50:
        score += 20
    elif 10 <= phosphorus < 25:
        score += 12
        recommendations.append("Low phosphorus — apply bone meal or rock phosphate")
    else:
        score += 5
        recommendations.append("Very low phosphorus — mycorrhizal inoculants can improve uptake")

    # Potassium  (ideal 120–250 mg/kg)
    if 120 <= potassium <= 250:
        score += 20
    elif 60 <= potassium < 120:
        score += 12
        recommendations.append("Low potassium — apply wood ash or potassium sulfate")
    else:
        score += 5
        recommendations.append("Very low potassium — apply greensand or compost")

    # Moisture  (ideal 40–60%)
    if 40 <= moisture <= 60:
        score += 10
    elif 25 <= moisture < 40 or 60 < moisture <= 75:
        score += 6
        recommendations.append("Moisture suboptimal — consider mulching or drainage improvements")
    else:
        score += 2
        recommendations.append("Severe moisture imbalance — urgent irrigation or drainage needed")

    grade = "A" if score >= 80 else "B" if score >= 65 else "C" if score >= 50 else "D"
    nutrient_status_map = {
        "A": "Excellent — all nutrients well-balanced",
        "B": "Good — minor nutrient adjustments recommended",
        "C": "Fair — several nutrient deficiencies present",
        "D": "Poor — significant nutrient restoration needed",
    }
    if not recommendations:
        recommendations.append("Maintain current practices — your soil is thriving!")

    return {
        "score":                     round(score, 1),
        "grade":                     grade,
        "ph_status":                 ph_status,
        "nutrient_status":           nutrient_status_map[grade],
        "microbiome_diversity":      round(score / 100 * 8.5, 2),
        "carbon_sequestration_tons": round((score / 100) * 4.0, 3),
        "recommendations":           recommendations,
        "data_source":               "sensor_fusion",
        "confidence_score":          0.8,
        "verification_status":       "PARTIAL"
    }


def _blend_scores(cnn_result: dict, sensor_score: float) -> float:
    """
    Blend CNN visual score with IoT sensor score.
    Weights: 40% image-based CNN, 60% sensor readings.
    """
    base = {"healthy": 85, "moderate": 60, "degraded": 30}
    cnn_base  = base[cnn_result["predicted_class"]]
    conf_adj  = (cnn_result["confidence"] - 0.5) * 10   # ±5 pts for confidence
    cnn_score = min(100, max(0, cnn_base + conf_adj))
    return round(0.4 * cnn_score + 0.6 * sensor_score, 1)


# ── Main Analysis Pipeline ─────────────────────────────────────────────────

def analyze_soil(request: SoilScanRequest, image_bytes: bytes = None) -> SoilScanResponse:
    """
    Main soil analysis pipeline.

    Modes:
      - Image + sensors → CNN inference + sensor fusion (blended score)
      - Sensors only    → formula scoring
      - No inputs       → demo mode with simulated values
    """
    # Fill sensor values or simulate for demo
    ph         = request.ph         or round(np.random.uniform(5.5, 7.8), 1)
    nitrogen   = request.nitrogen   or round(np.random.uniform(100, 500), 1)
    phosphorus = request.phosphorus or round(np.random.uniform(10, 55),   1)
    potassium  = request.potassium  or round(np.random.uniform(60, 260),  1)
    moisture   = request.moisture   or round(np.random.uniform(25, 70),   1)

    # Sensor scoring — always computed
    score_data   = calculate_soil_score(ph, nitrogen, phosphorus, potassium, moisture)
    sensor_score = score_data["score"]

    # CNN inference — only if image bytes provided
    cnn_result = None
    if image_bytes is not None:
        try:
            cnn_result = run_cnn_inference(image_bytes)
        except Exception as e:
            print(f"⚠️  CNN inference failed ({e}) — falling back to sensor-only scoring")

    # Fuse CNN + sensor if image was processed
    if cnn_result is not None:
        blended               = _blend_scores(cnn_result, sensor_score)
        score_data["score"]   = blended
        g = "A" if blended >= 80 else "B" if blended >= 65 else "C" if blended >= 50 else "D"
        score_data["grade"]                     = g
        score_data["microbiome_diversity"]      = round(blended / 100 * 8.5, 2)
        score_data["carbon_sequestration_tons"] = round((blended / 100) * 4.0, 3)
        # Prepend CNN classification as first recommendation
        ai_label      = cnn_result["predicted_class"].upper()
        ai_confidence = round(cnn_result["confidence"] * 100, 1)
        score_data["recommendations"].insert(
            0, f"📷 AI visual analysis: {ai_label} soil ({ai_confidence}% confidence)"
        )

    soil_health        = SoilHealthScore(**score_data)
    scan_id            = str(uuid.uuid4())
    eligible           = soil_health.score >= 80
    estimated_reward   = round(soil_health.carbon_sequestration_tons * 2, 2) if eligible else 0.0
    nft_uri            = f"ipfs://QmSoilChain/{scan_id}" if eligible else None

    return SoilScanResponse(
        scan_id                = scan_id,
        farmer_id              = request.farmer_id,
        farm_location          = request.farm_location,
        timestamp              = datetime.utcnow(),
        soil_health            = soil_health,
        eligible_for_token     = eligible,
        estimated_token_reward = estimated_reward,
        nft_metadata_uri       = nft_uri,
    )
