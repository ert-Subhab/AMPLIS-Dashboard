#!/usr/bin/env python3
"""
Test script to identify working HeyReach API endpoints
"""

import requests
import yaml
import json

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def test_endpoints():
    """Test different endpoint variations"""
    config = load_config()
    if not config:
        print("Failed to load config.yaml")
        return
    
    api_key = config['heyreach']['api_key']
    base_url = config['heyreach']['base_url']
    
    print("=" * 70)
    print("HeyReach API Endpoint Tester")
    print("=" * 70)
    print(f"Base URL: {base_url}")
    print(f"API Key: {api_key[:20]}...")
    print("=" * 70)
    print()
    
    # Test different endpoint variations
    endpoints_to_test = {
        'linkedin_accounts': [
            "api/public/linkedin-account/GetAll",
            "api/public/linkedinAccount/GetAll",
            "api/public/linkedin_account/getAll",
            "api/v1/linkedin-account",
            "api/v1/linkedinAccount",
            "api/v1/accounts",
            "api/linkedin-account",
            "api/linkedinAccount",
            "api/accounts",
            "linkedin-account/GetAll",
            "api/public/accounts",
        ],
        'campaigns': [
            "api/public/campaign/GetAll",
            "api/public/campaign/getAll",
            "api/public/campaigns",
            "api/v1/campaign",
            "api/v1/campaigns",
            "api/campaign",
            "api/campaigns",
            "campaign/GetAll",
        ],
        'leads': [
            "api/public/lead/GetAll",
            "api/public/lead/getAll",
            "api/public/leads",
            "api/v1/lead",
            "api/v1/leads",
            "api/lead",
            "api/leads",
            "lead/GetAll",
        ]
    }
    
    # Header variations to test
    header_variations = [
        ("X-API-KEY", {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }),
        ("Authorization Bearer", {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }),
        ("api-key lowercase", {
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }),
        ("X-API-Key mixed case", {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }),
    ]
    
    request_data_templates = {
        'linkedin_accounts': {"offset": 0, "limit": 10},
        'campaigns': {"offset": 0, "keyword": "", "statuses": [], "accountIds": [], "limit": 10},
        'leads': {"offset": 0, "limit": 10, "keyword": "", "campaignIds": [], "linkedInAccountIds": [], "statuses": [], "tags": []}
    }
    
    successful_endpoints = {}
    
    for endpoint_type, endpoints in endpoints_to_test.items():
        print(f"\n{'=' * 70}")
        print(f"Testing {endpoint_type.upper()} endpoints")
        print(f"{'=' * 70}")
        
        request_data = request_data_templates[endpoint_type]
        found_working = False
        
        for header_name, headers in header_variations:
            if found_working:
                break
                
            print(f"\n  Testing with headers: {header_name}")
            
            for endpoint in endpoints:
                url = f"{base_url}/{endpoint}"
                try:
                    response = requests.post(
                        url,
                        headers=headers,
                        json=request_data,
                        timeout=10
                    )
                    
                    status_emoji = "✅" if response.status_code == 200 else "❌"
                    print(f"    {status_emoji} {endpoint}: Status {response.status_code}", end="")
                    
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            print(f" - SUCCESS!")
                            print(f"      Response structure: {type(data).__name__}")
                            if isinstance(data, dict):
                                print(f"      Keys: {list(data.keys())[:5]}")
                                if 'items' in data:
                                    print(f"      Items count: {len(data.get('items', []))}")
                                elif 'data' in data:
                                    print(f"      Data count: {len(data.get('data', [])) if isinstance(data.get('data'), list) else 'N/A'}")
                            elif isinstance(data, list):
                                print(f"      List length: {len(data)}")
                            
                            # Store successful endpoint
                            if endpoint_type not in successful_endpoints:
                                successful_endpoints[endpoint_type] = {
                                    'endpoint': endpoint,
                                    'headers': header_name,
                                    'headers_dict': headers
                                }
                            found_working = True
                            break
                        except json.JSONDecodeError:
                            print(f" - Invalid JSON response")
                    elif response.status_code == 401:
                        print(f" - Unauthorized (wrong auth)")
                    elif response.status_code == 403:
                        print(f" - Forbidden (auth issue)")
                    elif response.status_code == 404:
                        print(f" - Not Found")
                    elif response.status_code == 500:
                        print(f" - Server Error")
                        try:
                            error_text = response.text[:200]
                            print(f"      Error: {error_text}")
                        except:
                            pass
                    else:
                        print(f" - Status {response.status_code}")
                        try:
                            error_text = response.text[:200]
                            print(f"      Response: {error_text}")
                        except:
                            pass
                            
                except requests.exceptions.Timeout:
                    print(f"    ⏱️  {endpoint}: Timeout")
                except requests.exceptions.ConnectionError:
                    print(f"    🔌 {endpoint}: Connection Error")
                except Exception as e:
                    print(f"    ❌ {endpoint}: Error - {str(e)[:50]}")
        
        if not found_working:
            print(f"\n  ⚠️  No working endpoint found for {endpoint_type}")
    
    # Print summary
    print(f"\n{'=' * 70}")
    print("SUMMARY")
    print(f"{'=' * 70}")
    
    if successful_endpoints:
        print("\n✅ Working endpoints found:")
        for endpoint_type, info in successful_endpoints.items():
            print(f"  {endpoint_type}:")
            print(f"    Endpoint: {info['endpoint']}")
            print(f"    Headers: {info['headers']}")
    else:
        print("\n❌ No working endpoints found!")
        print("\nPossible reasons:")
        print("  1. API key is incorrect")
        print("  2. API endpoints have changed")
        print("  3. API requires different authentication")
        print("  4. API base URL is incorrect")
        print("\nPlease check:")
        print("  - HeyReach API documentation: https://help.heyreach.io/en/collections/10421873-integrations-api")
        print("  - Verify your API key is correct")
        print("  - Check if the API base URL is correct")
    
    print(f"\n{'=' * 70}")

if __name__ == '__main__':
    test_endpoints()
