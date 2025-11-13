#!/usr/bin/env python3
"""
Test script to check GetOverallStats endpoint response structure
"""

import yaml
import json
from datetime import datetime, timedelta
from heyreach_client import HeyReachClient

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

def test_get_overall_stats():
    """Test GetOverallStats endpoint"""
    config = load_config()
    if not config:
        print("Failed to load config.yaml")
        return
    
    heyreach_config = config.get('heyreach', {})
    api_key = heyreach_config.get('api_key')
    base_url = heyreach_config.get('base_url', 'https://api.heyreach.io')
    
    print("=" * 70)
    print("Testing GetOverallStats Endpoint")
    print("=" * 70)
    print(f"Base URL: {base_url}")
    print(f"API Key: {api_key[:20]}...")
    print("=" * 70)
    print()
    
    # Initialize client
    client = HeyReachClient(api_key=api_key, base_url=base_url)
    
    # Get LinkedIn accounts first
    print("Step 1: Getting LinkedIn accounts...")
    accounts = client.get_linkedin_accounts()
    print(f"Found {len(accounts)} LinkedIn accounts")
    
    if not accounts:
        print("❌ No LinkedIn accounts found. Cannot test stats endpoint.")
        return
    
    # Show accounts
    for i, account in enumerate(accounts[:5], 1):  # Show first 5
        print(f"  {i}. {account.get('linkedInUserListName', 'Unknown')} (ID: {account.get('id')})")
    
    if len(accounts) > 5:
        print(f"  ... and {len(accounts) - 5} more")
    
    print()
    
    # Test with first account
    test_account = accounts[0]
    account_id = test_account.get('id')
    account_name = test_account.get('linkedInUserListName', 'Unknown')
    
    print(f"Step 2: Testing GetOverallStats for: {account_name} (ID: {account_id})")
    print()
    
    # Test with last 7 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    start_iso = start_date.strftime('%Y-%m-%dT00:00:00.000Z')
    end_iso = end_date.strftime('%Y-%m-%dT23:59:59.999Z')
    
    print(f"Date Range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"ISO Format: {start_iso} to {end_iso}")
    print()
    
    # Get stats
    print("Fetching stats...")
    stats = client.get_overall_stats(
        account_ids=[str(account_id)],
        campaign_ids=[],
        start_date=start_iso,
        end_date=end_iso
    )
    
    print()
    print("=" * 70)
    print("API Response Structure")
    print("=" * 70)
    
    if stats:
        print(f"Response Type: {type(stats).__name__}")
        print()
        
        if isinstance(stats, dict):
            print("Response Keys:")
            for key in stats.keys():
                value = stats[key]
                value_type = type(value).__name__
                if isinstance(value, (int, float)):
                    print(f"  - {key}: {value} ({value_type})")
                elif isinstance(value, list):
                    print(f"  - {key}: [{value_type}] (length: {len(value)})")
                elif isinstance(value, dict):
                    print(f"  - {key}: {{dict}} (keys: {list(value.keys())[:5]})")
                else:
                    print(f"  - {key}: {value_type}")
            
            print()
            print("Full Response (JSON):")
            print(json.dumps(stats, indent=2, default=str))
        else:
            print(f"Response: {stats}")
    else:
        print("❌ No data returned from API")
        print("Check the logs above for error messages")
    
    print()
    print("=" * 70)

if __name__ == '__main__':
    test_get_overall_stats()
