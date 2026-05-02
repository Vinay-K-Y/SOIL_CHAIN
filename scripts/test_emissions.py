import requests
import json

BASE_URL = "http://127.0.0.1:8000/api"

def test_emissions_bridge():
    print("--- Testing Emission-to-Carbon Credit Bridge ---")
    
    test_cases = [
        {"name": "Small Emission (Factory)", "payload": {"event_name": "Small Factory", "co2_emissions": 500}},
        {"name": "Large Emission (War)", "payload": {"event_name": "Regional Conflict", "co2_emissions": 100000}},
        {"name": "Extreme Emission (City)", "payload": {"event_name": "Metropolis Annual", "co2_emissions": 1000000}}
    ]
    
    for case in test_cases:
        print(f"\nCase: {case['name']}")
        try:
            url = f"{BASE_URL}/emissions/estimate"
            response = requests.post(url, json=case['payload'])
            
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"Required: {data['credits_required']} tCO2")
                print(f"Available: {data['available_credits']} SOIL")
                print(f"Fulfillment: {data['fulfillment_ratio'] * 100}%")
                print(f"Status: {data['status']}")
            else:
                print(f"Error: {response.text}")
        except Exception as e:
            print(f"Request failed: {e}")

if __name__ == "__main__":
    test_emissions_bridge()
