#!/usr/bin/env python3
"""
Helper script to generate environment variable strings from config.yaml
for deployment to online hosting platforms (e.g., Render, Heroku, etc.)

Usage:
    python generate_env_vars.py

This will output the environment variables you need to set in your hosting platform.
"""

import yaml
import json
import sys

def generate_env_vars():
    """Generate environment variable strings from config.yaml"""
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        heyreach_config = config.get('heyreach', {})
        
        # Generate environment variable strings
        env_vars = []
        
        # API Key
        api_key = heyreach_config.get('api_key', '')
        if api_key:
            env_vars.append(f"HEYREACH_API_KEY={api_key}")
        
        # Base URL
        base_url = heyreach_config.get('base_url', 'https://api.heyreach.io')
        env_vars.append(f"HEYREACH_BASE_URL={base_url}")
        
        # Sender IDs (as JSON array)
        sender_ids = heyreach_config.get('sender_ids', [])
        if sender_ids:
            sender_ids_json = json.dumps(sender_ids)
            env_vars.append(f"HEYREACH_SENDER_IDS={sender_ids_json}")
        
        # Sender Names (as JSON object)
        sender_names = heyreach_config.get('sender_names', {})
        if sender_names:
            sender_names_json = json.dumps(sender_names)
            env_vars.append(f"HEYREACH_SENDER_NAMES={sender_names_json}")
        
        # Client Groups (as JSON object)
        client_groups = heyreach_config.get('client_groups', {})
        if client_groups:
            client_groups_json = json.dumps(client_groups)
            env_vars.append(f"HEYREACH_CLIENT_GROUPS={client_groups_json}")
        
        # Print output
        print("=" * 80)
        print("Environment Variables for Online Deployment")
        print("=" * 80)
        print()
        print("Copy and paste these into your hosting platform's environment variables:")
        print()
        for env_var in env_vars:
            # Truncate long values for display
            if len(env_var) > 100:
                display_var = env_var[:97] + "..."
            else:
                display_var = env_var
            print(display_var)
        print()
        print("=" * 80)
        print()
        print("Note: Some values may be truncated in the display above.")
        print("For Render.com:")
        print("1. Go to your service settings")
        print("2. Navigate to 'Environment' section")
        print("3. Add each variable individually")
        print()
        print("Full values saved to 'env_vars.txt' for reference.")
        print()
        
        # Save to file for easy copy-paste
        with open('env_vars.txt', 'w') as f:
            f.write("\n".join(env_vars))
        
        print(f"[OK] Generated {len(env_vars)} environment variables")
        print(f"[OK] Saved to env_vars.txt")
        
        return True
        
    except FileNotFoundError:
        print("ERROR: config.yaml not found!")
        print("Please run this script from the project root directory.")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = generate_env_vars()
    sys.exit(0 if success else 1)

