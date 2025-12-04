#!/usr/bin/env python3
"""
HeyReach Performance Dashboard
Flask web application for HeyReach performance tracking
"""

import yaml
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, session, redirect
from flask_cors import CORS
import logging
from heyreach_client import HeyReachClient
from sheets_client import SheetsClient
from google_oauth import (
    get_authorization_url, handle_oauth_callback, 
    get_stored_credentials, is_authorized, revoke_authorization, is_configured
)
import secrets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)  # Generate a secret key for sessions
CORS(app)

# Global client instance
heyreach_client = None


def load_config():
    """Load configuration from environment variables (production) or config.yaml (local)"""
    try:
        print("load_config(): Starting...", flush=True)
        config = {}
        
        # Try environment variables first (for production deployment)
        api_key = os.environ.get('HEYREACH_API_KEY')
        print(f"load_config(): HEYREACH_API_KEY from env: {bool(api_key)}", flush=True)
        
        if api_key:
            print("load_config(): API key found, loading from environment variables", flush=True)
            logger.info("Loading configuration from environment variables (production mode)")
            base_url = os.environ.get('HEYREACH_BASE_URL', 'https://api.heyreach.io')
            print(f"load_config(): Base URL: {base_url}", flush=True)
            
            # Build config from environment variables
            config['heyreach'] = {
                'api_key': api_key,
                'base_url': base_url,
                'sender_ids': [],
                'sender_names': {},
                'client_groups': {}
            }
            print("load_config(): Base config created", flush=True)
            
            # Try to load sender_ids from environment variable (JSON format)
            sender_ids_str = os.environ.get('HEYREACH_SENDER_IDS')
            if sender_ids_str and sender_ids_str.strip():  # Only process if not empty
                try:
                    import json
                    sender_ids = json.loads(sender_ids_str)
                    if isinstance(sender_ids, list) and len(sender_ids) > 0:
                        config['heyreach']['sender_ids'] = sender_ids
                        print(f"load_config(): Loaded {len(sender_ids)} sender IDs from environment", flush=True)
                        logger.info(f"Loaded {len(sender_ids)} sender IDs from HEYREACH_SENDER_IDS environment variable")
                    else:
                        print("load_config(): HEYREACH_SENDER_IDS is empty list, skipping", flush=True)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse HEYREACH_SENDER_IDS from environment: {e}")
                    print(f"load_config(): Failed to parse HEYREACH_SENDER_IDS: {e}", flush=True)
            else:
                print("load_config(): HEYREACH_SENDER_IDS not set or empty", flush=True)
            
            # Try to load sender_names from environment variable (JSON format)
            sender_names_str = os.environ.get('HEYREACH_SENDER_NAMES')
            if sender_names_str and sender_names_str.strip():  # Only process if not empty
                try:
                    import json
                    sender_names = json.loads(sender_names_str)
                    if isinstance(sender_names, dict) and len(sender_names) > 0:
                        # Convert string keys to integers
                        processed_sender_names = {}
                        for key, value in sender_names.items():
                            try:
                                key_int = int(key) if isinstance(key, str) else key
                                processed_sender_names[key_int] = value
                            except (ValueError, TypeError):
                                processed_sender_names[key] = value
                        config['heyreach']['sender_names'] = processed_sender_names
                        print(f"load_config(): Loaded {len(processed_sender_names)} sender names from environment", flush=True)
                        logger.info(f"Loaded {len(processed_sender_names)} sender names from HEYREACH_SENDER_NAMES environment variable")
                    else:
                        print("load_config(): HEYREACH_SENDER_NAMES is empty dict, skipping", flush=True)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse HEYREACH_SENDER_NAMES from environment: {e}")
                    print(f"load_config(): Failed to parse HEYREACH_SENDER_NAMES: {e}", flush=True)
            else:
                print("load_config(): HEYREACH_SENDER_NAMES not set or empty", flush=True)
            
            # Try to load client_groups from environment variable (JSON format)
            client_groups_str = os.environ.get('HEYREACH_CLIENT_GROUPS')
            if client_groups_str and client_groups_str.strip():  # Only process if not empty
                try:
                    import json
                    client_groups = json.loads(client_groups_str)
                    if isinstance(client_groups, dict) and len(client_groups) > 0:
                        config['heyreach']['client_groups'] = client_groups
                        print(f"load_config(): Loaded {len(client_groups)} client groups from environment", flush=True)
                        logger.info(f"Loaded {len(client_groups)} client groups from HEYREACH_CLIENT_GROUPS environment variable")
                    else:
                        print("load_config(): HEYREACH_CLIENT_GROUPS is empty dict, skipping", flush=True)
                except (json.JSONDecodeError, TypeError) as e:
                    logger.warning(f"Failed to parse HEYREACH_CLIENT_GROUPS from environment: {e}")
                    print(f"load_config(): Failed to parse HEYREACH_CLIENT_GROUPS: {e}", flush=True)
            else:
                print("load_config(): HEYREACH_CLIENT_GROUPS not set or empty", flush=True)
            
            print(f"load_config(): Returning config with api_key: {bool(config.get('heyreach', {}).get('api_key'))}, sender_ids: {len(config.get('heyreach', {}).get('sender_ids', []))}", flush=True)
            return config
        
        # Fallback to config.yaml (for local development)
        print("load_config(): No API key in environment, trying config.yaml...", flush=True)
        try:
            logger.info("Loading configuration from config.yaml (local development mode)")
            with open('config.yaml', 'r') as f:
                config = yaml.safe_load(f)
            print("load_config(): Config loaded from config.yaml", flush=True)
            return config
        except FileNotFoundError:
            error_msg = "config.yaml not found and no environment variables set!"
            print(f"load_config(): ERROR - {error_msg}", flush=True)
            logger.error(error_msg)
            return None
        except Exception as e:
            error_msg = f"Error loading config: {e}"
            print(f"load_config(): ERROR - {error_msg}", flush=True)
            import traceback
            print(f"load_config(): TRACEBACK:\n{traceback.format_exc()}", flush=True)
            logger.error(error_msg)
            return None
    except Exception as e:
        error_msg = f"Exception in load_config(): {e}"
        print(f"load_config(): EXCEPTION - {error_msg}", flush=True)
        import traceback
        print(f"load_config(): TRACEBACK:\n{traceback.format_exc()}", flush=True)
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return None


