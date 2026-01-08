"""
Supabase Client for HeyReach Messages Storage
Handles storing message replies and AI evaluation
"""

from supabase import create_client, Client
import os
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class SupabaseMessageStore:
    """Client for storing and retrieving HeyReach messages from Supabase"""
    
    def __init__(self):
        """
        Initialize Supabase client
        
        Requires environment variables:
        - SUPABASE_URL: Your Supabase project URL
        - SUPABASE_SERVICE_ROLE_KEY: Your Supabase service role key (keep secret!)
        """
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.warning("Supabase credentials not found. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY environment variables.")
            self.client = None
            return
        
        try:
            self.client: Client = create_client(supabase_url, supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Supabase client: {e}")
            self.client = None
    
    def is_configured(self) -> bool:
        """Check if Supabase is properly configured"""
        return self.client is not None
    
    def insert_message(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Insert a message from HeyReach webhook into Supabase
        
        Args:
            webhook_data: The webhook payload from n8n (full request object)
            
        Returns:
            Inserted record or None if failed
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return None
        
        try:
            body = webhook_data.get('body', {})
            
            # Extract and validate required fields
            correlation_id = body.get('correlation_id')
            if not correlation_id:
                logger.error("Missing correlation_id in webhook data")
                return None
            
            # Check if message already exists (idempotency)
            existing = self.client.table('heyreach_messages')\
                .select('id')\
                .eq('correlation_id', correlation_id)\
                .execute()
            
            if existing.data:
                logger.info(f"Message with correlation_id {correlation_id} already exists, skipping insert")
                return existing.data[0]
            
            # Prepare message data
            message_data = {
                'correlation_id': correlation_id,
                'event_type': body.get('event_type', 'unknown'),
                'timestamp': body.get('timestamp'),
                'is_inmail': body.get('is_inmail', False),
                'conversation_id': body.get('conversation_id'),
                'campaign': body.get('campaign', {}),
                'sender': body.get('sender', {}),
                'lead': body.get('lead', {}),
                'recent_messages': body.get('recent_messages', [])
            }
            
            # Insert into Supabase
            result = self.client.table('heyreach_messages').insert(message_data).execute()
            
            if result.data and len(result.data) > 0:
                logger.info(f"Inserted message with correlation_id: {correlation_id}")
                return result.data[0]
            else:
                logger.error(f"Failed to insert message: No data returned")
                return None
                
        except Exception as e:
            logger.error(f"Error inserting message into Supabase: {e}", exc_info=True)
            return None
    
    def get_conversation_thread(self, conversation_id: str) -> List[Dict[str, Any]]:
        """
        Get full conversation thread for a conversation_id
        
        Args:
            conversation_id: The conversation ID to retrieve
            
        Returns:
            List of messages in the conversation, ordered by timestamp
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return []
        
        try:
            # Get all messages for this conversation
            result = self.client.table('heyreach_messages')\
                .select('*')\
                .eq('conversation_id', conversation_id)\
                .order('timestamp', desc=False)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting conversation thread: {e}", exc_info=True)
            return []
    
    def get_unevaluated_messages(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get messages that haven't been evaluated by AI yet
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of unevaluated messages
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return []
        
        try:
            result = self.client.table('heyreach_messages')\
                .select('*')\
                .eq('ai_evaluated', False)\
                .order('timestamp', desc=False)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting unevaluated messages: {e}", exc_info=True)
            return []
    
    def update_ai_evaluation(
        self, 
        message_id: str, 
        is_open_conversation: Optional[bool] = None,
        is_interested: Optional[bool] = None,
        ai_confidence: Optional[float] = None,
        ai_reasoning: Optional[str] = None,
        ai_model_version: Optional[str] = None,
        conversation_thread: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """
        Update AI evaluation results for a message
        
        Args:
            message_id: UUID of the message
            is_open_conversation: Whether this is an open conversation
            is_interested: Whether the lead shows interest
            ai_confidence: Confidence score (0.0 to 1.0)
            ai_reasoning: AI's explanation for the classification
            ai_model_version: Version of AI model used
            conversation_thread: Full conversation thread for context
            
        Returns:
            True if successful
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return False
        
        try:
            update_data = {
                'ai_evaluated': True,
                'ai_evaluation_timestamp': datetime.utcnow().isoformat() + 'Z'
            }
            
            if is_open_conversation is not None:
                update_data['is_open_conversation'] = is_open_conversation
            if is_interested is not None:
                update_data['is_interested'] = is_interested
            if ai_confidence is not None:
                update_data['ai_confidence'] = ai_confidence
            if ai_reasoning is not None:
                update_data['ai_reasoning'] = ai_reasoning
            if ai_model_version is not None:
                update_data['ai_model_version'] = ai_model_version
            if conversation_thread is not None:
                update_data['conversation_thread'] = conversation_thread
            
            result = self.client.table('heyreach_messages')\
                .update(update_data)\
                .eq('id', message_id)\
                .execute()
            
            if result.data:
                logger.info(f"Updated AI evaluation for message {message_id}")
                return True
            else:
                logger.warning(f"No data returned when updating message {message_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating AI evaluation: {e}", exc_info=True)
            return False
    
    def get_open_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all open conversations
        
        Args:
            limit: Maximum number of conversations to return
            
        Returns:
            List of open conversations
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return []
        
        try:
            result = self.client.table('heyreach_messages')\
                .select('*')\
                .eq('is_open_conversation', True)\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting open conversations: {e}", exc_info=True)
            return []
    
    def get_interested_leads(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all interested leads
        
        Args:
            limit: Maximum number of leads to return
            
        Returns:
            List of interested leads
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return []
        
        try:
            result = self.client.table('heyreach_messages')\
                .select('*')\
                .eq('is_interested', True)\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting interested leads: {e}", exc_info=True)
            return []
    
    def get_messages_by_sender(self, sender_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Get all messages for a specific sender
        
        Args:
            sender_id: The sender ID
            limit: Maximum number of messages to return
            
        Returns:
            List of messages for the sender
        """
        if not self.client:
            logger.error("Supabase client not initialized")
            return []
        
        try:
            result = self.client.table('heyreach_messages')\
                .select('*')\
                .eq('sender_id', sender_id)\
                .order('timestamp', desc=True)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting messages by sender: {e}", exc_info=True)
            return []

