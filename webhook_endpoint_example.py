"""
Example webhook endpoint for HeyReach messages
Add this to your app.py file
"""

from supabase_client import SupabaseMessageStore
from flask import jsonify, request
import logging

logger = logging.getLogger(__name__)

# Initialize Supabase client (add this near the top of app.py with other initializations)
supabase_store = None
try:
    supabase_store = SupabaseMessageStore()
    if supabase_store.is_configured():
        logger.info("Supabase message store initialized")
    else:
        logger.warning("Supabase not configured - webhook endpoint will not work")
except Exception as e:
    logger.warning(f"Supabase initialization failed: {e}")

@app.route('/api/webhook/heyreach-message', methods=['POST'])
def heyreach_message_webhook():
    """
    Receive webhook from n8n for HeyReach messages
    
    Expected payload structure:
    {
        "body": {
            "correlation_id": "...",
            "event_type": "every_message_reply_received",
            "timestamp": "2026-01-08T02:54:08.3464786Z",
            "conversation_id": "...",
            "campaign": {...},
            "sender": {...},
            "lead": {...},
            "recent_messages": [...]
        }
    }
    """
    try:
        webhook_data = request.get_json()
        
        if not webhook_data:
            logger.error("No data received in webhook")
            return jsonify({'error': 'No data received'}), 400
        
        # Validate required fields
        body = webhook_data.get('body', {})
        if not body.get('correlation_id'):
            logger.error("Missing correlation_id in webhook data")
            return jsonify({'error': 'Missing correlation_id'}), 400
        
        if not body.get('conversation_id'):
            logger.error("Missing conversation_id in webhook data")
            return jsonify({'error': 'Missing conversation_id'}), 400
        
        # Insert into Supabase
        if not supabase_store or not supabase_store.is_configured():
            logger.error("Supabase not configured")
            return jsonify({'error': 'Supabase not configured'}), 500
        
        result = supabase_store.insert_message(webhook_data)
        
        if result:
            logger.info(f"Successfully stored message: {result.get('id')}")
            return jsonify({
                'success': True,
                'message_id': result.get('id'),
                'correlation_id': result.get('correlation_id'),
                'conversation_id': result.get('conversation_id')
            }), 200
        else:
            logger.error("Failed to insert message into Supabase")
            return jsonify({'error': 'Failed to insert message'}), 500
            
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/unevaluated', methods=['GET'])
def get_unevaluated_messages():
    """Get messages that need AI evaluation"""
    try:
        if not supabase_store or not supabase_store.is_configured():
            return jsonify({'error': 'Supabase not configured'}), 500
        
        limit = request.args.get('limit', 100, type=int)
        messages = supabase_store.get_unevaluated_messages(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(messages),
            'messages': messages
        }), 200
    except Exception as e:
        logger.error(f"Error getting unevaluated messages: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/conversation/<conversation_id>', methods=['GET'])
def get_conversation(conversation_id):
    """Get full conversation thread"""
    try:
        if not supabase_store or not supabase_store.is_configured():
            return jsonify({'error': 'Supabase not configured'}), 500
        
        thread = supabase_store.get_conversation_thread(conversation_id)
        
        return jsonify({
            'success': True,
            'conversation_id': conversation_id,
            'message_count': len(thread),
            'thread': thread
        }), 200
    except Exception as e:
        logger.error(f"Error getting conversation thread: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/open-conversations', methods=['GET'])
def get_open_conversations():
    """Get all open conversations"""
    try:
        if not supabase_store or not supabase_store.is_configured():
            return jsonify({'error': 'Supabase not configured'}), 500
        
        limit = request.args.get('limit', 100, type=int)
        conversations = supabase_store.get_open_conversations(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(conversations),
            'conversations': conversations
        }), 200
    except Exception as e:
        logger.error(f"Error getting open conversations: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

@app.route('/api/messages/interested', methods=['GET'])
def get_interested_leads():
    """Get all interested leads"""
    try:
        if not supabase_store or not supabase_store.is_configured():
            return jsonify({'error': 'Supabase not configured'}), 500
        
        limit = request.args.get('limit', 100, type=int)
        leads = supabase_store.get_interested_leads(limit=limit)
        
        return jsonify({
            'success': True,
            'count': len(leads),
            'leads': leads
        }), 200
    except Exception as e:
        logger.error(f"Error getting interested leads: {e}", exc_info=True)
        return jsonify({'error': str(e)}), 500

