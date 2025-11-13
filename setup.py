#!/usr/bin/env python3
"""
Setup Script
Verifies all API connections and configurations
"""

import yaml
import os
import sys
from src import (
    HeyReachClient,
    SmartleadClient,
    GoogleSheetsHandler,
    EmailSender
)

def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        print("❌ Error: config.yaml not found!")
        print("Please create config.yaml from the template and add your API keys.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        sys.exit(1)

def test_heyreach(config):
    """Test HeyReach API connection"""
    print("\n🔍 Testing HeyReach API connection...")
    
    heyreach_config = config.get('heyreach', {})
    api_key = heyreach_config.get('api_key')
    
    if not api_key or api_key == "YOUR_HEYREACH_API_KEY_HERE":
        print("❌ HeyReach API key not configured")
        return False
    
    client = HeyReachClient(
        api_key=api_key,
        base_url=heyreach_config.get('base_url', 'https://api.heyreach.io/v1')
    )
    
    return client.test_connection()

def test_smartlead(config):
    """Test Smartlead API connection"""
    print("\n🔍 Testing Smartlead API connection...")
    
    smartlead_config = config.get('smartlead', {})
    api_key = smartlead_config.get('api_key')
    
    if not api_key or api_key == "YOUR_SMARTLEAD_API_KEY_HERE":
        print("❌ Smartlead API key not configured")
        return False
    
    client = SmartleadClient(
        api_key=api_key,
        base_url=smartlead_config.get('base_url', 'https://server.smartlead.ai/api/v1')
    )
    
    return client.test_connection()

def test_google_sheets(config):
    """Test Google Sheets connection"""
    print("\n🔍 Testing Google Sheets connection...")
    
    sheets_config = config.get('google_sheets', {})
    
    if not sheets_config.get('enabled', False):
        print("ℹ️  Google Sheets integration is disabled")
        return True
    
    credentials_file = sheets_config.get('credentials_file')
    spreadsheet_id = sheets_config.get('spreadsheet_id')
    
    if not credentials_file or not os.path.exists(credentials_file):
        print(f"❌ Google credentials file not found: {credentials_file}")
        return False
    
    if not spreadsheet_id or spreadsheet_id == "YOUR_GOOGLE_SHEET_ID_HERE":
        print("❌ Google Sheets spreadsheet ID not configured")
        return False
    
    handler = GoogleSheetsHandler(
        credentials_file=credentials_file,
        spreadsheet_id=spreadsheet_id
    )
    
    if handler.test_connection():
        print("\n🎨 Creating dashboard template...")
        handler.create_dashboard_template()
        return True
    
    return False

def test_email(config):
    """Test email configuration"""
    print("\n🔍 Testing email configuration...")
    
    email_config = config.get('email_reports', {})
    
    if not email_config.get('enabled', False):
        print("ℹ️  Email reports are disabled")
        return True
    
    smtp_server = email_config.get('smtp_server')
    smtp_port = email_config.get('smtp_port')
    sender_email = email_config.get('sender_email')
    sender_password = email_config.get('sender_password')
    
    if not all([smtp_server, smtp_port, sender_email, sender_password]):
        print("❌ Email configuration incomplete")
        return False
    
    if sender_password == "YOUR_APP_PASSWORD_HERE":
        print("❌ Email password not configured")
        return False
    
    sender = EmailSender(
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        sender_email=sender_email,
        sender_password=sender_password
    )
    
    return sender.test_connection()

def create_reports_directory():
    """Create reports directory if it doesn't exist"""
    reports_dir = './reports'
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
        print(f"✅ Created reports directory: {reports_dir}")

def main():
    """Main setup function"""
    print("=" * 60)
    print("🚀 Outreach Reporting Automation - Setup")
    print("=" * 60)
    
    # Load configuration
    print("\n📋 Loading configuration...")
    config = load_config()
    print("✅ Configuration loaded successfully")
    
    # Create reports directory
    create_reports_directory()
    
    # Test all connections
    results = {
        'HeyReach': test_heyreach(config),
        'Smartlead': test_smartlead(config),
        'Google Sheets': test_google_sheets(config),
        'Email': test_email(config)
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Setup Summary")
    print("=" * 60)
    
    all_passed = True
    for service, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{service}: {status}")
        if not passed and service in ['HeyReach', 'Smartlead']:
            all_passed = False
    
    print("\n" + "=" * 60)
    
    if all_passed:
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Run: python generate_report.py (to generate a one-time report)")
        print("2. Run: python scheduler.py (to schedule automated reports)")
    else:
        print("❌ Setup failed. Please fix the errors above and run setup again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
