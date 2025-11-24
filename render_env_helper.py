#!/usr/bin/env python3
"""
Helper script to format environment variables for easy copy-paste into Render.com
Creates a formatted output that's easier to use in Render's web interface
"""

import yaml
import json
import sys

def format_for_render():
    """Format environment variables for Render.com web interface"""
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        heyreach_config = config.get('heyreach', {})
        
        print("=" * 80)
        print("ENVIRONMENT VARIABLES FOR RENDER.COM")
        print("=" * 80)
        print()
        print("Copy each variable below and add it to Render.com:")
        print("  1. Go to your service on Render.com")
        print("  2. Click 'Environment' in the sidebar")
        print("  3. Click 'Add Environment Variable'")
        print("  4. Paste the KEY and VALUE from below")
        print()
        print("-" * 80)
        print()
        
        # API Key
        api_key = heyreach_config.get('api_key', '')
        if api_key:
            print("VARIABLE 1: HEYREACH_API_KEY")
            print("-" * 80)
            print(f"KEY:   HEYREACH_API_KEY")
            print(f"VALUE: {api_key}")
            print()
        
        # Base URL
        base_url = heyreach_config.get('base_url', 'https://api.heyreach.io')
        print("VARIABLE 2: HEYREACH_BASE_URL")
        print("-" * 80)
        print(f"KEY:   HEYREACH_BASE_URL")
        print(f"VALUE: {base_url}")
        print()
        
        # Sender IDs
        sender_ids = heyreach_config.get('sender_ids', [])
        if sender_ids:
            sender_ids_json = json.dumps(sender_ids)
            print("VARIABLE 3: HEYREACH_SENDER_IDS")
            print("-" * 80)
            print(f"KEY:   HEYREACH_SENDER_IDS")
            print(f"VALUE: {sender_ids_json}")
            print(f"      (This is a JSON array with {len(sender_ids)} sender IDs)")
            print()
        
        # Sender Names
        sender_names = heyreach_config.get('sender_names', {})
        if sender_names:
            sender_names_json = json.dumps(sender_names)
            print("VARIABLE 4: HEYREACH_SENDER_NAMES")
            print("-" * 80)
            print(f"KEY:   HEYREACH_SENDER_NAMES")
            print(f"VALUE: {sender_names_json}")
            print(f"      (This is a JSON object with {len(sender_names)} sender names)")
            print()
        
        # Client Groups
        client_groups = heyreach_config.get('client_groups', {})
        if client_groups:
            client_groups_json = json.dumps(client_groups)
            print("VARIABLE 5: HEYREACH_CLIENT_GROUPS")
            print("-" * 80)
            print(f"KEY:   HEYREACH_CLIENT_GROUPS")
            print(f"VALUE: {client_groups_json}")
            print(f"      (This is a JSON object with {len(client_groups)} client groups)")
            print()
        
        print("=" * 80)
        print()
        print("TIPS:")
        print("- Copy the entire VALUE line (everything after 'VALUE:')")
        print("- Don't add extra quotes - Render handles that automatically")
        print("- For long JSON values, copy the entire line carefully")
        print("- After adding all variables, Render will automatically redeploy")
        print()
        print("Full values also saved to 'render_env_values.txt' for reference")
        print()
        
        # Save to separate file for easy reference
        with open('render_env_values.txt', 'w') as f:
            f.write("Environment Variables for Render.com\n")
            f.write("=" * 80 + "\n\n")
            if api_key:
                f.write(f"HEYREACH_API_KEY={api_key}\n\n")
            f.write(f"HEYREACH_BASE_URL={base_url}\n\n")
            if sender_ids:
                f.write(f"HEYREACH_SENDER_IDS={sender_ids_json}\n\n")
            if sender_names:
                f.write(f"HEYREACH_SENDER_NAMES={sender_names_json}\n\n")
            if client_groups:
                f.write(f"HEYREACH_CLIENT_GROUPS={client_groups_json}\n")
        
        print(f"[OK] Generated formatted environment variables")
        print(f"[OK] Saved full values to render_env_values.txt")
        
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
    success = format_for_render()
    sys.exit(0 if success else 1)

