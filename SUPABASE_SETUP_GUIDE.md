# Supabase Setup Guide for HeyReach Messages

This guide will help you set up the Supabase database table for storing HeyReach message replies and AI evaluation.

## Prerequisites

1. A Supabase account (sign up at https://supabase.com)
2. A Supabase project created
3. Access to the Supabase SQL Editor

## Step 1: Create the Table

1. **Log into Supabase Dashboard**
   - Go to https://app.supabase.com
   - Select your project

2. **Open SQL Editor**
   - Click on "SQL Editor" in the left sidebar
   - Click "New query"

3. **Run the Schema SQL**
   - Copy the contents of `supabase_schema.sql`
   - Paste into the SQL Editor
   - Click "Run" (or press Ctrl+Enter)

4. **Verify Table Creation**
   - Go to "Table Editor" in the left sidebar
   - You should see `heyreach_messages` table
   - Check that all columns are created correctly

## Step 2: Set Up Row Level Security (RLS)

For production, you should set up RLS policies. Here's a basic setup:

```sql
-- Enable RLS
ALTER TABLE heyreach_messages ENABLE ROW LEVEL SECURITY;

-- Policy: Allow service role to do everything (for backend API)
CREATE POLICY "Service role can do everything"
ON heyreach_messages
FOR ALL
TO service_role
USING (true)
WITH CHECK (true);

-- Policy: Allow authenticated users to read their own data
-- (Adjust based on your authentication setup)
CREATE POLICY "Users can read their own messages"
ON heyreach_messages
FOR SELECT
TO authenticated
USING (true); -- Adjust this based on your auth requirements
```

## Step 3: Set Up Webhook Endpoint

You'll need to create an API endpoint in your Flask app to receive webhooks from n8n and insert them into Supabase.

### Install Supabase Python Client

```bash
pip install supabase
```

### Create Webhook Endpoint

Create a new file `supabase_client.py`:

```python
from supabase import create_client, Client
import os
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SupabaseMessageStore:
    def __init__(self):
        supabase_url = os.environ.get('SUPABASE_URL')
        supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        
        self.client: Client = create_client(supabase_url, supabase_key)
    
    def insert_message(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Insert a message from HeyReach webhook into Supabase
        
        Args:
            webhook_data: The webhook payload from n8n
            
        Returns:
            Inserted record
        """
        body = webhook_data.get('body', {})
        
        # Extract data from webhook
        message_data = {
            'correlation_id': body.get('correlation_id'),
            'event_type': body.get('event_type'),
            'timestamp': body.get('timestamp'),
            'is_inmail': body.get('is_inmail', False),
            'conversation_id': body.get('conversation_id'),
            'campaign': body.get('campaign', {}),
            'sender': body.get('sender', {}),
            'lead': body.get('lead', {}),
            'recent_messages': body.get('recent_messages', [])
        }
        
        try:
            # Insert into Supabase
            result = self.client.table('heyreach_messages').insert(message_data).execute()
            
            if result.data:
                logger.info(f"Inserted message with correlation_id: {message_data['correlation_id']}")
                return result.data[0]
            else:
                logger.error(f"Failed to insert message: {result}")
                return None
                
        except Exception as e:
            logger.error(f"Error inserting message into Supabase: {e}")
            raise
    
    def get_conversation_thread(self, conversation_id: str) -> list:
        """
        Get full conversation thread for a conversation_id
        
        Args:
            conversation_id: The conversation ID to retrieve
            
        Returns:
            List of messages in the conversation
        """
        try:
            result = self.client.rpc('get_conversation_thread', {
                'p_conversation_id': conversation_id
            }).execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting conversation thread: {e}")
            return []
    
    def get_unevaluated_messages(self, limit: int = 100) -> list:
        """
        Get messages that haven't been evaluated by AI yet
        
        Args:
            limit: Maximum number of messages to return
            
        Returns:
            List of unevaluated messages
        """
        try:
            result = self.client.table('heyreach_messages')\
                .select('*')\
                .eq('ai_evaluated', False)\
                .order('timestamp', desc=False)\
                .limit(limit)\
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error getting unevaluated messages: {e}")
            return []
    
    def update_ai_evaluation(self, message_id: str, evaluation: Dict[str, Any]) -> bool:
        """
        Update AI evaluation results for a message
        
        Args:
            message_id: UUID of the message
            evaluation: Dict with ai_evaluated, is_open_conversation, is_interested, etc.
            
        Returns:
            True if successful
        """
        try:
            update_data = {
                'ai_evaluated': True,
                'ai_evaluation_timestamp': 'now()',
                **evaluation
            }
            
            result = self.client.table('heyreach_messages')\
                .update(update_data)\
                .eq('id', message_id)\
                .execute()
            
            return result.data is not None
        except Exception as e:
            logger.error(f"Error updating AI evaluation: {e}")
            return False
```

## Step 4: Add Webhook Route to Flask App

Add this to your `app.py`:

```python
from supabase_client import SupabaseMessageStore

# Initialize Supabase client
supabase_store = None
try:
    supabase_store = SupabaseMessageStore()
except Exception as e:
    logger.warning(f"Supabase not configured: {e}")

@app.route('/api/webhook/heyreach-message', methods=['POST'])
def heyreach_message_webhook():
    """Receive webhook from n8n for HeyReach messages"""
    try:
        webhook_data = request.get_json()
        
        if not webhook_data:
            return jsonify({'error': 'No data received'}), 400
        
        # Insert into Supabase
        if supabase_store:
            result = supabase_store.insert_message(webhook_data)
            
            if result:
                return jsonify({
                    'success': True,
                    'message_id': result.get('id'),
                    'correlation_id': result.get('correlation_id')
                }), 200
            else:
                return jsonify({'error': 'Failed to insert message'}), 500
        else:
            return jsonify({'error': 'Supabase not configured'}), 500
            
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({'error': str(e)}), 500
```

## Step 5: Environment Variables

Add these to your `.env` or Render environment variables:

```
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
```

To get these values:
1. Go to Supabase Dashboard → Settings → API
2. Copy "Project URL" → `SUPABASE_URL`
3. Copy "service_role" key → `SUPABASE_SERVICE_ROLE_KEY` (keep this secret!)

## Step 6: Test the Setup

1. **Test Webhook Endpoint**
   ```bash
   curl -X POST http://localhost:5000/api/webhook/heyreach-message \
     -H "Content-Type: application/json" \
     -d @test_webhook.json
   ```

2. **Verify in Supabase**
   - Go to Table Editor
   - Check `heyreach_messages` table
   - You should see the inserted record

## Step 7: Set Up AI Evaluation (Next Steps)

The AI evaluation will be a separate process that:
1. Fetches unevaluated messages from Supabase
2. Gets the full conversation thread
3. Uses AI (OpenAI, Anthropic, etc.) to evaluate the thread
4. Updates the message with evaluation results

This will be implemented in a separate script or background job.

## Useful Queries

### Get all open conversations
```sql
SELECT * FROM open_conversations;
```

### Get all interested leads
```sql
SELECT * FROM interested_leads;
```

### Get conversation thread
```sql
SELECT get_conversation_thread('your-conversation-id');
```

### Get unevaluated messages
```sql
SELECT * FROM heyreach_messages 
WHERE ai_evaluated = FALSE 
ORDER BY timestamp ASC 
LIMIT 100;
```

## Next Steps

1. ✅ Create the table (Step 1)
2. ✅ Set up webhook endpoint (Step 4)
3. ⏭️ Implement AI evaluation service
4. ⏭️ Create background job to process unevaluated messages
5. ⏭️ Integrate with existing dashboard

