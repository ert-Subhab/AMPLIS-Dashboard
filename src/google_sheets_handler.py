"""
Google Sheets Handler
Handles writing outreach data to Google Sheets for live dashboards
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from typing import Dict, List
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleSheetsHandler:
    """Handler for Google Sheets integration"""
    
    def __init__(self, credentials_file: str, spreadsheet_id: str):
        """
        Initialize Google Sheets handler
        
        Args:
            credentials_file: Path to Google service account JSON credentials
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.credentials_file = credentials_file
        self.spreadsheet_id = spreadsheet_id
        self.client = None
        self.spreadsheet = None
        
    def authenticate(self):
        """Authenticate with Google Sheets API"""
        try:
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            
            creds = ServiceAccountCredentials.from_json_keyfile_name(
                self.credentials_file, 
                scope
            )
            self.client = gspread.authorize(creds)
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            
            logger.info("✅ Google Sheets authentication successful")
            return True
        except Exception as e:
            logger.error(f"❌ Google Sheets authentication failed: {e}")
            return False
    
    def create_dashboard_template(self):
        """Create dashboard template with all necessary sheets"""
        if not self.spreadsheet:
            self.authenticate()
        
        try:
            # Create Overview sheet
            overview_sheet = self._get_or_create_worksheet("Overview")
            self._setup_overview_sheet(overview_sheet)
            
            # Create LinkedIn Details sheet
            linkedin_sheet = self._get_or_create_worksheet("LinkedIn Campaigns")
            self._setup_linkedin_sheet(linkedin_sheet)
            
            # Create Email Details sheet
            email_sheet = self._get_or_create_worksheet("Email Campaigns")
            self._setup_email_sheet(email_sheet)
            
            # Create Historical Data sheet
            history_sheet = self._get_or_create_worksheet("Historical Data")
            self._setup_history_sheet(history_sheet)
            
            logger.info("✅ Dashboard template created successfully")
            return True
        except Exception as e:
            logger.error(f"Error creating dashboard template: {e}")
            return False
    
    def _get_or_create_worksheet(self, title: str):
        """Get existing worksheet or create new one"""
        try:
            worksheet = self.spreadsheet.worksheet(title)
        except gspread.exceptions.WorksheetNotFound:
            worksheet = self.spreadsheet.add_worksheet(title=title, rows=1000, cols=26)
        return worksheet
    
    def _setup_overview_sheet(self, sheet):
        """Setup overview sheet with headers and formatting"""
        headers = [
            ["OUTREACH PERFORMANCE DASHBOARD"],
            ["Last Updated:", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            [],
            ["SUMMARY METRICS"],
            [],
            ["Platform", "Campaigns", "Sent", "Delivered/Accepted", "Opened/Messages", "Replied", "Reply Rate"],
        ]
        
        # Write headers
        for i, row in enumerate(headers, 1):
            if row:
                sheet.update(f'A{i}', [row])
        
        # Format header row
        sheet.format('A1:G1', {
            'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.8},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
            'horizontalAlignment': 'CENTER'
        })
    
    def _setup_linkedin_sheet(self, sheet):
        """Setup LinkedIn campaigns sheet"""
        headers = [[
            "Campaign ID", "Campaign Name", "Status", "Invites Sent", 
            "Invites Accepted", "Acceptance Rate %", "Messages Sent", 
            "Replies", "Reply Rate %", "Last Updated"
        ]]
        sheet.update('A1', headers)
        
        sheet.format('A1:J1', {
            'backgroundColor': {'red': 0.2, 'green': 0.5, 'blue': 0.8},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
    
    def _setup_email_sheet(self, sheet):
        """Setup email campaigns sheet"""
        headers = [[
            "Campaign ID", "Campaign Name", "Status", "Emails Sent", 
            "Delivered", "Delivery Rate %", "Opened", "Open Rate %", 
            "Clicked", "Click Rate %", "Replied", "Reply Rate %", 
            "Bounced", "Unsubscribed", "Last Updated"
        ]]
        sheet.update('A1', headers)
        
        sheet.format('A1:O1', {
            'backgroundColor': {'red': 0.8, 'green': 0.3, 'blue': 0.3},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
    
    def _setup_history_sheet(self, sheet):
        """Setup historical data tracking sheet"""
        headers = [[
            "Date", "LinkedIn Invites", "LinkedIn Acceptance Rate", 
            "LinkedIn Reply Rate", "Emails Sent", "Email Open Rate", 
            "Email Reply Rate"
        ]]
        sheet.update('A1', headers)
        
        sheet.format('A1:G1', {
            'backgroundColor': {'red': 0.3, 'green': 0.7, 'blue': 0.3},
            'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}}
        })
    
    def update_overview(self, linkedin_data: Dict, email_data: Dict):
        """
        Update overview sheet with summary metrics
        
        Args:
            linkedin_data: LinkedIn metrics dictionary
            email_data: Email metrics dictionary
        """
        if not self.spreadsheet:
            self.authenticate()
        
        try:
            sheet = self.spreadsheet.worksheet("Overview")
            
            # Update timestamp
            sheet.update('B2', [[datetime.now().strftime("%Y-%m-%d %H:%M:%S")]])
            
            # Update LinkedIn row
            linkedin_row = [
                "LinkedIn (HeyReach)",
                linkedin_data.get('total_campaigns', 0),
                linkedin_data.get('total_invites_sent', 0),
                linkedin_data.get('total_invites_accepted', 0),
                linkedin_data.get('total_messages_sent', 0),
                linkedin_data.get('total_replies', 0),
                f"{linkedin_data.get('reply_rate', 0)}%"
            ]
            sheet.update('A7', [linkedin_row])
            
            # Update Email row
            email_row = [
                "Email (Smartlead)",
                email_data.get('total_campaigns', 0),
                email_data.get('total_emails_sent', 0),
                email_data.get('total_emails_delivered', 0),
                email_data.get('total_opened', 0),
                email_data.get('total_replied', 0),
                f"{email_data.get('reply_rate', 0)}%"
            ]
            sheet.update('A8', [email_row])
            
            logger.info("✅ Overview sheet updated")
        except Exception as e:
            logger.error(f"Error updating overview sheet: {e}")
    
    def update_linkedin_campaigns(self, campaigns_data: List[Dict]):
        """
        Update LinkedIn campaigns sheet
        
        Args:
            campaigns_data: List of campaign dictionaries
        """
        if not self.spreadsheet:
            self.authenticate()
        
        try:
            sheet = self.spreadsheet.worksheet("LinkedIn Campaigns")
            
            # Clear existing data (except headers)
            sheet.delete_rows(2, sheet.row_count)
            
            # Prepare rows
            rows = []
            for campaign in campaigns_data:
                acceptance_rate = (
                    campaign.get('invites_accepted', 0) / campaign.get('invites_sent', 1) * 100
                    if campaign.get('invites_sent', 0) > 0 else 0
                )
                reply_rate = (
                    campaign.get('replies', 0) / campaign.get('messages_sent', 1) * 100
                    if campaign.get('messages_sent', 0) > 0 else 0
                )
                
                row = [
                    campaign.get('campaign_id', ''),
                    campaign.get('campaign_name', ''),
                    campaign.get('status', ''),
                    campaign.get('invites_sent', 0),
                    campaign.get('invites_accepted', 0),
                    f"{acceptance_rate:.2f}%",
                    campaign.get('messages_sent', 0),
                    campaign.get('replies', 0),
                    f"{reply_rate:.2f}%",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
                rows.append(row)
            
            # Write all rows at once
            if rows:
                sheet.update('A2', rows)
            
            logger.info(f"✅ Updated {len(rows)} LinkedIn campaigns")
        except Exception as e:
            logger.error(f"Error updating LinkedIn campaigns: {e}")
    
    def update_email_campaigns(self, campaigns_data: List[Dict]):
        """
        Update email campaigns sheet
        
        Args:
            campaigns_data: List of campaign dictionaries
        """
        if not self.spreadsheet:
            self.authenticate()
        
        try:
            sheet = self.spreadsheet.worksheet("Email Campaigns")
            
            # Clear existing data (except headers)
            sheet.delete_rows(2, sheet.row_count)
            
            # Prepare rows
            rows = []
            for campaign in campaigns_data:
                delivered = campaign.get('emails_delivered', 0)
                sent = campaign.get('emails_sent', 0)
                
                delivery_rate = (delivered / sent * 100) if sent > 0 else 0
                open_rate = (campaign.get('emails_opened', 0) / delivered * 100) if delivered > 0 else 0
                click_rate = (campaign.get('links_clicked', 0) / delivered * 100) if delivered > 0 else 0
                reply_rate = (campaign.get('replies', 0) / delivered * 100) if delivered > 0 else 0
                
                row = [
                    campaign.get('campaign_id', ''),
                    campaign.get('campaign_name', ''),
                    campaign.get('status', ''),
                    sent,
                    delivered,
                    f"{delivery_rate:.2f}%",
                    campaign.get('emails_opened', 0),
                    f"{open_rate:.2f}%",
                    campaign.get('links_clicked', 0),
                    f"{click_rate:.2f}%",
                    campaign.get('replies', 0),
                    f"{reply_rate:.2f}%",
                    campaign.get('bounced', 0),
                    campaign.get('unsubscribed', 0),
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ]
                rows.append(row)
            
            # Write all rows at once
            if rows:
                sheet.update('A2', rows)
            
            logger.info(f"✅ Updated {len(rows)} email campaigns")
        except Exception as e:
            logger.error(f"Error updating email campaigns: {e}")
    
    def append_historical_data(self, linkedin_data: Dict, email_data: Dict):
        """
        Append today's data to historical tracking
        
        Args:
            linkedin_data: LinkedIn metrics
            email_data: Email metrics
        """
        if not self.spreadsheet:
            self.authenticate()
        
        try:
            sheet = self.spreadsheet.worksheet("Historical Data")
            
            row = [
                datetime.now().strftime("%Y-%m-%d"),
                linkedin_data.get('total_invites_sent', 0),
                f"{linkedin_data.get('acceptance_rate', 0)}%",
                f"{linkedin_data.get('reply_rate', 0)}%",
                email_data.get('total_emails_sent', 0),
                f"{email_data.get('open_rate', 0)}%",
                f"{email_data.get('reply_rate', 0)}%"
            ]
            
            sheet.append_row(row)
            logger.info("✅ Historical data appended")
        except Exception as e:
            logger.error(f"Error appending historical data: {e}")
    
    def test_connection(self) -> bool:
        """Test Google Sheets connection"""
        return self.authenticate()
