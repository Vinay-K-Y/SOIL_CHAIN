"""
SoilChain Inference Test
==========================
Tests the trained model on a single image and returns a full
soil health analysis — exactly what the FastAPI backend calls.

Run:
  python test_inference.py --image path/to/soil_photo.jpg
  python test_inference.py --image soil.jpg --ph 6.5 --nitrogen 320 --phosphorus 38 --potassium 185 --moisture 48
"""

import argparse
import json
import numpy as np
import tensorflow as tf
from pathlib import Path
from PIL import Image

BASE_DIR   = Path(__file__).resolve().parent.parent
IMG_SIZE   = (224, 224)

# FIX: prefer final model → phase2 → phase1 (in that priority order)
def _find_model_path() -> Path:
    candidates = [
        BASE_DIR / "models" / "soil_classifier.h5",
        BASE_DIR / "models" / "best_model_phase2.h5",
        BASE_DIR / "models" / "best_model_phase1.h5",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None

MODEL_PATH        = _find_model_path()
CLASS_INDICES_PATH = BASE_DIR / "models" / "class_indices.json"


def load_model() -> tf.keras.Model:
    if MODEL_PATH is None:
        print("❌ No model found! Run: python train_model.py first")
        exit(1)
    print(f"✅ Loading model: {MODEL_PATH.name}")
    return tf.keras.models.load_model(str(MODEL_PATH))


def load_class_map() -> dict:
    """Load class indices from JSON and invert: {index → class_name}."""
    if not CLASS_INDICES_PATH.exists():
        print("⚠️  class_indices.json not found — using default class map")
        return {0: "degraded", 1: "healthy", 2: "moderate"}
    with open(CLASS_INDICES_PATH) as f:
        class_indices = json.load(f)
    # class_indices = {"degraded": 0, "healthy": 1, "moderate": 2}
    # Inverted:      {0: "degraded", 1: "healthy", 2: "moderate"}
    return {v: k for k, v in class_indices.items()}


def preprocess_image(image_path: str) -> np.ndarray:
    img = Image.open(image_path).convert("RGB").resize(IMG_SIZE)
    arr = np.array(img, dtype=np.float32) / 255.0
    return np.expand_dims(arr, axis=0)  # (1, 224, 224, 3)


def compute_soil_score(
    predicted_class: str, confidence: float,
    ph=None, nitrogen=None, phosphorus=None,
    potassium=None, moisture=None
) -> dict:
    """
    Converts CNN prediction into a 0–100 Soil Health Score.
    Sensor readings adjust the score by up to ±15 points.
    """
    base_scores = {"healthy": 83, "moderate": 60, "degraded": 32}
    base = base_scores[predicted_class]

    # Confidence adjustment: high confidence → score stays near base
    confidence_adj = (confidence - 0.5) * 10  # –5 to +5
    score = base + confidence_adj

    sensor_boost = 0
    sensor_notes = []

    if ph is not None:
        if 6.0 <= ph <= 7.5:   sensor_boost += 3
        elif ph < 5.5 or ph > 8.0:
            sensor_boost -= 3
            sensor_notes.append(f"pH {ph} is outside optimal range (6.0–7.5)")

    if nitrogen is not None:
        if 280 <= nitrogen <= 560:  sensor_boost += 4
        elif nitrogen < 140:
            sensor_boost -= 4
            sensor_notes.append("Very low nitrogen — apply compost or green manure")

    if phosphorus is not None:
        if 25 <= phosphorus <= 50:  sensor_boost += 3
        elif phosphorus < 10:
            sensor_boost -= 3
            sensor_notes.append("Low phosphorus — apply bone meal or rock phosphate")

    if potassium is not None:
        if 120 <= potassium <= 250: sensor_boost += 3
        elif potassium < 60:
            sensor_boost -= 3
            sensor_notes.append("Very low potassium — apply wood ash or greensand")

    if moisture is not None:
        if 40 <= moisture <= 60:    sensor_boost += 2
        elif moisture < 25 or moisture > 75:
            sensor_boost -= 2
            sensor_notes.append("Moisture out of range — check irrigation or drainage")

    final_score = round(min(100, max(0, score + sensor_boost)), 1)

    grade = (
        "A" if final_score >= 80 else
        "B" if final_score >= 65 else
        "C" if final_score >= 50 else "D"
    )

    eligible     = final_score >= 80
    carbon_tons  = round((final_score / 100) * 4.0, 2)
    token_reward = round(carbon_tons * 2, 2) if eligible else 0.0

    if not sensor_notes:
        default_recs = {
            "healthy":  ["Maintain current practices", "Consider cover cropping between seasons"],
            "moderate": ["Increase organic matter input", "Test for specific micronutrient deficiencies"],
            "degraded": ["Apply compost at 5 tons/acre", "Plant nitrogen-fixing cover crops", "Avoid tilling — use no-till methods"],
        }
        sensor_notes = default_recs[predicted_class]

    return {
        "soil_health_score":                  final_score,
        "grade":                              grade,
        "predicted_class":                    predicted_class,
        "confidence":                         round(confidence * 100, 1),
        "carbon_sequestration_tons_per_year": carbon_tons,
        "eligible_for_soil_token":            eligible,
        "estimated_token_reward":             token_reward,
        "recommendations":                    sensor_notes,
    }


def run_inference(
    image_path: str,
    ph=None, nitrogen=None, phosphorus=None,
    potassium=None, moisture=None
):
    model     = load_model()
    class_map = load_class_map()

    print(f"\n🔍 Analysing: {image_path}")
    img_array = preprocess_image(image_path)

    predictions    = model.predict(img_array, verbose=0)[0]
    predicted_idx  = int(np.argmax(predictions))
    predicted_class = class_map[predicted_idx]
    confidence     = float(predictions[predicted_idx])

    # Show raw probabilities for transparency
    print("\n📊 Raw class probabilities:")
    for i, prob in enumerate(predictions):
        label = class_map.get(i, f"class_{i}")
        bar   = "█" * int(prob * 20)
        print(f"  {label:<10} {prob:.4f}  {bar}")

    result = compute_soil_score(
        predicted_class, confidence,
        ph, nitrogen, phosphorus, potassium, moisture
    )

    print("\n" + "=" * 52)
    print("  🌱  SOILCHAIN SOIL ANALYSIS RESULT")
    print("=" * 52)
    print(f"  Model Used        : {MODEL_PATH.name}")
    print(f"  Soil Health Score : {result['soil_health_score']} / 100  (Grade {result['grade']})")
    print(f"  AI Classification : {result['predicted_class'].upper()} ({result['confidence']}% confident)")
    print(f"  CO₂ Sequestration : {result['carbon_sequestration_tons_per_year']} tons/ha/yr")
    print(f"  Token Eligible    : {'✅ YES' if result['eligible_for_soil_token'] else '❌ NO  (score < 80)'}")
    if result["eligible_for_soil_token"]:
        print(f"  Token Reward      : {result['estimated_token_reward']} SOIL tokens")
    print("\n  📋 Recommendations:")
    for rec in result["recommendations"]:
        print(f"    • {rec}")
    print("=" * 52)
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SoilChain Soil Inference Test")
    parser.add_argument("--image",      required=True,  help="Path to soil image (jpg/png)")
    parser.add_argument("--ph",         type=float,     help="Soil pH value")
    parser.add_argument("--nitrogen",   type=float,     help="Nitrogen mg/kg")
    parser.add_argument("--phosphorus", type=float,     help="Phosphorus mg/kg")
    parser.add_argument("--potassium",  type=float,     help="Potassium mg/kg")
    parser.add_argument("--moisture",   type=float,     help="Moisture percentage")
    args = parser.parse_args()

    run_inference(
        args.image,
        ph=args.ph, nitrogen=args.nitrogen,
        phosphorus=args.phosphorus, potassium=args.potassium,
        moisture=args.moisture
    )
