import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_unified_mint():
    print("--- Testing Unified Token Minting ---")
    
    payload = {
        "farmer_id": "farmer_unified_001",
        "wallet_address": "0x5084932142bA",
        "soil_input": {
            "farmer_id": "farmer_unified_001",
            "farm_location": "Mysuru, Karnataka",
            "latitude": 12.29,
            "longitude": 76.63,
            "ph": 6.5,
            "nitrogen": 320,
            "phosphorus": 38,
            "potassium": 185,
            "moisture": 48
        },
        "air_input": {
            "ndvi_start": 0.3,
            "ndvi_end": 0.7,
            "area": 5.0,
            "crop_type": "wheat"
        },
        "water_input": {
            "water_used_liters": 5000,
            "soil_moisture": 0.5,
            "ndvi_value": 0.7,
            "crop_type": "wheat"
        }
    }
    
    try:
        url = f"{BASE_URL}/tokens/mint"
        response = requests.post(url, json=payload)
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Unified Mint Response:")
            print(json.dumps(data, indent=2))
            
            # Weighted calculation check:
            # Soil: Score 100 -> 8.0 tokens (simulated/calculated)
            # Air: (0.7-0.3)*5*1.0 = 2.0 biomass -> 0.9 carbon -> 9.0 tokens
            # Water: (0.7/5000)*1.0 = 0.00014 ICES -> 0.0 tokens
            # Weighted: 8.0*1.0 + 9.0*0.7 + 0.0*0.5 = 8.0 + 6.3 + 0.0 = 14.3
            
            print(f"\nSoil Tokens: {data['soil_tokens']}")
            print(f"Air Tokens: {data['air_tokens']}")
            print(f"Water Tokens: {data['water_tokens']}")
            print(f"TOTAL TOKENS (Weighted): {data['total_tokens']}")
            
            expected_total = round(data['soil_tokens'] * 1.0 + data['air_tokens'] * 0.7 + data['water_tokens'] * 0.5, 2)
            assert data['total_tokens'] == expected_total
            print("\nWeighted formula verification successful!")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    test_unified_mint()
