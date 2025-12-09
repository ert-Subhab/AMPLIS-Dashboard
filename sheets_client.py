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
    
    def _normalize_date_string(self, value: str) -> Optional[str]:
        """
        Normalize a sheet date header into ISO format (YYYY-MM-DD).
        Supports common sheet date formats like YYYY-MM-DD, MM/DD/YYYY, MM/DD/YY, and MM/DD.
        """
        if value is None:
            return None
        
        value_str = str(value).strip()
        if not value_str:
            return None
        
        # Try several known formats
        date_formats = ['%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%Y/%m/%d']
        for fmt in date_formats:
            try:
                return datetime.strptime(value_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        # Handle MM/DD without a year by assuming current year
        if re.match(r'^\d{1,2}/\d{1,2}$', value_str):
            try:
                month, day = value_str.split('/')
                today_year = datetime.now().year
                parsed = datetime(today_year, int(month), int(day))
                return parsed.strftime('%Y-%m-%d')
            except Exception:
                return None
        
        return None
    
    def _find_or_create_date_column(self, worksheet, structure: Dict, target_date: str) -> Optional[int]:
        """
        Find the column for the target date; if missing, append a new column with that date header.
        """
        norm = self._normalize_date_string(target_date)
        if not norm:
            return None
        
        date_columns = structure.get('date_columns', {})
        date_row = structure.get('date_row') or 1
        
        # Return existing column if found
        if norm in date_columns:
            return date_columns[norm]
        
        try:
            # Append a new column at the end
            new_col_index = worksheet.col_count + 1
            worksheet.add_cols(1)
            worksheet.update_cell(date_row, new_col_index, norm)
            
            # Track the new column in the local structure for downstream writes
            date_columns[norm] = new_col_index
            structure['date_columns'] = date_columns
            
            logger.info(f"Added new date column {norm} at index {new_col_index}")
            return new_col_index
        except Exception as e:
            logger.error(f"Error creating date column for {norm}: {e}")
            return None
    
    def _get_metric_rows_for_sender(self, all_values: List[List[str]], start_row_idx: int, end_row_idx: int,
                                    metric_mapping: Dict[str, List[str]]) -> Dict[str, int]:
        """
        Given the full sheet values and the row range for a sender block, find the row index for each metric.
        Returns 1-indexed row numbers for each metric.
        """
        metric_rows = {}
        for row_idx in range(start_row_idx + 1, end_row_idx):
            if row_idx >= len(all_values):
                break
            row = all_values[row_idx] if row_idx < len(all_values) else []
            first_cell = row[0].strip().lower() if row and row[0] else ""
            
            for metric_key, metric_names in metric_mapping.items():
                if metric_key in metric_rows:
                    continue
                for name in metric_names:
                    if name in first_cell:
                        metric_rows[metric_key] = row_idx + 1  # 1-indexed
                        break
        return metric_rows
    
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
                'data_start_row': None,
                'date_columns': {},
                'date_row': None
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
            
            # Detect date columns (first row that has date-like values)
            for row_idx, row in enumerate(all_values):
                for col_idx, cell in enumerate(row):
                    norm = self._normalize_date_string(cell)
                    if norm:
                        if structure['date_row'] is None:
                            structure['date_row'] = row_idx + 1  # 1-indexed
                        structure['date_columns'][norm] = col_idx + 1  # 1-indexed
                if structure['date_columns']:
                    # Assume first row with any date headers is the date row
                    break
            
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
            worksheet = self.spreadsheet.worksheet(worksheet_name)
            all_values = worksheet.get_all_values()
            
            # Parse sheet structure (date columns, senders, metric markers)
            structure = self.parse_sheet_structure(worksheet_name)
            
            if not structure['senders']:
                results['errors'].append(f"No senders found in worksheet '{worksheet_name}'")
                return results
            
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
            
            # Determine which sender data to use based on worksheet title (client name)
            sender_data_map = heyreach_data.get('senders', {}) or {}
            clients_map = heyreach_data.get('clients', {}) or {}
            
            # If a client name matches (exact or partial) the worksheet title, scope to that client
            worksheet_title = worksheet_name.lower().strip()
            for client_name, client_senders in clients_map.items():
                client_title = str(client_name).lower().strip()
                if client_title == worksheet_title or client_title in worksheet_title or worksheet_title in client_title:
                    sender_data_map = client_senders or {}
                    break
            
            # Process each sender in the sheet
            for idx, sheet_sender in enumerate(structure['senders']):
                sheet_sender_name = sheet_sender['name']
                sender_row = sheet_sender['row']
                
                # Determine the block range for this sender (until next sender or end)
                next_sender_row = (
                    structure['senders'][idx + 1]['row']
                    if idx + 1 < len(structure['senders'])
                    else len(all_values) + 1  # 1-indexed end
                )
                
                # Locate metric rows inside the sender block
                metric_rows = self._get_metric_rows_for_sender(
                    all_values=all_values,
                    start_row_idx=sender_row - 1,  # convert to 0-index
                    end_row_idx=next_sender_row - 1,  # exclusive, 0-index
                    metric_mapping=metric_mapping
                )
                
                # Find matching HeyReach sender
                heyreach_sender_data = None
                for heyreach_sender_name, weeks_data in sender_data_map.items():
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
                
                # Populate each week separately into the correct date column
                for week_data in heyreach_sender_data:
                    week_end = week_data.get('week_end') or week_data.get('week_end_date') or week_data.get('weekStart')
                    if not week_end:
                        continue
                    
                    date_col = self._find_or_create_date_column(worksheet, structure, week_end)
                    if not date_col:
                        continue
                    
                    # Calculate rates for this week
                    connections_sent = week_data.get('connections_sent', 0) or 0
                    connections_accepted = week_data.get('connections_accepted', 0) or 0
                    messages_sent = week_data.get('messages_sent', 0) or 0
                    message_replies = week_data.get('message_replies', 0) or 0
                    
                    acceptance_rate = (connections_accepted / connections_sent * 100) if connections_sent > 0 else 0
                    reply_rate = (message_replies / messages_sent * 100) if messages_sent > 0 else 0
                    
                    metric_values = {
                        'connections_sent': int(connections_sent),
                        'connections_accepted': int(connections_accepted),
                        'acceptance_rate': f"{acceptance_rate:.2f}%",
                        'messages_sent': int(messages_sent),
                        'message_replies': int(message_replies),
                        'reply_rate': f"{reply_rate:.2f}%",
                        'open_conversations': int(week_data.get('open_conversations', 0) or 0),
                        'interested': int(week_data.get('interested', 0) or 0),
                        'leads_not_enrolled': int(week_data.get('leads_not_enrolled', 0) or 0)
                    }
                    
                    # Write values into metric rows for this sender/week
                    for heyreach_metric, value_to_write in metric_values.items():
                        metric_row = metric_rows.get(heyreach_metric)
                        if not metric_row:
                            continue
                        
                        current_value = self.get_cell_value(worksheet_name, metric_row, date_col)
                        
                        # Only update if empty to avoid overwriting
                        if not current_value or current_value.strip() == '':
                            try:
                                self.update_cell(worksheet_name, metric_row, date_col, str(value_to_write))
                                results['updated'] += 1
                                logger.info(f"Updated {sheet_sender_name} week {week_end} - {heyreach_metric}: {value_to_write}")
                            except Exception as e:
                                error_msg = f"Error updating {sheet_sender_name} week {week_end} - {heyreach_metric}: {e}"
                                results['errors'].append(error_msg)
                                logger.error(error_msg)
                        else:
                            logger.debug(f"Skipping {sheet_sender_name} week {week_end} - {heyreach_metric} (already has value: {current_value})")
            
            logger.info(f"Completed populating worksheet '{worksheet_name}': {results['updated']} cells updated")
            return results
            
        except Exception as e:
            error_msg = f"Error populating HeyReach data: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
            import traceback
            logger.error(traceback.format_exc())
            return results

