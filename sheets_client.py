"""
Google Sheets Client
Handles reading from and writing to Google Sheets
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google.auth.exceptions import GoogleAuthError
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)


class SheetsClient:
    """Client for interacting with Google Sheets"""
    
    def __init__(self, sheet_url: str, credentials_json: Optional[Dict] = None, 
                 oauth_token: Optional[Dict] = None):
        """
        Initialize Google Sheets client
        
        Args:
            sheet_url: Full Google Sheets URL
            credentials_json: Optional service account credentials as dict
            oauth_token: Optional OAuth 2.0 token dict with 'token', 'refresh_token', 'token_uri', 'client_id', 'client_secret', 'scopes'
        """
        self.sheet_url = sheet_url
        self.credentials_json = credentials_json
        self.oauth_token = oauth_token
        self.client = None
        self.spreadsheet = None
        
        # Extract spreadsheet ID from URL
        self.spreadsheet_id = self._extract_spreadsheet_id(sheet_url)
        if not self.spreadsheet_id:
            raise ValueError(f"Invalid Google Sheets URL: {sheet_url}")
        
        # Initialize client
        self._initialize_client()
    
    def _extract_spreadsheet_id(self, url: str) -> Optional[str]:
        """Extract spreadsheet ID from Google Sheets URL"""
        # Pattern: https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit...
        patterns = [
            r'/spreadsheets/d/([a-zA-Z0-9-_]+)',
            r'id=([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _initialize_client(self):
        """Initialize gspread client"""
        try:
            if self.oauth_token:
                # Use OAuth 2.0 credentials (for SaaS - user authorized access)
                creds = OAuthCredentials(
                    token=self.oauth_token.get('token'),
                    refresh_token=self.oauth_token.get('refresh_token'),
                    token_uri=self.oauth_token.get('token_uri', 'https://oauth2.googleapis.com/token'),
                    client_id=self.oauth_token.get('client_id'),
                    client_secret=self.oauth_token.get('client_secret'),
                    scopes=self.oauth_token.get('scopes', ['https://www.googleapis.com/auth/spreadsheets'])
                )
                
                # Refresh token if expired
                if creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    # Update token in oauth_token dict
                    self.oauth_token['token'] = creds.token
                
                self.client = gspread.authorize(creds)
                logger.info("Initialized Google Sheets client with OAuth 2.0 credentials")
            elif self.credentials_json:
                # Use service account credentials
                creds = ServiceAccountCredentials.from_service_account_info(
                    self.credentials_json,
                    scopes=['https://www.googleapis.com/auth/spreadsheets']
                )
                self.client = gspread.authorize(creds)
                logger.info("Initialized Google Sheets client with service account credentials")
            else:
                # Try to use default service account (from environment or default location)
                try:
                    self.client = gspread.service_account()
                    logger.info("Initialized Google Sheets client with default service account")
                except Exception as e:
                    logger.warning(f"No default service account found: {e}")
                    raise ValueError(
                        "No Google Sheets credentials provided. "
                        "Please authorize Google Sheets access or provide service account credentials."
                    )
            
            # Open spreadsheet
            self.spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            logger.info(f"Opened spreadsheet: {self.spreadsheet.title}")
        except GoogleAuthError as e:
            logger.error(f"Google authentication error: {e}")
            raise
        except Exception as e:
            logger.error(f"Error initializing Google Sheets client: {e}")
            raise
    
    def get_worksheet_names(self) -> List[str]:
        """Get list of all worksheet names in the spreadsheet"""
        try:
            worksheets = self.spreadsheet.worksheets()
            return [ws.title for ws in worksheets]
        except Exception as e:
            logger.error(f"Error getting worksheet names: {e}")
            return []
    
    def parse_sheet_structure(self, worksheet_name: str) -> Dict:
        """
        Parse a worksheet to understand its structure
        
        Returns:
            Dictionary with:
            - 'senders': List of sender info (name, row_index)
            - 'metrics': Dict mapping metric names to column indices
            - 'date_column': Column index for dates (if found)
            - 'year_cell': Cell reference for year (if found)
        """
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            all_values = worksheet.get_all_values()
            
            if not all_values:
                return {'senders': [], 'metrics': {}, 'date_column': None, 'year_cell': None}
            
            structure = {
                'senders': [],
                'metrics': {},
                'date_column': None,
                'year_cell': None,
                'data_start_row': None
            }
            
            # Common metric names to look for
            metric_names = [
                'connections sent', 'connections accepted', 'acceptance rate',
                'messages sent', 'message replies', 'reply rate',
                'open conversations', 'interested', 'leads not yet enrolled',
                'leads not enrolled'
            ]
            
            # Find year in first row
            if len(all_values) > 0:
                first_row = [str(cell).lower().strip() for cell in all_values[0]]
                for col_idx, cell in enumerate(first_row):
                    if cell.isdigit() and len(cell) == 4:  # Year
                        structure['year_cell'] = (1, col_idx + 1)  # 1-indexed
            
            # Find senders and metrics
            current_sender = None
            sender_row = None
            
            for row_idx, row in enumerate(all_values):
                row_lower = [str(cell).lower().strip() for cell in row]
                
                # Check if this row contains a sender name (usually in first column)
                first_cell = row[0].strip() if row else ""
                first_cell_lower = first_cell.lower()
                
                # Skip if it's a metric name or empty
                if not first_cell or first_cell_lower in metric_names:
                    continue
                
                # Check if it looks like a sender name (not a number, not a date, has letters)
                if first_cell and not first_cell.isdigit() and not re.match(r'^\d{1,2}/\d{1,2}$', first_cell):
                    # This might be a sender name
                    if current_sender and sender_row is not None:
                        # Save previous sender
                        structure['senders'].append({
                            'name': current_sender,
                            'row': sender_row + 1,  # 1-indexed
                            'row_index': sender_row  # 0-indexed
                        })
                    
                    current_sender = first_cell
                    sender_row = row_idx
                
                # Look for metrics in this row
                for col_idx, cell in enumerate(row_lower):
                    for metric in metric_names:
                        if metric in cell:
                            if metric not in structure['metrics']:
                                structure['metrics'][metric] = col_idx + 1  # 1-indexed
            
            # Add last sender
            if current_sender and sender_row is not None:
                structure['senders'].append({
                    'name': current_sender,
                    'row': sender_row + 1,
                    'row_index': sender_row
                })
            
            # Find data start row (first row after headers that might contain dates)
            for row_idx, row in enumerate(all_values):
                if row_idx == 0:
                    continue
                first_cell = row[0].strip() if row else ""
                # Check if it looks like a date (MM/DD format)
                if re.match(r'^\d{1,2}/\d{1,2}$', first_cell):
                    structure['data_start_row'] = row_idx + 1  # 1-indexed
                    structure['date_column'] = 1  # Dates in first column
                    break
            
            logger.info(f"Parsed sheet structure: {len(structure['senders'])} senders, {len(structure['metrics'])} metrics")
            return structure
            
        except Exception as e:
            logger.error(f"Error parsing sheet structure: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {'senders': [], 'metrics': {}, 'date_column': None, 'year_cell': None}
    
    def find_sender_row(self, worksheet_name: str, sender_name: str) -> Optional[int]:
        """Find the row index (1-indexed) for a sender name"""
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            all_values = worksheet.get_all_values()
            
            for row_idx, row in enumerate(all_values, start=1):
                if row and row[0].strip().lower() == sender_name.lower():
                    return row_idx
            
            return None
        except Exception as e:
            logger.error(f"Error finding sender row: {e}")
            return None
    
    def find_metric_column(self, worksheet_name: str, metric_name: str) -> Optional[int]:
        """Find the column index (1-indexed) for a metric"""
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            all_values = worksheet.get_all_values()
            
            metric_lower = metric_name.lower()
            metric_variations = [
                metric_lower,
                metric_lower.replace(' ', ''),
                metric_lower.replace('_', ' '),
            ]
            
            for row in all_values:
                for col_idx, cell in enumerate(row, start=1):
                    cell_lower = str(cell).lower().strip()
                    for variation in metric_variations:
                        if variation in cell_lower:
                            return col_idx
            
            return None
        except Exception as e:
            logger.error(f"Error finding metric column: {e}")
            return None
    
    def get_cell_value(self, worksheet_name: str, row: int, col: int) -> Optional[str]:
        """Get value from a specific cell (1-indexed)"""
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            cell = worksheet.cell(row, col)
            return cell.value
        except Exception as e:
            logger.error(f"Error getting cell value: {e}")
            return None
    
    def update_cell(self, worksheet_name: str, row: int, col: int, value: str):
        """Update a cell value (1-indexed)"""
        try:
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            worksheet.update_cell(row, col, value)
            logger.debug(f"Updated cell ({row}, {col}) in '{worksheet_name}' with value: {value}")
        except Exception as e:
            logger.error(f"Error updating cell: {e}")
            raise
    
    def populate_heyreach_data(self, worksheet_name: str, heyreach_data: Dict, 
                              date_range: Tuple[str, str]) -> Dict:
        """
        Populate HeyReach data into a worksheet
        
        Args:
            worksheet_name: Name of the worksheet
            heyreach_data: Data from HeyReach API (from get_sender_weekly_performance)
            date_range: Tuple of (start_date, end_date) in YYYY-MM-DD format
        
        Returns:
            Dictionary with results: {'updated': int, 'errors': List[str]}
        """
        results = {'updated': 0, 'errors': []}
        
        try:
            # Parse sheet structure
            structure = self.parse_sheet_structure(worksheet_name)
            
            if not structure['senders']:
                results['errors'].append(f"No senders found in worksheet '{worksheet_name}'")
                return results
            
            # Map HeyReach metrics to sheet metric names
            metric_mapping = {
                'connections_sent': ['connections sent'],
                'connections_accepted': ['connections accepted'],
                'acceptance_rate': ['acceptance rate'],
                'messages_sent': ['messages sent'],
                'message_replies': ['message replies'],
                'reply_rate': ['reply rate'],
                'open_conversations': ['open conversations'],
                'interested': ['interested'],
                'leads_not_enrolled': ['leads not yet enrolled', 'leads not enrolled']
            }
            
            # Process each sender in the sheet
            for sheet_sender in structure['senders']:
                sheet_sender_name = sheet_sender['name']
                sender_row = sheet_sender['row']
                
                # Find matching HeyReach sender
                heyreach_sender_data = None
                for heyreach_sender_name, weeks_data in heyreach_data.get('senders', {}).items():
                    # Try exact match first
                    if heyreach_sender_name.lower() == sheet_sender_name.lower():
                        heyreach_sender_data = weeks_data
                        break
                    # Try partial match
                    if sheet_sender_name.lower() in heyreach_sender_name.lower() or \
                       heyreach_sender_name.lower() in sheet_sender_name.lower():
                        heyreach_sender_data = weeks_data
                        break
                
                if not heyreach_sender_data:
                    logger.debug(f"No HeyReach data found for sender '{sheet_sender_name}'")
                    continue
                
                # Aggregate data across all weeks in the date range
                aggregated = {
                    'connections_sent': 0,
                    'connections_accepted': 0,
                    'messages_sent': 0,
                    'message_replies': 0,
                    'open_conversations': 0,
                    'interested': 0,
                    'leads_not_enrolled': 0
                }
                
                for week_data in heyreach_sender_data:
                    aggregated['connections_sent'] += week_data.get('connections_sent', 0) or 0
                    aggregated['connections_accepted'] += week_data.get('connections_accepted', 0) or 0
                    aggregated['messages_sent'] += week_data.get('messages_sent', 0) or 0
                    aggregated['message_replies'] += week_data.get('message_replies', 0) or 0
                    aggregated['open_conversations'] += week_data.get('open_conversations', 0) or 0
                    aggregated['interested'] += week_data.get('interested', 0) or 0
                    aggregated['leads_not_enrolled'] += week_data.get('leads_not_enrolled', 0) or 0
                
                # Calculate rates
                acceptance_rate = 0
                if aggregated['connections_sent'] > 0:
                    acceptance_rate = (aggregated['connections_accepted'] / aggregated['connections_sent']) * 100
                
                reply_rate = 0
                if aggregated['messages_sent'] > 0:
                    reply_rate = (aggregated['message_replies'] / aggregated['messages_sent']) * 100
                
                # Update cells only if they're empty or need updating
                # Find metric columns and update values
                for heyreach_metric, sheet_metric_names in metric_mapping.items():
                    # Find the column for this metric
                    metric_col = None
                    for sheet_metric_name in sheet_metric_names:
                        for metric_name, col_idx in structure['metrics'].items():
                            if sheet_metric_name in metric_name:
                                metric_col = col_idx
                                break
                        if metric_col:
                            break
                    
                    if not metric_col:
                        continue
                    
                    # Get current value
                    current_value = self.get_cell_value(worksheet_name, sender_row, metric_col)
                    
                    # Determine what value to write
                    if heyreach_metric == 'acceptance_rate':
                        value_to_write = f"{acceptance_rate:.2f}%"
                    elif heyreach_metric == 'reply_rate':
                        value_to_write = f"{reply_rate:.2f}%"
                    else:
                        value_to_write = str(aggregated[heyreach_metric])
                    
                    # Only update if cell is empty or different
                    if not current_value or current_value.strip() == '':
                        try:
                            self.update_cell(worksheet_name, sender_row, metric_col, value_to_write)
                            results['updated'] += 1
                            logger.info(f"Updated {sheet_sender_name} - {heyreach_metric}: {value_to_write}")
                        except Exception as e:
                            error_msg = f"Error updating {sheet_sender_name} - {heyreach_metric}: {e}"
                            results['errors'].append(error_msg)
                            logger.error(error_msg)
                    else:
                        logger.debug(f"Skipping {sheet_sender_name} - {heyreach_metric} (already has value: {current_value})")
            
            logger.info(f"Completed populating worksheet '{worksheet_name}': {results['updated']} cells updated")
            return results
            
        except Exception as e:
            error_msg = f"Error populating HeyReach data: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            return results

