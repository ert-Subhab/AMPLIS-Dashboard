#!/usr/bin/env python3
"""
Test script to check actual API response from GetOverallStats
"""

import yaml
import json
from datetime import datetime, timedelta
from heyreach_client import HeyReachClient

def test_api_response():
    """Test GetOverallStats API response"""
    config = yaml.safe_load(open('config.yaml', 'r'))
    heyreach_config = config.get('heyreach', {})
    api_key = heyreach_config.get('api_key')
    base_url = heyreach_config.get('base_url', 'https://api.heyreach.io')
    sender_ids = heyreach_config.get('sender_ids', [])
    sender_names = heyreach_config.get('sender_names', {})
    client_groups = heyreach_config.get('client_groups', {})
    
    # Convert sender_names keys to integers
    if sender_names:
        processed_sender_names = {}
        for key, value in sender_names.items():
            try:
                key_int = int(key) if isinstance(key, str) else key
                processed_sender_names[key_int] = value
            except (ValueError, TypeError):
                processed_sender_names[key] = value
        sender_names = processed_sender_names
    
    print("=" * 70)
    print("Testing GetOverallStats API Response")
    print("=" * 70)
    
    client = HeyReachClient(
        api_key=api_key,
        base_url=base_url,
        sender_ids=sender_ids,
        sender_names=sender_names,
        client_groups=client_groups
    )
    
    # Test with first sender and last 7 days
    if sender_ids:
        test_sender_id = sender_ids[0]
        test_sender_name = sender_names.get(test_sender_id, f"Sender {test_sender_id}")
        
        print(f"\nTesting with sender: {test_sender_name} (ID: {test_sender_id})")
        
        # Get last 7 days
        end_date = datetime.now()
        start_date = end_date - timedelta(days=7)
        
        start_iso = start_date.strftime('%Y-%m-%dT00:00:00.000Z')
        end_iso = end_date.strftime('%Y-%m-%dT23:59:59.999Z')
        
        print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
        print(f"ISO format: {start_iso} to {end_iso}")
        print()
        
        # Call API directly
        print("Calling GetOverallStats API...")
        stats = client.get_overall_stats(
            account_ids=[test_sender_id],
            campaign_ids=[],
            start_date=start_iso,
            end_date=end_iso
        )
        
        print()
        print("=" * 70)
        print("API Response:")
        print("=" * 70)
        
        if stats:
            print(f"Response type: {type(stats).__name__}")
            if isinstance(stats, dict):
                print(f"Response keys: {list(stats.keys())}")
                print()
                print("Full response:")
                print(json.dumps(stats, indent=2, default=str))
                
                # Show all values
                print()
                print("All fields and values:")
                for key, value in stats.items():
                    print(f"  {key}: {value} (type: {type(value).__name__})")
            else:
                print(f"Response: {stats}")
        else:
            print("ERROR: No response from API")
            print("Check the logs above for error messages")
    else:
        print("ERROR: No sender IDs found in config.yaml")
    
    print()
    print("=" * 70)

if __name__ == '__main__':
    test_api_response()