def init_client():
    """Initialize HeyReach client"""
    global heyreach_client
    try:
        print("init_client(): Starting...", flush=True)
        config = load_config()
        if not config:
            print("init_client(): load_config() returned None", flush=True)
            logger.error("init_client(): load_config() returned None")
            return False
        
        print("init_client(): Config loaded successfully", flush=True)
        heyreach_config = config.get('heyreach', {})
        api_key = heyreach_config.get('api_key')
        base_url = heyreach_config.get('base_url', 'https://api.heyreach.io')
        
        print(f"init_client(): API key present: {bool(api_key)}", flush=True)
        print(f"init_client(): Base URL: {base_url}", flush=True)
        
        # Get manually configured sender IDs if available
        sender_ids = heyreach_config.get('sender_ids', [])
        sender_names = heyreach_config.get('sender_names', {})
        client_groups = heyreach_config.get('client_groups', {})
        
        print(f"init_client(): Sender IDs: {len(sender_ids)}", flush=True)
        print(f"init_client(): Sender names: {len(sender_names)}", flush=True)
        print(f"init_client(): Client groups: {len(client_groups)}", flush=True)
        
        # Convert sender_names keys to integers if they're strings
        if sender_names:
            processed_sender_names = {}
            for key, value in sender_names.items():
                try:
                    key_int = int(key) if isinstance(key, str) else key
                    processed_sender_names[key_int] = value
                except (ValueError, TypeError):
                    processed_sender_names[key] = value
            sender_names = processed_sender_names
        
        if not api_key:
            error_msg = "HeyReach API key not found in config.yaml or environment variables"
            print(f"init_client(): ERROR - {error_msg}", flush=True)
            logger.error(error_msg)
            logger.error("Please set HEYREACH_API_KEY environment variable")
            return False
        
        print("init_client(): Creating HeyReachClient instance...", flush=True)
        try:
            heyreach_client = HeyReachClient(
                api_key=api_key, 
                base_url=base_url,
                sender_ids=sender_ids,
                sender_names=sender_names,
                client_groups=client_groups
            )
            print("init_client(): [OK] HeyReachClient created successfully!", flush=True)
            logger.info("[OK] HeyReach client initialized successfully")
            if sender_ids:
                logger.info(f"[INFO] Using {len(sender_ids)} manually configured sender IDs")
                print(f"init_client(): Using {len(sender_ids)} sender IDs", flush=True)
            if client_groups:
                logger.info(f"[INFO] Loaded {len(client_groups)} client groups")
                print(f"init_client(): Loaded {len(client_groups)} client groups", flush=True)
            return True
        except Exception as client_error:
            error_msg = f"Error creating HeyReachClient: {client_error}"
            print(f"init_client(): EXCEPTION - {error_msg}", flush=True)
            import traceback
            traceback_str = traceback.format_exc()
            print(f"init_client(): TRACEBACK:\n{traceback_str}", flush=True)
            logger.error(error_msg)
            logger.error(traceback_str)
            return False
    except Exception as e:
        error_msg = f"Error in init_client(): {e}"
        print(f"init_client(): OUTER EXCEPTION - {error_msg}", flush=True)
        import traceback
        traceback_str = traceback.format_exc()
        print(f"init_client(): TRACEBACK:\n{traceback_str}", flush=True)
        logger.error(error_msg)
        logger.error(traceback_str)
        return False


