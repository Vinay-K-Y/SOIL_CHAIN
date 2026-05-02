import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_endpoint(name, method, endpoint, payload=None):
    print(f"\n--- Testing {name} ---")
    url = f"{BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url)
        else:
            response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response Data:")
            print(json.dumps(response.json(), indent=2))
            return response.json()
        else:
            print(f"Error: {response.text}")
            return None
    except Exception as e:
        print(f"Request failed: {e}")
        return None

def run_tests():
    # 1. Root Endpoint
    test_endpoint("Root", "GET", "/")

    # 2. Air Carbon Test
    air_payload = {
        "ndvi_start": 0.3,
        "ndvi_end": 0.7,
        "area": 5.0,
        "crop_type": "wheat"
    }
    air_res = test_endpoint("Air Carbon", "POST", "/api/air-carbon/estimate", air_payload)

    # 3. Water Carbon Test
    water_payload = {
        "water_used_liters": 5000,
        "soil_moisture": 0.5,
        "ndvi_value": 0.7,
        "crop_type": "wheat"
    }
    water_res = test_endpoint("Water Carbon", "POST", "/api/water-carbon/estimate", water_payload)

    # 4. Soil Carbon Test
    soil_payload = {
        "farmer_id": "farmer_test_001",
        "farm_location": "Bangalore, India",
        "latitude": 12.9716,
        "longitude": 77.5946,
        "ph": 6.5,
        "nitrogen": 320,
        "phosphorus": 35,
        "potassium": 180,
        "moisture": 45
    }
    soil_res = test_endpoint("Soil Carbon", "POST", "/api/soil/scan", soil_payload)

    # 5. Integration (Total Carbon) Test
    if air_res and water_res and soil_res:
        total_payload = {
            "farmer_id": "farmer_test_001",
            "soil_scan": soil_payload,
            "air_carbon": air_payload,
            "water_carbon": water_payload
        }
        test_endpoint("Total Carbon Integration", "POST", "/api/integration/total-carbon", total_payload)
        
        # 6. Unified Minting Test
        mint_payload = {
            "farmer_id": "farmer_test_001",
            "wallet_address": "0x5084932142bA",
            "soil_input": soil_payload,
            "air_input": air_payload,
            "water_input": water_payload
        }
        test_endpoint("Unified Token Minting", "POST", "/api/tokens/mint", mint_payload)

if __name__ == "__main__":
    run_tests()
