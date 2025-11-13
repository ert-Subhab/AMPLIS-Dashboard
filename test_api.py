"""
API Test Script
This will show us exactly what the HeyReach and Smartlead APIs are returning
"""

import requests
import yaml
import json

# Load config
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

print("=" * 60)
print("🔍 Testing API Endpoints")
print("=" * 60)

# Test HeyReach
print("\n1️⃣ Testing HeyReach API...")
print("-" * 60)

heyreach_key = config['heyreach']['api_key']
heyreach_base = config['heyreach']['base_url']

# Test campaigns endpoint
print(f"\nEndpoint: POST {heyreach_base}/api/public/campaign/GetAll")
print(f"Headers: X-API-KEY: {heyreach_key[:20]}...")

try:
    response = requests.post(
        f"{heyreach_base}/api/public/campaign/GetAll",
        headers={
            "X-API-KEY": heyreach_key,
            "Content-Type": "application/json",
            "Accept": "text/plain"
        },
        json={
            "offset": 0,
            "keyword": "",
            "statuses": [],
            "accountIds": [],
            "limit": 100
        },
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2)[:500])  # First 500 chars
    
except Exception as e:
    print(f"ERROR: {e}")

# Test LinkedIn accounts endpoint
print(f"\n\nEndpoint: POST {heyreach_base}/api/public/linkedin-account/GetAll")
try:
    response = requests.post(
        f"{heyreach_base}/api/public/linkedin-account/GetAll",
        headers={
            "X-API-KEY": heyreach_key,
            "Content-Type": "application/json",
            "Accept": "text/plain"
        },
        json={
            "offset": 0,
            "limit": 100
        },
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    print(json.dumps(response.json(), indent=2)[:500])  # First 500 chars
    
except Exception as e:
    print(f"ERROR: {e}")

# Test Smartlead
print("\n\n2️⃣ Testing Smartlead API...")
print("-" * 60)

smartlead_key = config['smartlead']['api_key']
smartlead_base = config['smartlead']['base_url']

print(f"\nEndpoint: GET {smartlead_base}/api/v1/campaigns?api_key=...")
try:
    response = requests.get(
        f"{smartlead_base}/api/v1/campaigns",
        params={"api_key": smartlead_key},
        timeout=30
    )
    
    print(f"Status Code: {response.status_code}")
    print(f"Response:")
    data = response.json()
    if isinstance(data, list):
        print(f"Got {len(data)} campaigns")
        if len(data) > 0:
            print(f"First campaign: {json.dumps(data[0], indent=2)[:500]}")
    else:
        print(json.dumps(data, indent=2)[:500])
    
except Exception as e:
    print(f"ERROR: {e}")

print("\n" + "=" * 60)
print("✅ Test Complete!")
print("=" * 60)