# Initialize client when app starts (for production deployment with gunicorn)
def initialize_app():
    """Initialize the HeyReach client when the app starts"""
    global heyreach_client
    try:
        # Use print() to ensure logs are visible in Render
        print("=" * 50, flush=True)
        print("INITIALIZING HEYREACH CLIENT ON APP STARTUP", flush=True)
        print("=" * 50, flush=True)
        
        api_key_present = bool(os.environ.get('HEYREACH_API_KEY'))
        base_url = os.environ.get('HEYREACH_BASE_URL', 'Not set')
        
        print(f"HEYREACH_API_KEY present: {api_key_present}", flush=True)
        print(f"HEYREACH_BASE_URL: {base_url}", flush=True)
        
        logger.info("=" * 50)
        logger.info("Initializing HeyReach client on app startup...")
        logger.info(f"HEYREACH_API_KEY present: {api_key_present}")
        logger.info(f"HEYREACH_BASE_URL: {base_url}")
        
        if not heyreach_client:
            print("Client not initialized yet, calling init_client()...", flush=True)
            if not init_client():
                print("=" * 50, flush=True)
                print("CRITICAL: Failed to initialize HeyReach client!", flush=True)
                print("Check environment variables: HEYREACH_API_KEY and HEYREACH_BASE_URL", flush=True)
                print("=" * 50, flush=True)
                logger.error("=" * 50)
                logger.error("CRITICAL: Failed to initialize HeyReach client on app startup")
                logger.error("The dashboard will not function without a valid client.")
                logger.error("Check environment variables: HEYREACH_API_KEY and HEYREACH_BASE_URL")
                logger.error("=" * 50)
            else:
                print("=" * 50, flush=True)
                print("[OK] HeyReach client initialized successfully!", flush=True)
                print("=" * 50, flush=True)
                logger.info("=" * 50)
                logger.info("[OK] HeyReach client initialized successfully on app startup")
                logger.info("=" * 50)
        else:
            print("HeyReach client already initialized", flush=True)
            logger.info("HeyReach client already initialized")
    except Exception as e:
        print(f"EXCEPTION during app initialization: {e}", flush=True)
        import traceback
        print(traceback.format_exc(), flush=True)
        logger.error(f"Exception during app initialization: {e}")
        logger.error(traceback.format_exc())


# Initialize client when app is imported (for gunicorn/production)
# This happens after all functions are defined
try:
    print("APP.PY: Starting initialization...", flush=True)
    initialize_app()
    print("APP.PY: Initialization complete.", flush=True)
except Exception as e:
    print(f"APP.PY: Warning - initialization failed during import: {e}", flush=True)
    logger.warning(f"Initialization failed during import: {e}")


@app.route('/')
def index():
    """Render dashboard homepage"""
    return render_template('dashboard.html')


@app.route('/static/google_apps_script_template.js')
def apps_script_template():
    """Serve the Google Apps Script template"""
    try:
        with open('static/google_apps_script_template.js', 'r') as f:
            return f.read(), 200, {'Content-Type': 'application/javascript'}
    except FileNotFoundError:
        return "// Apps Script template not found", 404


