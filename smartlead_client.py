"""
Smartlead API Client
Handles all interactions with Smartlead API for email outreach data
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SmartleadClient:
    """Client for interacting with Smartlead API"""
    
    def __init__(self, api_key: str, base_url: str = "https://server.smartlead.ai"):
        """
        Initialize Smartlead client
        
        Args:
            api_key: Smartlead API key
            base_url: Base URL for Smartlead API
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def _make_request(self, endpoint: str, method: str = "GET", params: Dict = None, data: Dict = None) -> Dict:
        """
        Make API request to Smartlead
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Query parameters
            data: Request body data
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}/{endpoint}"
        
        # Add API key to params for Smartlead
        if params is None:
            params = {}
        params['api_key'] = self.api_key
        
        try:
            response = requests.request(
                method=method,
                url=url,
                params=params,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Smartlead API error: {e}")
            return {}
    
    def get_campaigns(self) -> List[Dict]:
        """
        Get all email campaigns
        
        Returns:
            List of campaign dictionaries
        """
        logger.info("Fetching Smartlead campaigns...")
        data = self._make_request("api/v1/campaigns")
        
        # Smartlead returns an array directly
        if isinstance(data, list):
            return data
        return []
    
    def get_campaign_stats(self, campaign_id: str) -> Dict:
        """
        Get statistics for a specific campaign
        
        Args:
            campaign_id: Campaign ID
            
        Returns:
            Campaign statistics dictionary
        """
        logger.info(f"Fetching stats for campaign {campaign_id}...")
        return self._make_request(f"campaigns/{campaign_id}/analytics")
    
    def get_all_campaign_stats(self) -> List[Dict]:
        """
        Get statistics for all campaigns
        
        Returns:
            List of campaign statistics
        """
        campaigns = self.get_campaigns()
        all_stats = []
        
        for campaign in campaigns:
            campaign_id = campaign.get('id')
            if campaign_id:
                stats = self.get_campaign_stats(campaign_id=campaign_id)
                
                # Combine campaign info with stats
                combined = {
                    'campaign_id': campaign_id,
                    'campaign_name': campaign.get('name', 'Unknown'),
                    'status': campaign.get('status', 'unknown'),
                    **stats
                }
                all_stats.append(combined)
        
        return all_stats
    
    def get_leads(self, campaign_id: str = None, status: str = None) -> List[Dict]:
        """
        Get leads data
        
        Args:
            campaign_id: Filter by campaign ID (optional)
            status: Filter by lead status (optional)
            
        Returns:
            List of leads
        """
        params = {}
        if campaign_id:
            params['campaign_id'] = campaign_id
        if status:
            params['status'] = status
            
        logger.info("Fetching leads data...")
        data = self._make_request("leads", params=params)
        return data.get('leads', []) if isinstance(data, dict) else []
    
    def get_email_accounts(self) -> List[Dict]:
        """
        Get all connected email accounts
        
        Returns:
            List of email account dictionaries
        """
        logger.info("Fetching email accounts...")
        data = self._make_request("email-accounts")
        return data.get('email_accounts', []) if isinstance(data, dict) else []
    
    def get_summary_metrics(self, days_back: int = 7) -> Dict:
        """
        Get summary metrics across all campaigns
        
        Args:
            days_back: Number of days to look back (for filtering recent data)
            
        Returns:
            Summary metrics dictionary
        """
        campaigns_stats = self.get_all_campaign_stats()
        
        # Aggregate metrics
        total_sent = 0
        total_delivered = 0
        total_opened = 0
        total_clicked = 0
        total_replied = 0
        total_bounced = 0
        total_unsubscribed = 0
        
        for campaign in campaigns_stats:
            total_sent += campaign.get('emails_sent', 0)
            total_delivered += campaign.get('emails_delivered', 0)
            total_opened += campaign.get('emails_opened', 0)
            total_clicked += campaign.get('links_clicked', 0)
            total_replied += campaign.get('replies', 0)
            total_bounced += campaign.get('bounced', 0)
            total_unsubscribed += campaign.get('unsubscribed', 0)
        
        # Calculate rates
        delivery_rate = (total_delivered / total_sent * 100) if total_sent > 0 else 0
        open_rate = (total_opened / total_delivered * 100) if total_delivered > 0 else 0
        click_rate = (total_clicked / total_delivered * 100) if total_delivered > 0 else 0
        reply_rate = (total_replied / total_delivered * 100) if total_delivered > 0 else 0
        bounce_rate = (total_bounced / total_sent * 100) if total_sent > 0 else 0
        
        return {
            'platform': 'Email (Smartlead)',
            'date_range_days': days_back,
            'total_campaigns': len(campaigns_stats),
            'total_emails_sent': total_sent,
            'total_emails_delivered': total_delivered,
            'delivery_rate': round(delivery_rate, 2),
            'total_opened': total_opened,
            'open_rate': round(open_rate, 2),
            'total_clicked': total_clicked,
            'click_rate': round(click_rate, 2),
            'total_replied': total_replied,
            'reply_rate': round(reply_rate, 2),
            'total_bounced': total_bounced,
            'bounce_rate': round(bounce_rate, 2),
            'total_unsubscribed': total_unsubscribed,
            'campaigns_data': campaigns_stats
        }
    
    def test_connection(self) -> bool:
        """
        Test API connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            campaigns = self.get_campaigns()
            logger.info("✅ Smartlead API connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Smartlead API connection failed: {e}")
            return False
