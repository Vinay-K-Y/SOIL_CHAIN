import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.air_carbon import calculate_air_carbon, calculate_air_tokens, get_ndvi

def test_logic():
    print("--- Testing Air Carbon Logic ---")
    ndvi_start = 0.3
    ndvi_end = 0.7
    area = 10.0
    crop_type = "trees"
    
    results = calculate_air_carbon(ndvi_start, ndvi_end, area, crop_type)
    print(f"Inputs: NDVI {ndvi_start} -> {ndvi_end}, Area: {area}, Crop: {crop_type}")
    print(f"Results: {results}")
    
    tokens = calculate_air_tokens(results["air_carbon_captured"])
    print(f"Tokens: {tokens}")
    
    # Verify values
    # delta_ndvi = 0.4
    # biomass = 0.4 * 10 * 1.5 = 6.0
    # carbon = 6.0 * 0.45 = 2.7
    # tokens = 2.7 * 10 = 27.0
    
    assert tokens == 27.0
    print("Logic test passed!")

def test_ndvi_mock():
    print("\n--- Testing NDVI Mock ---")
    data = get_ndvi(12.9716, 77.5946, "2024-01-01", "2024-06-01")
    print(f"Mock NDVI data: {data}")
    assert "ndvi_start" in data
    assert "ndvi_end" in data
    print("NDVI mock test passed!")

if __name__ == "__main__":
    try:
        test_logic()
        test_ndvi_mock()
    except Exception as e:
        print(f"Test failed: {e}")