@app.route('/api/initialize', methods=['POST'])
def initialize_api_key():
    """Initialize HeyReach client with API key from request"""
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key is required'}), 400
        
        # Store API key in session
        session['heyreach_api_key'] = api_key
        session['heyreach_base_url'] = data.get('base_url', 'https://api.heyreach.io')
        
        # Load config.yaml to get sender names and client groups mapping
        config = load_config()
        sender_names = {}
        sender_ids = []
        client_groups = {}
        
        if config and 'heyreach' in config:
            sender_names = config['heyreach'].get('sender_names', {})
            sender_ids = config['heyreach'].get('sender_ids', [])
            client_groups = config['heyreach'].get('client_groups', {})
            logger.info(f"Loaded {len(sender_names)} sender names and {len(client_groups)} client groups from config")
        
        # Store in session for later use
        session['sender_names'] = sender_names
        session['sender_ids'] = sender_ids
        session['client_groups'] = client_groups
        
        # Create a temporary client to test the connection and fetch senders
        # Pass sender_names and client_groups for mapping, but force API fetch
        temp_client = HeyReachClient(
            api_key=api_key,
            base_url=session['heyreach_base_url'],
            sender_ids=[],  # Empty list to force API fetch
            sender_names=sender_names,  # For mapping IDs to names
            client_groups=client_groups  # For client grouping
        )
        
        # Test connection by fetching accounts from API
        # force_api=True ensures we fetch from API, not use manual config
        accounts = temp_client.get_linkedin_accounts(force_api=True)
        
        if not accounts:
            logger.warning("No LinkedIn accounts returned from API")
            return jsonify({
                'success': True,
                'senders': [{'id': 'all', 'name': 'All'}],
                'warning': 'No senders found. API key is valid but no accounts available.'
            }), 200
        
        # Map API sender IDs to names from config.yaml
        senders = []
        for acc in accounts:
            sender_id = acc.get('id')
            if not sender_id:
                continue
            
            # Convert sender_id to int for lookup if needed (config.yaml uses int keys)
            sender_id_int = int(sender_id) if sender_id and isinstance(sender_id, (str, float)) else sender_id
            
            # Try to get name from config.yaml first (try both int and original format), then from API response
            sender_name = (
                sender_names.get(sender_id_int) or 
                sender_names.get(sender_id) or 
                acc.get('linkedInUserListName') or 
                acc.get('name') or 
                f'Sender {sender_id}'
            )
            
            senders.append({
                'id': sender_id,
                'name': sender_name
            })
        
        # Add "All" option
        senders.insert(0, {'id': 'all', 'name': 'All'})
        
        logger.info(f"Initialized API key and found {len(senders)} senders (including 'All' option)")
        return jsonify({
            'success': True,
            'senders': senders,
            'message': f'Successfully connected! Found {len(senders) - 1} sender(s).'
        })
    except Exception as e:
        logger.error(f"Error initializing API key: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to initialize API key: {str(e)}'}), 500


@app.route('/api/senders', methods=['GET'])
def get_senders():
    """Get list of all senders (LinkedIn accounts)"""
    try:
        # Check if API key is in session
        api_key = session.get('heyreach_api_key')
        
        if not api_key:
            # Fallback to global client if available
            if not heyreach_client:
                error_msg = 'HeyReach API key not set. Please enter your API key first.'
                logger.error(error_msg)
                return jsonify({'error': error_msg, 'senders': [{'id': 'all', 'name': 'All'}]}), 200
            
            accounts = heyreach_client.get_linkedin_accounts()
        else:
            # Use session API key
            base_url = session.get('heyreach_base_url', 'https://api.heyreach.io')
            sender_names = session.get('sender_names', {})
            sender_ids = session.get('sender_ids', [])
            client_groups = session.get('client_groups', {})
            
            temp_client = HeyReachClient(
                api_key=api_key,
                base_url=base_url,
                sender_ids=[],  # Empty to force API fetch
                sender_names=sender_names,
                client_groups=client_groups
            )
            accounts = temp_client.get_linkedin_accounts(force_api=True)
        
        if not accounts:
            logger.warning("No LinkedIn accounts returned from API")
            return jsonify({'senders': [{'id': 'all', 'name': 'All'}], 'warning': 'No senders found'}), 200
        
        # Map sender IDs to names from config.yaml
        sender_names = session.get('sender_names', {})
        
        senders = []
        for acc in accounts:
            sender_id = acc.get('id')
            if not sender_id:
                continue
            
            # Convert sender_id to int for lookup if needed (config.yaml uses int keys)
            sender_id_int = int(sender_id) if sender_id and isinstance(sender_id, (str, float)) else sender_id
            
            # Try to get name from config.yaml first, then from API response
            sender_name = (
                sender_names.get(sender_id_int) or 
                sender_names.get(sender_id) or 
                acc.get('linkedInUserListName') or 
                acc.get('name') or 
                f'Sender {sender_id}'
            )
            
            senders.append({
                'id': sender_id,
                'name': sender_name
            })
        
        # Add "All" option
        senders.insert(0, {'id': 'all', 'name': 'All'})
        
        logger.info(f"Returning {len(senders)} senders")
        return jsonify({'senders': senders})
    except Exception as e:
        logger.error(f"Error fetching senders: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e), 'senders': [{'id': 'all', 'name': 'All'}]}), 200


def get_client_for_request():
    """Get HeyReach client from session or global"""
    api_key = session.get('heyreach_api_key')
    
    if api_key:
        base_url = session.get('heyreach_base_url', 'https://api.heyreach.io')
        # Get sender mapping from session (loaded from config.yaml during initialization)
        sender_names_raw = session.get('sender_names', {})
        sender_ids = session.get('sender_ids', [])
        client_groups = session.get('client_groups', {})
        
        # CRITICAL: Flask session serializes to JSON, converting int keys to strings
        # Convert string keys back to integers for proper lookup
        sender_names = {}
        for key, value in sender_names_raw.items():
            try:
                key_int = int(key) if isinstance(key, str) else key
                sender_names[key_int] = value
            except (ValueError, TypeError):
                sender_names[key] = value
        
        return HeyReachClient(
            api_key=api_key,
            base_url=base_url,
            sender_ids=sender_ids,
            sender_names=sender_names,
            client_groups=client_groups
        )
    elif heyreach_client:
        return heyreach_client
    else:
        return None


@app.route('/api/performance', methods=['GET'])
def get_performance():
    """Get performance data for selected sender and date range"""
    try:
        # Get client from session or global
        client = get_client_for_request()
        
        if not client:
            error_msg = 'HeyReach API key not set. Please enter your API key first.'
            logger.error(error_msg)
            print(f"ERROR: {error_msg}", flush=True)
            return jsonify({
                'error': error_msg,
                'start_date': request.args.get('start_date', ''),
                'end_date': request.args.get('end_date', ''),
                'senders': {},
                'clients': {}
            }), 200
        
        # Get query parameters
        sender_id = request.args.get('sender_id', 'all')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # If no dates provided, default to last 7 days (instead of 12 weeks)
        if not start_date or not end_date:
            end_date_obj = datetime.now()
            start_date_obj = end_date_obj - timedelta(days=7)  # Changed from weeks=12
            start_date = start_date_obj.strftime('%Y-%m-%d')
            end_date = end_date_obj.strftime('%Y-%m-%d')
        
        # Convert sender_id
        sender_id_param = None if sender_id == 'all' else sender_id
        
        # Get performance data
        try:
            performance_data = client.get_sender_weekly_performance(
                sender_id=sender_id_param,
                start_date=start_date,
                end_date=end_date
            )
            
            # Ensure we have a valid response structure
            if not performance_data:
                return jsonify({
                    'error': 'No data returned from HeyReach API',
                    'start_date': start_date,
                    'end_date': end_date,
                    'senders': {}
                }), 200
            
            return jsonify(performance_data)
        except Exception as api_error:
            logger.error(f"Error in get_sender_weekly_performance: {api_error}")
            import traceback
            traceback.print_exc()
            # Return empty data structure instead of error to allow dashboard to display
            return jsonify({
                'error': f'Error fetching performance data: {str(api_error)}',
                'start_date': start_date,
                'end_date': end_date,
                'senders': {}
            }), 200
    except Exception as e:
        logger.error(f"Error in performance endpoint: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/summary', methods=['GET'])
def get_summary():
    """Get summary metrics for the dashboard"""
    try:
        # Get client from session or global
        client = get_client_for_request()
        
        if not client:
            return jsonify({'error': 'HeyReach API key not set. Please enter your API key first.'}), 500
        
        # Get query parameters
        sender_id = request.args.get('sender_id', 'all')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # If no dates provided, default to last 7 days
        if not start_date or not end_date:
            end_date_obj = datetime.now()
            start_date_obj = end_date_obj - timedelta(days=7)
            start_date = start_date_obj.strftime('%Y-%m-%d')
            end_date = end_date_obj.strftime('%Y-%m-%d')
        
        # Get performance data
        performance_data = client.get_sender_weekly_performance(
            sender_id=None if sender_id == 'all' else sender_id,
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate summary metrics
        summary = {
            'total_senders': len(performance_data.get('senders', {})),
            'date_range': {
                'start': performance_data.get('start_date'),
                'end': performance_data.get('end_date')
            },
            'total_connections_sent': 0,
            'total_connections_accepted': 0,
            'total_messages_sent': 0,
            'total_message_replies': 0,
            'total_open_conversations': 0,
            'total_interested': 0,
            'total_leads_not_enrolled': 0
        }
        
        for sender_name, weeks_data in performance_data.get('senders', {}).items():
            for week_data in weeks_data:
                summary['total_connections_sent'] += week_data.get('connections_sent', 0)
                summary['total_connections_accepted'] += week_data.get('connections_accepted', 0)
                summary['total_messages_sent'] += week_data.get('messages_sent', 0)
                summary['total_message_replies'] += week_data.get('message_replies', 0)
                summary['total_open_conversations'] += week_data.get('open_conversations', 0)
                summary['total_interested'] += week_data.get('interested', 0)
                summary['total_leads_not_enrolled'] += week_data.get('leads_not_enrolled', 0)
        
        # Calculate rates
        if summary['total_connections_sent'] > 0:
            summary['overall_acceptance_rate'] = round(
                (summary['total_connections_accepted'] / summary['total_connections_sent']) * 100, 2
            )
        else:
            summary['overall_acceptance_rate'] = 0
        
        if summary['total_messages_sent'] > 0:
            summary['overall_reply_rate'] = round(
                (summary['total_message_replies'] / summary['total_messages_sent']) * 100, 2
            )
        else:
            summary['overall_reply_rate'] = 0
        
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error fetching summary: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/google/save-credentials', methods=['POST'])
def save_oauth_credentials():
    """Save user's OAuth credentials to session"""
    try:
        data = request.get_json()
        client_id = data.get('client_id', '').strip()
        client_secret = data.get('client_secret', '').strip()
        
        if not client_id or not client_secret:
            return jsonify({'error': 'Client ID and Client Secret are required'}), 400
        
        # Store in session
        session['google_oauth_client_id'] = client_id
        session['google_oauth_client_secret'] = client_secret
        
        logger.info("OAuth credentials saved to session")
        return jsonify({
            'success': True,
            'message': 'OAuth credentials saved. You can now connect your Google account.'
        })
    except Exception as e:
        logger.error(f"Error saving OAuth credentials: {e}")
        return jsonify({'error': f'Failed to save credentials: {str(e)}'}), 500


@app.route('/api/google/authorize', methods=['GET'])
def google_authorize():
    """Initiate Google OAuth authorization using user's credentials"""
    try:
        # Get user's credentials from session
        client_id = session.get('google_oauth_client_id')
        client_secret = session.get('google_oauth_client_secret')
        
        if not client_id or not client_secret:
            return jsonify({
                'error': 'OAuth credentials not found',
                'configured': False,
                'message': 'Please save your Google OAuth credentials first.'
            }), 400
        
        # Get redirect URI from request or use default
        redirect_uri = request.args.get('redirect_uri') or request.url_root.rstrip('/') + '/api/google/callback'
        
        authorization_url = get_authorization_url(client_id, client_secret, redirect_uri)
        return jsonify({'authorization_url': authorization_url})
    except Exception as e:
        logger.error(f"Error initiating OAuth: {e}")
        return jsonify({
            'error': f'Failed to initiate Google authorization: {str(e)}',
            'configured': is_configured()
        }), 500


@app.route('/api/google/callback', methods=['GET'])
def google_callback():
    """Handle Google OAuth callback"""
    try:
        code = request.args.get('code')
        state = request.args.get('state')
        
        if not code:
            return jsonify({'error': 'Authorization code not provided'}), 400
        
        token_info = handle_oauth_callback(code, state)
        
        # Redirect to dashboard with success message
        return redirect('/?google_connected=1')
    except Exception as e:
        logger.error(f"Error handling OAuth callback: {e}")
        return redirect('/?google_error=1')


@app.route('/api/google/status', methods=['GET'])
def google_status():
    """Check Google Sheets authorization status"""
    # Check if user has provided OAuth credentials
    has_credentials = bool(session.get('google_oauth_client_id'))
    authorized = is_authorized()
    
    # Get redirect URI for help
    redirect_uri = request.url_root.rstrip('/') + '/api/google/callback'
    
    if not has_credentials:
        return jsonify({
            'authorized': False,
            'configured': False,
            'has_credentials': False,
            'redirect_uri': redirect_uri,
            'message': 'Please provide your Google OAuth credentials first.'
        })
    
    return jsonify({
        'authorized': authorized,
        'configured': True,
        'has_credentials': True,
        'redirect_uri': redirect_uri,
        'message': 'Google Sheets connected' if authorized else 'OAuth credentials saved. Connect your Google account.'
    })


@app.route('/api/google/revoke', methods=['POST'])
def google_revoke():
    """Revoke Google Sheets authorization"""
    try:
        revoke_authorization()
        # Optionally clear OAuth credentials too
        # session.pop('google_oauth_client_id', None)
        # session.pop('google_oauth_client_secret', None)
        return jsonify({'success': True, 'message': 'Google Sheets authorization revoked'})
    except Exception as e:
        logger.error(f"Error revoking authorization: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/export-csv', methods=['POST'])
def export_csv():
    """Export HeyReach data as CSV"""
    try:
        import csv
        import io
        from flask import Response
        
        # Get client from session or global
        client = get_client_for_request()
        
        if not client:
            return jsonify({'error': 'HeyReach API key not set. Please enter your API key first.'}), 400
        
        data = request.get_json()
        sender_id = data.get('sender_id', 'all')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # If no dates provided, default to last 7 days
        if not start_date or not end_date:
            end_date_obj = datetime.now()
            start_date_obj = end_date_obj - timedelta(days=7)
            start_date = start_date_obj.strftime('%Y-%m-%d')
            end_date = end_date_obj.strftime('%Y-%m-%d')
        
        # Get performance data
        performance_data = client.get_sender_weekly_performance(
            sender_id=None if sender_id == 'all' else sender_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not performance_data or not performance_data.get('senders'):
            return jsonify({'error': 'No data available for the selected date range'}), 400
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            'Sender Name', 'Week Start', 'Connections Sent', 'Connections Accepted',
            'Acceptance Rate (%)', 'Messages Sent', 'Message Replies', 'Reply Rate (%)',
            'Open Conversations', 'Interested', 'Leads Not Enrolled'
        ])
        
        # Write data
        for sender_name, weeks_data in performance_data.get('senders', {}).items():
            for week_data in weeks_data:
                writer.writerow([
                    sender_name,
                    week_data.get('week_start', ''),
                    week_data.get('connections_sent', 0),
                    week_data.get('connections_accepted', 0),
                    week_data.get('acceptance_rate', 0),
                    week_data.get('messages_sent', 0),
                    week_data.get('message_replies', 0),
                    week_data.get('reply_rate', 0),
                    week_data.get('open_conversations', 0),
                    week_data.get('interested', 0),
                    week_data.get('leads_not_enrolled', 0)
                ])
        
        # Create response
        output.seek(0)
        filename = f'heyreach_data_{start_date}_to_{end_date}.csv'
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Type': 'text/csv; charset=utf-8'
            }
        )
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to export CSV: {str(e)}'}), 500


@app.route('/api/send-to-apps-script', methods=['POST'])
def send_to_apps_script():
    """Send data to Google Apps Script web app"""
    try:
        import requests
        
        data = request.get_json()
        apps_script_url = data.get('apps_script_url', '').strip()
        
        if not apps_script_url:
            return jsonify({'error': 'Apps Script web app URL is required'}), 400
        
        # Validate URL
        if not apps_script_url.startswith('https://script.google.com'):
            return jsonify({'error': 'Invalid Apps Script URL. Must start with https://script.google.com'}), 400
        
        # Get client from session or global
        client = get_client_for_request()
        
        if not client:
            return jsonify({'error': 'HeyReach API key not set. Please enter your API key first.'}), 400
        
        # Get query parameters for date range
        sender_id = data.get('sender_id', 'all')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # If no dates provided, default to last 7 days
        if not start_date or not end_date:
            end_date_obj = datetime.now()
            start_date_obj = end_date_obj - timedelta(days=7)
            start_date = start_date_obj.strftime('%Y-%m-%d')
            end_date = end_date_obj.strftime('%Y-%m-%d')
        
        # Get performance data
        performance_data = client.get_sender_weekly_performance(
            sender_id=None if sender_id == 'all' else sender_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not performance_data or not performance_data.get('senders'):
            return jsonify({'error': 'No data available for the selected date range'}), 400
        
        # Get sender_names mapping from session
        sender_names_raw = session.get('sender_names', {})
        client_groups_raw = session.get('client_groups', {})
        
        # CRITICAL: Flask session serializes to JSON, converting int keys to strings
        # Convert string keys back to integers for proper lookup
        sender_names = {}
        for key, value in sender_names_raw.items():
            try:
                key_int = int(key) if isinstance(key, str) else key
                sender_names[key_int] = value
            except (ValueError, TypeError):
                sender_names[key] = value
        
        # Process client_groups - convert sender_ids to integers
        client_groups = {}
        for client_name, client_data in client_groups_raw.items():
            if isinstance(client_data, dict):
                sender_ids_raw = client_data.get('sender_ids', [])
            elif isinstance(client_data, list):
                sender_ids_raw = client_data
            else:
                continue
            
            # Convert sender IDs to integers
            sender_ids = []
            for sid in sender_ids_raw:
                try:
                    sender_ids.append(int(sid) if isinstance(sid, str) else sid)
                except (ValueError, TypeError):
                    sender_ids.append(sid)
            
            client_groups[client_name] = {
                'sender_ids': sender_ids
            }
        
        # Format data for Apps Script with sender IDs and client groups
        formatted_data = {
            'date_range': {
                'start': start_date,
                'end': end_date
            },
            'senders': [],
            'sender_id_mapping': {},  # Map sender names to IDs for matching
            'client_groups': client_groups  # Include client groups for sheet matching
        }
        
        # Build reverse mapping: name -> ID (for Apps Script to look up by name)
        for sender_id, name in sender_names.items():
            formatted_data['sender_id_mapping'][name] = sender_id
        
        logger.info(f"Client groups being sent: {list(client_groups.keys())}")
        
        # Log the sender_names mapping for debugging
        logger.info(f"Sender names mapping has {len(sender_names)} entries")
        if len(sender_names) > 0:
            first_key = list(sender_names.keys())[0]
            logger.info(f"Sample sender_names entry: {first_key} (type: {type(first_key).__name__}) -> {sender_names[first_key]}")
        
        for sender_name, weeks_data in performance_data.get('senders', {}).items():
            # Find sender ID from mapping (reverse lookup: name -> ID)
            sender_id = None
            for mapped_name, mapped_id in formatted_data['sender_id_mapping'].items():
                if mapped_name.lower() == sender_name.lower() or sender_name.lower() in mapped_name.lower():
                    sender_id = mapped_id
                    break
            
            # If still not found, try to extract ID from "Sender XXXXX" format
            if sender_id is None and sender_name.startswith('Sender '):
                try:
                    sender_id = int(sender_name.replace('Sender ', ''))
                    # Also get the real name from sender_names if available
                    real_name = sender_names.get(sender_id)
                    if real_name:
                        sender_name = real_name
                        logger.info(f"Resolved 'Sender {sender_id}' to '{real_name}'")
                except ValueError:
                    pass
            
            sender_data = {
                'name': sender_name,
                'sender_id': sender_id,
                'weeks': weeks_data
            }
            formatted_data['senders'].append(sender_data)
        
        # Log the data being sent (first sender only for brevity)
        if formatted_data.get('senders') and len(formatted_data['senders']) > 0:
            first_sender = formatted_data['senders'][0]
            logger.info(f"Sending to Apps Script: {len(formatted_data['senders'])} senders")
            logger.info(f"First sender example: name='{first_sender.get('name')}', id={first_sender.get('sender_id')}, weeks={len(first_sender.get('weeks', []))}")
            if first_sender.get('weeks') and len(first_sender['weeks']) > 0:
                first_week = first_sender['weeks'][0]
                logger.info(f"First week example: week_start='{first_week.get('week_start')}', week_end='{first_week.get('week_end')}', keys={list(first_week.keys())}")
        
        # Send to Apps Script (increased timeout for large datasets)
        try:
            response = requests.post(
                apps_script_url,
                json=formatted_data,
                timeout=300  # 5 minutes for large datasets
            )
            response.raise_for_status()
            
            # Parse response to get detailed results
            response_data = None
            try:
                response_data = response.json()
                logger.info(f"Apps Script response: {response_data}")
            except:
                logger.info(f"Apps Script response (text): {response.text[:500]}")
            
            # Build detailed response message
            message = f'Data sent to Apps Script. {len(formatted_data["senders"])} senders.'
            details = {}
            
            if response_data and isinstance(response_data, dict):
                results = response_data.get('results', {})
                processed = results.get('processed', [])
                not_found = results.get('not_found', [])
                errors = results.get('errors', [])
                debug = results.get('debug', {})
                
                message = f'Processed {len(processed)} senders, {len(not_found)} not found.'
                
                if processed:
                    details['processed'] = [f"{p.get('sender')} → {p.get('sheet')} (row {p.get('row')}, {p.get('cells_updated')} cells)" for p in processed[:5]]
                if not_found:
                    details['not_found'] = [f"{n.get('sender')}: {n.get('reason')}" for n in not_found[:10]]
                if errors:
                    details['errors'] = [f"{e.get('sender')}: {e.get('error')}" for e in errors[:5]]
                if debug:
                    details['sheets_found'] = debug.get('sheets_available', [])
                    details['client_groups_received'] = debug.get('client_groups', [])
            
            return jsonify({
                'success': True,
                'message': message,
                'details': details,
                'response': response.text[:1000] if response.text else 'Success'
            })
        except requests.exceptions.RequestException as e:
            logger.error(f"Error sending to Apps Script: {e}")
            return jsonify({
                'error': f'Failed to send data to Apps Script: {str(e)}',
                'hint': 'Make sure your Apps Script web app is deployed and accessible.'
            }), 500
        
    except Exception as e:
        logger.error(f"Error sending to Apps Script: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to send data: {str(e)}'}), 500


@app.route('/api/populate-sheets', methods=['POST'])
def populate_sheets():
    """Populate Google Sheets with HeyReach data"""
    try:
        data = request.get_json()
        sheets_url = data.get('sheets_url')
        
        if not sheets_url:
            return jsonify({'error': 'Google Sheets URL is required'}), 400
        
        # Check if user has authorized Google Sheets access
        if not is_authorized():
            return jsonify({
                'error': 'Google Sheets not authorized',
                'requires_auth': True,
                'message': 'Please authorize Google Sheets access first'
            }), 401
        
        # Get client from session or global
        client = get_client_for_request()
        
        if not client:
            return jsonify({'error': 'HeyReach API key not set. Please enter your API key first.'}), 400
        
        # Get query parameters for date range
        sender_id = data.get('sender_id', 'all')
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        
        # If no dates provided, default to last 7 days
        if not start_date or not end_date:
            end_date_obj = datetime.now()
            start_date_obj = end_date_obj - timedelta(days=7)
            start_date = start_date_obj.strftime('%Y-%m-%d')
            end_date = end_date_obj.strftime('%Y-%m-%d')
        
        # Get performance data from HeyReach
        performance_data = client.get_sender_weekly_performance(
            sender_id=None if sender_id == 'all' else sender_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if not performance_data or not performance_data.get('senders'):
            return jsonify({
                'error': 'No HeyReach data available for the selected date range',
                'updated': 0
            }), 200
        
        # Get OAuth token from session
        oauth_token = session.get('google_oauth_token')
        
        # Initialize Sheets client with OAuth token
        try:
            sheets_client = SheetsClient(sheets_url, oauth_token=oauth_token)
        except Exception as e:
            logger.error(f"Error initializing Sheets client: {e}")
            return jsonify({'error': f'Failed to connect to Google Sheets: {str(e)}'}), 400
        
        # Get all worksheets
        worksheet_names = sheets_client.get_worksheet_names()
        
        if not worksheet_names:
            return jsonify({'error': 'No worksheets found in the Google Sheet'}), 400
        
        # Populate each worksheet
        all_results = {
            'updated': 0,
            'errors': [],
            'worksheets': {}
        }
        
        for worksheet_name in worksheet_names:
            try:
                logger.info(f"Populating worksheet: {worksheet_name}")
                results = sheets_client.populate_heyreach_data(
                    worksheet_name=worksheet_name,
                    heyreach_data=performance_data,
                    date_range=(start_date, end_date)
                )
                
                all_results['updated'] += results['updated']
                all_results['errors'].extend(results['errors'])
                all_results['worksheets'][worksheet_name] = {
                    'updated': results['updated'],
                    'errors': results['errors']
                }
            except Exception as e:
                error_msg = f"Error populating worksheet '{worksheet_name}': {str(e)}"
                logger.error(error_msg)
                all_results['errors'].append(error_msg)
                all_results['worksheets'][worksheet_name] = {
                    'updated': 0,
                    'errors': [error_msg]
                }
        
        return jsonify({
            'success': True,
            'message': f'Successfully updated {all_results["updated"]} cells across {len(worksheet_names)} worksheet(s)',
            'updated': all_results['updated'],
            'worksheets': all_results['worksheets'],
            'errors': all_results['errors']
        })
        
    except Exception as e:
        logger.error(f"Error populating sheets: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Failed to populate sheets: {str(e)}'}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint - shows initialization status"""
    try:
        # Check environment variables
        api_key_set = bool(os.environ.get('HEYREACH_API_KEY'))
        base_url_set = os.environ.get('HEYREACH_BASE_URL', 'Not set')
        
        health_status = {
            'status': 'healthy' if heyreach_client else 'unhealthy',
            'client_initialized': bool(heyreach_client),
            'api_key_set': api_key_set,
            'base_url': base_url_set,
            'config_source': 'environment' if api_key_set else 'config.yaml'
        }
        
        if heyreach_client:
            # Test connection by getting accounts
            try:
                accounts = heyreach_client.get_linkedin_accounts()
                health_status['connected'] = True
                health_status['accounts_found'] = len(accounts) if accounts else 0
                health_status['status'] = 'healthy'
            except Exception as e:
                health_status['connected'] = False
                health_status['error'] = str(e)
                health_status['status'] = 'error'
        else:
            health_status['error'] = 'HeyReach client not initialized'
            health_status['connected'] = False
        
        status_code = 200 if health_status['status'] == 'healthy' else 500
        return jsonify(health_status), status_code
    except Exception as e:
        logger.error(f"Health check error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({
            'status': 'error', 
            'message': str(e),
            'client_initialized': bool(heyreach_client),
            'api_key_set': bool(os.environ.get('HEYREACH_API_KEY'))
        }), 500


if __name__ == '__main__':
    # Initialize client
    if not init_client():
        logger.error("Failed to initialize HeyReach client. Check your config.yaml or environment variables")
        exit(1)
    
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    os.makedirs('static/css', exist_ok=True)
    os.makedirs('static/js', exist_ok=True)
    
    # Get port from environment variable (for production) or use default 5000
    port = int(os.environ.get('PORT', 5000))
    # Disable debug mode in production (when PORT is set by platform)
    debug_mode = os.environ.get('PORT') is None
    
    # Run app
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
