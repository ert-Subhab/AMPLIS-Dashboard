#!/usr/bin/env python3
"""
HeyReach Performance Dashboard
Flask web application for HeyReach performance tracking
"""

import yaml
import os
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import logging
from heyreach_client import HeyReachClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global client instance
heyreach_client = None

# Initialize client when app starts (for production deployment with gunicorn)
def initialize_app():
    """Initialize the HeyReach client when the app starts"""
    global heyreach_client
    try:
        logger.info("=" * 50)
        logger.info("Initializing HeyReach client on app startup...")
        logger.info(f"HEYREACH_API_KEY present: {bool(os.environ.get('HEYREACH_API_KEY'))}")
        logger.info(f"HEYREACH_BASE_URL: {os.environ.get('HEYREACH_BASE_URL', 'Not set')}")
        
        if not heyreach_client:
            if not init_client():
                logger.error("=" * 50)
                logger.error("CRITICAL: Failed to initialize HeyReach client on app startup")
                logger.error("The dashboard will not function without a valid client.")
                logger.error("Check environment variables: HEYREACH_API_KEY and HEYREACH_BASE_URL")
                logger.error("=" * 50)
            else:
                logger.info("=" * 50)
                logger.info("✅ HeyReach client initialized successfully on app startup")
                logger.info("=" * 50)
        else:
            logger.info("HeyReach client already initialized")
    except Exception as e:
        logger.error(f"Exception during app initialization: {e}")
        import traceback
        logger.error(traceback.format_exc())

# Initialize client when app is imported (for gunicorn)
initialize_app()


def load_config():
    """Load configuration from environment variables (production) or config.yaml (local)"""
    config = {}
    
    # Try environment variables first (for production deployment)
    api_key = os.environ.get('HEYREACH_API_KEY')
    if api_key:
        logger.info("Loading configuration from environment variables (production mode)")
        base_url = os.environ.get('HEYREACH_BASE_URL', 'https://api.heyreach.io')
        
        # Build config from environment variables
        config['heyreach'] = {
            'api_key': api_key,
            'base_url': base_url,
            'sender_ids': [],
            'sender_names': {},
            'client_groups': {}
        }
        
        # Try to load sender_ids from environment variable (JSON format)
        sender_ids_str = os.environ.get('HEYREACH_SENDER_IDS', '[]')
        if sender_ids_str:
            try:
                import json
                sender_ids = json.loads(sender_ids_str)
                if isinstance(sender_ids, list):
                    config['heyreach']['sender_ids'] = sender_ids
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to parse HEYREACH_SENDER_IDS from environment")
        
        # Try to load sender_names from environment variable (JSON format)
        sender_names_str = os.environ.get('HEYREACH_SENDER_NAMES', '{}')
        if sender_names_str:
            try:
                import json
                sender_names = json.loads(sender_names_str)
                if isinstance(sender_names, dict):
                    # Convert string keys to integers
                    processed_sender_names = {}
                    for key, value in sender_names.items():
                        try:
                            key_int = int(key) if isinstance(key, str) else key
                            processed_sender_names[key_int] = value
                        except (ValueError, TypeError):
                            processed_sender_names[key] = value
                    config['heyreach']['sender_names'] = processed_sender_names
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to parse HEYREACH_SENDER_NAMES from environment")
        
        # Try to load client_groups from environment variable (JSON format)
        client_groups_str = os.environ.get('HEYREACH_CLIENT_GROUPS', '{}')
        if client_groups_str:
            try:
                import json
                client_groups = json.loads(client_groups_str)
                if isinstance(client_groups, dict):
                    config['heyreach']['client_groups'] = client_groups
            except (json.JSONDecodeError, TypeError):
                logger.warning("Failed to parse HEYREACH_CLIENT_GROUPS from environment")
        
        return config
    
    # Fallback to config.yaml (for local development)
    try:
        logger.info("Loading configuration from config.yaml (local development mode)")
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        return config
    except FileNotFoundError:
        logger.error("config.yaml not found and no environment variables set!")
        return None
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return None


def init_client():
    """Initialize HeyReach client"""
    global heyreach_client
    config = load_config()
    if not config:
        return False
    
    heyreach_config = config.get('heyreach', {})
    api_key = heyreach_config.get('api_key')
    base_url = heyreach_config.get('base_url', 'https://api.heyreach.io')
    
    # Get manually configured sender IDs if available
    sender_ids = heyreach_config.get('sender_ids', [])
    sender_names = heyreach_config.get('sender_names', {})
    client_groups = heyreach_config.get('client_groups', {})
    
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
        logger.error("HeyReach API key not found in config.yaml or environment variables")
        logger.error("Please set HEYREACH_API_KEY environment variable")
        return False
    
    try:
        heyreach_client = HeyReachClient(
            api_key=api_key, 
            base_url=base_url,
            sender_ids=sender_ids,
            sender_names=sender_names,
            client_groups=client_groups
        )
        logger.info("✅ HeyReach client initialized successfully")
        if sender_ids:
            logger.info(f"📋 Using {len(sender_ids)} manually configured sender IDs")
        if client_groups:
            logger.info(f"📦 Loaded {len(client_groups)} client groups")
        return True
    except Exception as e:
        logger.error(f"Error initializing HeyReach client: {e}")
        import traceback
        traceback.print_exc()
        return False


@app.route('/')
def index():
    """Render dashboard homepage"""
    return render_template('dashboard.html')


@app.route('/api/senders', methods=['GET'])
def get_senders():
    """Get list of all senders (LinkedIn accounts)"""
    try:
        if not heyreach_client:
            error_msg = 'HeyReach client not initialized. Check environment variables and logs.'
            logger.error(error_msg)
            return jsonify({'error': error_msg, 'senders': [{'id': 'all', 'name': 'All'}]}), 200
        
        accounts = heyreach_client.get_linkedin_accounts()
        if not accounts:
            logger.warning("No LinkedIn accounts returned from API")
            # Return at least "All" option
            return jsonify({'senders': [{'id': 'all', 'name': 'All'}], 'warning': 'No senders found'}), 200
        
        senders = [
            {
                'id': acc.get('id'),
                'name': acc.get('linkedInUserListName', 'Unknown')
            }
            for acc in accounts if acc.get('id')
        ]
        
        # Add "All" option
        senders.insert(0, {'id': 'all', 'name': 'All'})
        
        logger.info(f"Returning {len(senders)} senders")
        return jsonify({'senders': senders})
    except Exception as e:
        logger.error(f"Error fetching senders: {e}")
        import traceback
        logger.error(traceback.format_exc())
        # Return at least "All" option even on error
        return jsonify({'error': str(e), 'senders': [{'id': 'all', 'name': 'All'}]}), 200


@app.route('/api/performance', methods=['GET'])
def get_performance():
    """Get performance data for selected sender and date range"""
    try:
        if not heyreach_client:
            return jsonify({'error': 'HeyReach client not initialized'}), 500
        
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
            performance_data = heyreach_client.get_sender_weekly_performance(
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
        if not heyreach_client:
            return jsonify({'error': 'HeyReach client not initialized'}), 500
        
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
        performance_data = heyreach_client.get_sender_weekly_performance(
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


@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        if not heyreach_client:
            return jsonify({'status': 'error', 'message': 'Client not initialized'}), 500
        
        # Test connection by getting accounts
        accounts = heyreach_client.get_linkedin_accounts()
        is_connected = len(accounts) >= 0  # If we get a response (even empty), we're connected
        
        return jsonify({
            'status': 'healthy' if is_connected else 'unhealthy',
            'connected': is_connected,
            'accounts_found': len(accounts)
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


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
