"""
HeyReach API Client
Handles all interactions with HeyReach API for LinkedIn outreach data
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import json

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Reduce verbosity for requests library
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('urllib3').setLevel(logging.WARNING)


class HeyReachClient:
    """Client for interacting with HeyReach API"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.heyreach.io"):
        """
        Initialize HeyReach client
        
        Args:
            api_key: HeyReach API key
            base_url: Base URL for HeyReach API
        """
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.headers = {
            "X-API-KEY": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Store working endpoints (discovered dynamically)
        self.working_endpoints = {}
    
    def _make_request(self, endpoint: str, method: str = "GET", params: Dict = None, data: Dict = None, headers: Dict = None) -> Dict:
        """
        Make API request to HeyReach
        
        Args:
            endpoint: API endpoint
            method: HTTP method
            params: Query parameters
            data: Request body data
            headers: Optional custom headers
            
        Returns:
            Response data as dictionary
        """
        url = f"{self.base_url}/{endpoint}"
        request_headers = headers or self.headers
        
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=request_headers,
                params=params,
                json=data,
                timeout=30
            )
            
            # Log detailed error information for debugging
            if response.status_code != 200:
                logger.error(f"API Error - Status: {response.status_code}, URL: {url}")
                try:
                    error_text = response.text[:500]
                    logger.error(f"Response: {error_text}")
                except:
                    pass
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            logger.error(f"URL: {url}")
            try:
                error_text = e.response.text[:500] if e.response else 'No response'
                logger.error(f"Response: {error_text}")
            except:
                pass
            return {}
        except requests.exceptions.RequestException as e:
            logger.error(f"HeyReach API error: {e}")
            return {}
    
    def get_campaigns(self) -> List[Dict]:
        """
        Get all LinkedIn campaigns
        
        Returns:
            List of campaign dictionaries
        """
        logger.info("Fetching HeyReach campaigns...")
        
        # Check if we already know a working endpoint
        if 'campaigns' in self.working_endpoints:
            endpoint = self.working_endpoints['campaigns']
            logger.info(f"Using cached working endpoint: {endpoint}")
            data = self._make_request(endpoint, method="POST", data={
                "offset": 0,
                "keyword": "",
                "statuses": [],
                "accountIds": [],
                "limit": 100
            })
            if data and isinstance(data, dict):
                if 'items' in data:
                    return data.get('items', [])
                elif 'data' in data:
                    return data.get('data', [])
            elif isinstance(data, list):
                return data
        
        # Try different endpoint variations
        endpoints_to_try = [
            "api/public/campaign/GetAll",
            "api/public/campaign/getAll",
            "api/public/campaigns",
            "api/v1/campaign",
            "api/v1/campaigns",
            "api/campaign",
            "api/campaigns",
            "campaign/GetAll",
        ]
        
        request_data = {
            "offset": 0,
            "keyword": "",
            "statuses": [],
            "accountIds": [],
            "limit": 100
        }
        
        for endpoint in endpoints_to_try:
            try:
                logger.debug(f"Trying endpoint: {endpoint}")
                data = self._make_request(endpoint, method="POST", data=request_data)
                
                if data and isinstance(data, dict):
                    if 'items' in data:
                        logger.info(f"✅ Successfully fetched campaigns from: {endpoint}")
                        self.working_endpoints['campaigns'] = endpoint
                        return data.get('items', [])
                    elif 'data' in data:
                        logger.info(f"✅ Successfully fetched campaigns from: {endpoint}")
                        self.working_endpoints['campaigns'] = endpoint
                        return data.get('data', [])
                elif isinstance(data, list):
                    logger.info(f"✅ Successfully fetched campaigns from: {endpoint}")
                    self.working_endpoints['campaigns'] = endpoint
                    return data
            except Exception as e:
                logger.debug(f"Endpoint {endpoint} failed: {str(e)[:100]}")
                continue
        
        logger.warning("⚠️ All endpoint variations failed for campaigns")
        return []
    
    def get_campaign_stats(self, campaign_id: str, start_date: str = None, end_date: str = None) -> Dict:
        """
        Get statistics for a specific campaign
        
        Args:
            campaign_id: Campaign ID
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            
        Returns:
            Campaign statistics dictionary
        """
        params = {
            "campaign_id": campaign_id
        }
        
        if start_date:
            params['start_date'] = start_date
        if end_date:
            params['end_date'] = end_date
            
        logger.info(f"Fetching stats for campaign {campaign_id}...")
        return self._make_request(f"campaigns/{campaign_id}/stats", params=params)
    
    def get_linkedin_accounts(self) -> List[Dict]:
        """
        Get all LinkedIn accounts (senders)
        
        Returns:
            List of LinkedIn account dictionaries
        """
        logger.info("Fetching LinkedIn accounts...")
        
        # Check if we already know a working endpoint
        if 'linkedin_accounts' in self.working_endpoints:
            endpoint = self.working_endpoints['linkedin_accounts']
            logger.info(f"Using cached working endpoint: {endpoint}")
            data = self._make_request(endpoint, method="POST", data={
                "offset": 0,
                "limit": 100
            })
            if data and isinstance(data, dict):
                if 'items' in data:
                    return data.get('items', [])
                elif 'data' in data:
                    return data.get('data', [])
            elif isinstance(data, list):
                return data
        
        # Try different endpoint variations
        endpoints_to_try = [
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
        ]
        
        # Try different header variations
        header_variations = [
            self.headers,  # Original headers
            {
                "X-API-KEY": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
            {
                "api-key": self.api_key,
                "Content-Type": "application/json",
                "Accept": "application/json"
            },
        ]
        
        request_data = {
            "offset": 0,
            "limit": 100
        }
        
        for headers in header_variations:
            for endpoint in endpoints_to_try:
                try:
                    logger.debug(f"Trying endpoint: {endpoint} with headers: {list(headers.keys())}")
                    data = self._make_request(endpoint, method="POST", data=request_data, headers=headers)
                    
                    if data and isinstance(data, dict):
                        # Check for different response structures
                        if 'items' in data and len(data.get('items', [])) >= 0:
                            logger.info(f"✅ Successfully fetched accounts from: {endpoint}")
                            self.working_endpoints['linkedin_accounts'] = endpoint
                            self.headers = headers  # Update to working headers
                            return data.get('items', [])
                        elif 'data' in data:
                            logger.info(f"✅ Successfully fetched accounts from: {endpoint}")
                            self.working_endpoints['linkedin_accounts'] = endpoint
                            self.headers = headers
                            return data.get('data', [])
                    elif isinstance(data, list) and len(data) >= 0:
                        logger.info(f"✅ Successfully fetched accounts from: {endpoint}")
                        self.working_endpoints['linkedin_accounts'] = endpoint
                        self.headers = headers
                        return data
                except Exception as e:
                    logger.debug(f"Endpoint {endpoint} failed: {str(e)[:100]}")
                    continue
        
        logger.warning("⚠️ All endpoint variations failed for LinkedIn accounts")
        return []
    
    def get_leads(self, campaign_id: str = None, start_date: str = None, end_date: str = None, 
                  linkedin_account_id: str = None, limit: int = 1000) -> List[Dict]:
        """
        Get leads data from campaigns
        
        Args:
            campaign_id: Optional campaign ID filter
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            linkedin_account_id: Optional LinkedIn account ID filter
            limit: Maximum number of leads to return
            
        Returns:
            List of lead dictionaries
        """
        logger.info("Fetching leads data...")
        
        # Check if we already know a working endpoint
        if 'leads' in self.working_endpoints:
            endpoint = self.working_endpoints['leads']
            logger.info(f"Using cached working endpoint: {endpoint}")
            request_data = {
                "offset": 0,
                "limit": limit,
                "keyword": "",
                "campaignIds": [campaign_id] if campaign_id else [],
                "linkedInAccountIds": [linkedin_account_id] if linkedin_account_id else [],
                "statuses": [],
                "tags": []
            }
            if start_date and end_date:
                request_data["startDate"] = start_date
                request_data["endDate"] = end_date
            
            data = self._make_request(endpoint, method="POST", data=request_data)
            if data and isinstance(data, dict):
                if 'items' in data:
                    return data.get('items', [])
                elif 'data' in data:
                    return data.get('data', [])
            elif isinstance(data, list):
                return data
        
        request_data = {
            "offset": 0,
            "limit": limit,
            "keyword": "",
            "campaignIds": [campaign_id] if campaign_id else [],
            "linkedInAccountIds": [linkedin_account_id] if linkedin_account_id else [],
            "statuses": [],
            "tags": []
        }
        
        if start_date and end_date:
            request_data["startDate"] = start_date
            request_data["endDate"] = end_date
        
        # Try different endpoint variations
        endpoints_to_try = [
            "api/public/lead/GetAll",
            "api/public/lead/getAll",
            "api/public/leads",
            "api/v1/lead",
            "api/v1/leads",
            "api/lead",
            "api/leads",
            "lead/GetAll",
        ]
        
        for endpoint in endpoints_to_try:
            try:
                logger.debug(f"Trying endpoint: {endpoint}")
                data = self._make_request(endpoint, method="POST", data=request_data)
                
                if data and isinstance(data, dict):
                    if 'items' in data:
                        logger.info(f"✅ Successfully fetched leads from: {endpoint}")
                        self.working_endpoints['leads'] = endpoint
                        return data.get('items', [])
                    elif 'data' in data:
                        logger.info(f"✅ Successfully fetched leads from: {endpoint}")
                        self.working_endpoints['leads'] = endpoint
                        return data.get('data', [])
                elif isinstance(data, list):
                    logger.info(f"✅ Successfully fetched leads from: {endpoint}")
                    self.working_endpoints['leads'] = endpoint
                    return data
            except Exception as e:
                logger.debug(f"Endpoint {endpoint} failed: {str(e)[:100]}")
                continue
        
        logger.warning("⚠️ All endpoint variations failed for leads")
        return []
    
    def get_overall_stats(self, account_ids: List[str] = None, campaign_ids: List[str] = None, 
                          start_date: str = None, end_date: str = None) -> Dict:
        """
        Get overall stats from HeyReach API using GetOverallStats endpoint
        
        Args:
            account_ids: List of LinkedIn account IDs. If None or empty, gets all senders
            campaign_ids: List of campaign IDs. If None or empty, gets all campaigns
            start_date: Start date in ISO format (YYYY-MM-DDTHH:MM:SS.000Z)
            end_date: End date in ISO format (YYYY-MM-DDTHH:MM:SS.000Z)
            
        Returns:
            Dictionary with overall stats
        """
        logger.info(f"Fetching overall stats from GetOverallStats endpoint...")
        
        endpoint = "api/public/stats/GetOverallStats"
        
        # Prepare request body
        # Convert account_ids to integers if they're strings
        processed_account_ids = []
        if account_ids:
            for acc_id in account_ids:
                try:
                    # Try to convert to int
                    if isinstance(acc_id, str):
                        processed_account_ids.append(int(acc_id))
                    else:
                        processed_account_ids.append(acc_id)
                except (ValueError, TypeError):
                    # If conversion fails, use as-is
                    processed_account_ids.append(acc_id)
        
        # Convert campaign_ids to integers if they're strings
        processed_campaign_ids = []
        if campaign_ids:
            for camp_id in campaign_ids:
                try:
                    if isinstance(camp_id, str):
                        processed_campaign_ids.append(int(camp_id))
                    else:
                        processed_campaign_ids.append(camp_id)
                except (ValueError, TypeError):
                    processed_campaign_ids.append(camp_id)
        
        request_data = {
            "accountIds": processed_account_ids if processed_account_ids else [],
            "campaignIds": processed_campaign_ids if processed_campaign_ids else [],
            "startDate": start_date,
            "endDate": end_date
        }
        
        logger.debug(f"Request data: accountIds={processed_account_ids}, startDate={start_date}, endDate={end_date}")
        
        # Set headers as per API documentation
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
            "Accept": "text/plain"
        }
        
        try:
            data = self._make_request(endpoint, method="POST", data=request_data, headers=headers)
            if data:
                # Log the actual response structure for debugging
                logger.info(f"GetOverallStats response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
                logger.debug(f"GetOverallStats response: {json.dumps(data, indent=2, default=str)[:1000]}")
            return data if data else {}
        except Exception as e:
            logger.error(f"Error fetching overall stats: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {}
    
    def get_sender_weekly_performance(self, sender_id: str = None, start_date: str = None, 
                                     end_date: str = None) -> Dict:
        """
        Get weekly performance data for a specific sender or all senders using GetOverallStats API
        
        Args:
            sender_id: Optional sender (LinkedIn account) ID. If None, gets all senders
            start_date: Start date (YYYY-MM-DD). If None, defaults to last 12 weeks
            end_date: End date (YYYY-MM-DD). If None, defaults to today
            
        Returns:
            Dictionary with weekly performance data grouped by sender
        """
        from collections import defaultdict
        from datetime import datetime, timedelta
        
        # Default to last 12 weeks if dates not provided
        if not end_date:
            end_date_obj = datetime.now()
        else:
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
        
        if not start_date:
            start_date_obj = end_date_obj - timedelta(weeks=12)
        else:
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
        
        # Get all LinkedIn accounts
        linkedin_accounts = self.get_linkedin_accounts()
        
        # Filter by sender_id if provided
        if sender_id and sender_id != 'all':
            linkedin_accounts = [acc for acc in linkedin_accounts if str(acc.get('id')) == str(sender_id)]
        
        # If no accounts found but we have sender_id, try to use it directly
        if not linkedin_accounts and sender_id and sender_id != 'all':
            logger.warning(f"No LinkedIn accounts found, but sender_id provided: {sender_id}")
            logger.info(f"Attempting to fetch stats directly for sender_id: {sender_id}")
            # Create a dummy account entry to proceed
            linkedin_accounts = [{
                'id': sender_id,
                'linkedInUserListName': f'Sender {sender_id}',
                'name': f'Sender {sender_id}'
            }]
        
        if not linkedin_accounts:
            logger.warning("⚠️ No LinkedIn accounts found. Cannot fetch stats.")
            logger.info("💡 Tip: If you know your sender IDs, you can modify the code to use them directly.")
            return {
                'start_date': start_date_obj.strftime('%Y-%m-%d'),
                'end_date': end_date_obj.strftime('%Y-%m-%d'),
                'senders': {}
            }
        
        # Generate list of weeks (Saturday to Friday)
        # weekday(): Monday=0, Tuesday=1, Wednesday=2, Thursday=3, Friday=4, Saturday=5, Sunday=6
        weeks = []
        
        # Find the Saturday that starts the week containing start_date
        start_weekday = start_date_obj.weekday()
        
        # Calculate days to go back to get to Saturday
        # If it's Saturday (5), we're already there (0 days back)
        # If it's Sunday (6), go back 1 day
        # If it's Monday (0), go back 2 days
        # If it's Tuesday (1), go back 3 days
        # If it's Wednesday (2), go back 4 days
        # If it's Thursday (3), go back 5 days
        # If it's Friday (4), go back 6 days
        if start_weekday == 5:  # Saturday
            days_back = 0
        elif start_weekday == 6:  # Sunday
            days_back = 1
        else:  # Monday (0) through Friday (4)
            days_back = start_weekday + 2
        
        # Find the Saturday that starts the week
        first_saturday = start_date_obj - timedelta(days=days_back)
        
        # Generate week ranges
        current_week_start = first_saturday
        week_count = 0
        max_weeks = 52  # Safety limit to prevent infinite loops
        
        while current_week_start <= end_date_obj and week_count < max_weeks:
            week_end = current_week_start + timedelta(days=6)  # Friday of this week
            
            # Only add week if it overlaps with our date range
            if week_end >= start_date_obj:
                # Adjust boundaries if needed
                effective_start = max(current_week_start, start_date_obj)
                effective_end = min(week_end, end_date_obj)
                
                weeks.append({
                    'start': effective_start,
                    'end': effective_end,
                    'key': current_week_start.strftime('%Y-%m-%d')  # Use Saturday as week identifier
                })
            
            # Move to next Saturday
            current_week_start = current_week_start + timedelta(days=7)
            week_count += 1
        
        # Store weekly data by sender
        sender_weekly_data = defaultdict(lambda: defaultdict(lambda: {
            'connections_sent': 0,
            'connections_accepted': 0,
            'messages_sent': 0,
            'message_replies': 0,
            'open_conversations': 0,
            'interested': 0,
            'leads_not_enrolled': 0
        }))
        
        # Get stats for each sender and each week
        for account in linkedin_accounts:
            account_id = account.get('id')
            sender_name = account.get('linkedInUserListName') or account.get('name') or f"Account {account_id}"
            
            logger.info(f"Fetching stats for sender: {sender_name} (ID: {account_id})")
            
            # Get stats for each week
            for week in weeks:
                week_start_iso = week['start'].strftime('%Y-%m-%dT00:00:00.000Z')
                week_end_iso = week['end'].strftime('%Y-%m-%dT23:59:59.999Z')
                
                logger.debug(f"  Fetching stats for week {week['key']} ({week_start_iso} to {week_end_iso})")
                
                # Get stats for this sender and week
                # Use account_id directly (get_overall_stats will handle conversion)
                stats = self.get_overall_stats(
                    account_ids=[account_id],
                    campaign_ids=[],
                    start_date=week_start_iso,
                    end_date=week_end_iso
                )
                
                if stats:
                    # Log the full response structure on first successful call (to understand API structure)
                    account_idx = linkedin_accounts.index(account)
                    week_idx = [w['key'] for w in weeks].index(week['key'])
                    if account_idx == 0 and week_idx == 0:
                        logger.info(f"📊 GetOverallStats Response Structure:")
                        logger.info(f"   Response type: {type(stats).__name__}")
                        if isinstance(stats, dict):
                            logger.info(f"   Keys: {list(stats.keys())}")
                            logger.info(f"   Full response (first 2000 chars): {json.dumps(stats, indent=2, default=str)[:2000]}")
                        else:
                            logger.info(f"   Response: {str(stats)[:500]}")
                    
                    # Extract metrics from stats response
                    # Note: Field names may vary - adjust based on actual API response
                    week_data = sender_weekly_data[sender_name][week['key']]
                    
                    # Map API response fields to our metrics
                    # Try multiple possible field names from the API response
                    # Use helper function to safely get values (handles 0 correctly)
                    def get_field_value(stats_dict, *field_names, default=0):
                        """Get field value, trying multiple field names, handling 0 correctly"""
                        for field_name in field_names:
                            if field_name in stats_dict:
                                value = stats_dict[field_name]
                                if value is not None:
                                    return value
                        return default
                    
                    week_data['connections_sent'] = get_field_value(
                        stats, 'connectionRequestsSent', 'connectionRequests', 'connectionsSent', 
                        'invitesSent', 'sentConnections', 'totalConnectionsSent'
                    )
                    
                    week_data['connections_accepted'] = get_field_value(
                        stats, 'connectionsAccepted', 'acceptedConnections', 'invitesAccepted', 
                        'acceptedInvites', 'totalConnectionsAccepted'
                    )
                    
                    week_data['messages_sent'] = get_field_value(
                        stats, 'messagesSent', 'sentMessages', 'totalMessagesSent', 'messages'
                    )
                    
                    week_data['message_replies'] = get_field_value(
                        stats, 'repliesReceived', 'replies', 'messageReplies', 
                        'totalReplies', 'repliesCount'
                    )
                    
                    week_data['open_conversations'] = get_field_value(
                        stats, 'openConversations', 'activeConversations', 
                        'conversations', 'activeChats'
                    )
                    
                    week_data['interested'] = get_field_value(
                        stats, 'interested', 'interestedLeads', 
                        'leadsInterested', 'interestedCount'
                    )
                    
                    week_data['leads_not_enrolled'] = get_field_value(
                        stats, 'leadsNotEnrolled', 'pendingLeads', 
                        'notEnrolled', 'pending'
                    )
                    
                    logger.debug(f"    Week {week['key']} Stats for {sender_name}: {week_data}")
        
        # Format data for response
        result = {
            'start_date': start_date_obj.strftime('%Y-%m-%d'),
            'end_date': end_date_obj.strftime('%Y-%m-%d'),
            'senders': {}
        }
        
        for sender_name, weekly_data in sender_weekly_data.items():
            # Sort weeks
            sorted_weeks = sorted(weekly_data.keys())
            
            # Calculate rates
            formatted_weeks = []
            for week_key in sorted_weeks:
                week_data = weekly_data[week_key]
                connections_sent = week_data['connections_sent']
                connections_accepted = week_data['connections_accepted']
                messages_sent = week_data['messages_sent']
                message_replies = week_data['message_replies']
                
                acceptance_rate = (connections_accepted / connections_sent * 100) if connections_sent > 0 else 0
                reply_rate = (message_replies / messages_sent * 100) if messages_sent > 0 else 0
                
                formatted_weeks.append({
                    'week_start': week_key,
                    'connections_sent': connections_sent,
                    'connections_accepted': connections_accepted,
                    'acceptance_rate': round(acceptance_rate, 2),
                    'messages_sent': messages_sent,
                    'message_replies': message_replies,
                    'reply_rate': round(reply_rate, 2),
                    'open_conversations': week_data['open_conversations'],
                    'interested': week_data['interested'],
                    'leads_not_enrolled': week_data['leads_not_enrolled']
                })
            
            result['senders'][sender_name] = formatted_weeks
        
        return result
    
    def get_all_campaign_stats(self, days_back: int = 7) -> List[Dict]:
        """
        Get statistics for all campaigns
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of campaign statistics
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        start_str = start_date.strftime('%Y-%m-%d')
        end_str = end_date.strftime('%Y-%m-%d')
        
        campaigns = self.get_campaigns()
        all_stats = []
        
        for campaign in campaigns:
            campaign_id = campaign.get('id')
            if campaign_id:
                stats = self.get_campaign_stats(
                    campaign_id=campaign_id,
                    start_date=start_str,
                    end_date=end_str
                )
                
                # Combine campaign info with stats
                combined = {
                    'campaign_id': campaign_id,
                    'campaign_name': campaign.get('name', 'Unknown'),
                    'status': campaign.get('status', 'unknown'),
                    **stats
                }
                all_stats.append(combined)
        
        return all_stats
    
    def get_connections_data(self, days_back: int = 7) -> Dict:
        """
        Get LinkedIn connection request data
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Connection data summary
        """
        params = {
            'days_back': days_back
        }
        
        logger.info("Fetching connection data...")
        return self._make_request("connections", params=params)
    
    def get_messages_data(self, days_back: int = 7) -> Dict:
        """
        Get LinkedIn messages data
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Messages data summary
        """
        params = {
            'days_back': days_back
        }
        
        logger.info("Fetching messages data...")
        return self._make_request("messages", params=params)
    
    def get_summary_metrics(self, days_back: int = 7) -> Dict:
        """
        Get summary metrics across all campaigns
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            Summary metrics dictionary
        """
        campaigns_stats = self.get_all_campaign_stats(days_back=days_back)
        connections = self.get_connections_data(days_back=days_back)
        messages = self.get_messages_data(days_back=days_back)
        
        # Aggregate metrics
        total_invites_sent = sum(c.get('invites_sent', 0) for c in campaigns_stats)
        total_invites_accepted = sum(c.get('invites_accepted', 0) for c in campaigns_stats)
        total_messages_sent = sum(c.get('messages_sent', 0) for c in campaigns_stats)
        total_replies = sum(c.get('replies', 0) for c in campaigns_stats)
        
        acceptance_rate = (total_invites_accepted / total_invites_sent * 100) if total_invites_sent > 0 else 0
        reply_rate = (total_replies / total_messages_sent * 100) if total_messages_sent > 0 else 0
        
        return {
            'platform': 'LinkedIn (HeyReach)',
            'date_range_days': days_back,
            'total_campaigns': len(campaigns_stats),
            'total_invites_sent': total_invites_sent,
            'total_invites_accepted': total_invites_accepted,
            'acceptance_rate': round(acceptance_rate, 2),
            'total_messages_sent': total_messages_sent,
            'total_replies': total_replies,
            'reply_rate': round(reply_rate, 2),
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
            logger.info("✅ HeyReach API connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ HeyReach API connection failed: {e}")
            return False
