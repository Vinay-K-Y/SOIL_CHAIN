import sys
import os

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.water_carbon import calculate_water_efficiency, calculate_water_tokens

def test_water_logic():
    print("--- Testing Water Carbon Logic ---")
    
    # Test case 1: Optimal moisture
    water_used = 100.0
    soil_moisture = 0.7  # optimal for rice
    ndvi = 0.8
    crop = "rice"
    
    results = calculate_water_efficiency(water_used, soil_moisture, ndvi, crop)
    print(f"Test 1 (Optimal): {results}")
    # efficiency = 0.8 / 100 = 0.008
    # moisture_score = 1.0
    # ICES = 0.008 * 1.0 = 0.008
    assert results["ices_score"] == 0.008
    
    # Test case 2: Suboptimal moisture (below)
    soil_moisture = 0.5 # rice optimal is 0.6-0.8
    results = calculate_water_efficiency(water_used, soil_moisture, ndvi, crop)
    print(f"Test 2 (Below Optimal): {results}")
    # moisture_score = 1.0 - (0.6 - 0.5) = 0.9
    # ICES = 0.008 * 0.9 = 0.0072
    assert results["ices_score"] == 0.0072
    
    # Test case 3: Suboptimal moisture (above)
    soil_moisture = 0.9 # rice optimal is 0.6-0.8
    results = calculate_water_efficiency(water_used, soil_moisture, ndvi, crop)
    print(f"Test 3 (Above Optimal): {results}")
    # moisture_score = 1.0 - (0.9 - 0.8) = 0.9
    # ICES = 0.008 * 0.9 = 0.0072
    assert results["ices_score"] == 0.0072
    
    # Token calculation
    tokens = calculate_water_tokens(0.008)
    print(f"Tokens for ICES 0.008: {tokens}")
    # tokens = 0.008 * 20 = 0.16
    assert tokens == 0.16
    
    print("Water logic tests passed!")

if __name__ == "__main__":
    try:
        test_water_logic()
    except Exception as e:
        print(f"Test failed: {e}")
