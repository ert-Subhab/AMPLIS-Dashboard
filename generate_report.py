#!/usr/bin/env python3
"""
Generate Report
Main script to generate outreach performance reports
"""

import yaml
import os
import sys
from datetime import datetime
from src import (
    HeyReachClient,
    SmartleadClient,
    GoogleSheetsHandler,
    DataProcessor,
    ReportGenerator,
    EmailSender
)
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_config():
    """Load configuration from config.yaml"""
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        logger.error("config.yaml not found! Run setup.py first.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        sys.exit(1)


def fetch_data(config):
    """Fetch data from HeyReach and Smartlead"""
    
    reporting_config = config.get('reporting', {})
    date_range = reporting_config.get('default_date_range', 'last_7_days')
    
    # Calculate days_back based on date range
    from datetime import datetime, timedelta
    
    today = datetime.now()
    
    if date_range == 'today':
        days_back = 1
    elif date_range == 'yesterday':
        days_back = 1
    elif date_range == 'last_7_days':
        days_back = 7
    elif date_range == 'last_30_days':
        days_back = 30
    elif date_range == 'this_week_sat_fri':
        # Find last Saturday
        days_since_saturday = (today.weekday() + 2) % 7
        days_back = days_since_saturday if days_since_saturday > 0 else 7
    elif date_range == 'last_week_sat_fri':
        # Find last Saturday, then go back 7 more days
        days_since_saturday = (today.weekday() + 2) % 7
        days_back = days_since_saturday + 7
    elif date_range == 'this_month':
        days_back = today.day
    elif date_range == 'last_month':
        days_back = 30
    else:
        days_back = 7
    
    logger.info(f"Fetching data for date range: {date_range} ({days_back} days)")
    
    # Fetch HeyReach data
    logger.info("Fetching HeyReach (LinkedIn) data...")
    heyreach_config = config['heyreach']
    heyreach_client = HeyReachClient(
        api_key=heyreach_config['api_key'],
        base_url=heyreach_config.get('base_url', 'https://api.heyreach.io')
    )
    linkedin_data = heyreach_client.get_summary_metrics(days_back=days_back)
    
    # Fetch Smartlead data
    logger.info("Fetching Smartlead (Email) data...")
    smartlead_config = config['smartlead']
    smartlead_client = SmartleadClient(
        api_key=smartlead_config['api_key'],
        base_url=smartlead_config.get('base_url', 'https://server.smartlead.ai')
    )
    email_data = smartlead_client.get_summary_metrics(days_back=days_back)
    
    return linkedin_data, email_data


def process_data(linkedin_data, email_data):
    """Process and analyze the fetched data"""
    logger.info("Processing data...")
    
    processor = DataProcessor()
    processed_data = processor.process_data(linkedin_data, email_data)
    
    return processed_data


def generate_report(processed_data, config):
    """Generate HTML report"""
    reporting_config = config.get('reporting', {})
    
    if not reporting_config.get('save_local', True):
        logger.info("Local report saving is disabled")
        return None
    
    logger.info("Generating HTML report...")
    
    # Create reports directory if it doesn't exist
    reports_dir = reporting_config.get('local_report_path', './reports')
    os.makedirs(reports_dir, exist_ok=True)
    
    # Generate filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = os.path.join(reports_dir, f'outreach_report_{timestamp}.html')
    
    # Generate report
    generator = ReportGenerator()
    generator.generate_html_report(processed_data, report_path)
    
    return report_path


def update_google_sheets(processed_data, config):
    """Update Google Sheets dashboard"""
    sheets_config = config.get('google_sheets', {})
    
    if not sheets_config.get('enabled', False):
        logger.info("Google Sheets integration is disabled")
        return
    
    logger.info("Updating Google Sheets...")
    
    handler = GoogleSheetsHandler(
        credentials_file=sheets_config['credentials_file'],
        spreadsheet_id=sheets_config['spreadsheet_id']
    )
    
    if handler.authenticate():
        linkedin_data = processed_data['linkedin']
        email_data = processed_data['email']
        
        # Update overview
        handler.update_overview(linkedin_data, email_data)
        
        # Update LinkedIn campaigns
        handler.update_linkedin_campaigns(linkedin_data.get('campaigns_data', []))
        
        # Update email campaigns
        handler.update_email_campaigns(email_data.get('campaigns_data', []))
        
        # Append historical data
        handler.append_historical_data(linkedin_data, email_data)
        
        logger.info("✅ Google Sheets updated successfully")


def send_email_report(processed_data, report_path, config):
    """Send email report"""
    email_config = config.get('email_reports', {})
    
    if not email_config.get('enabled', False):
        logger.info("Email reports are disabled")
        return
    
    logger.info("Sending email report...")
    
    sender = EmailSender(
        smtp_server=email_config['smtp_server'],
        smtp_port=email_config['smtp_port'],
        sender_email=email_config['sender_email'],
        sender_password=email_config['sender_password']
    )
    
    recipient_emails = email_config.get('recipient_emails', [])
    
    if not recipient_emails:
        logger.warning("No recipient emails configured")
        return
    
    sender.send_report(
        recipient_emails=recipient_emails,
        processed_data=processed_data,
        attachment_path=report_path
    )


def main():
    """Main execution function"""
    print("=" * 60)
    print("📊 Generating Outreach Performance Report")
    print("=" * 60)
    
    try:
        # Load configuration
        config = load_config()
        
        # Fetch data
        linkedin_data, email_data = fetch_data(config)
        
        # Process data
        processed_data = process_data(linkedin_data, email_data)
        
        # Generate HTML report
        report_path = generate_report(processed_data, config)
        
        # Update Google Sheets
        update_google_sheets(processed_data, config)
        
        # Send email report
        send_email_report(processed_data, report_path, config)
        
        # Summary
        print("\n" + "=" * 60)
        print("✅ Report Generation Complete!")
        print("=" * 60)
        
        combined = processed_data['combined_metrics']
        print(f"\n📈 Summary:")
        print(f"   Total Outreach: {combined['total_outreach_actions']:,}")
        print(f"   Total Responses: {combined['total_responses']:,}")
        print(f"   Overall Response Rate: {combined['overall_response_rate']}%")
        
        if report_path:
            print(f"\n📄 Report saved to: {report_path}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
