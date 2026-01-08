-- Supabase Table Schema for HeyReach Message Replies
-- This table stores all message replies from HeyReach webhooks
-- and includes AI evaluation fields for "open_conversation" and "interested"

-- Create the main messages table
CREATE TABLE IF NOT EXISTS heyreach_messages (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Webhook metadata
    correlation_id TEXT UNIQUE NOT NULL,
    event_type TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    is_inmail BOOLEAN DEFAULT FALSE,
    
    -- Conversation tracking
    conversation_id TEXT NOT NULL,
    
    -- Campaign information (stored as JSONB for flexibility)
    campaign JSONB NOT NULL,
    
    -- Sender information (stored as JSONB, can be queried with JSON operators)
    sender JSONB NOT NULL,
    sender_id INTEGER GENERATED ALWAYS AS ((sender->>'id')::INTEGER) STORED,
    sender_email TEXT GENERATED ALWAYS AS (sender->>'email_address') STORED,
    sender_full_name TEXT GENERATED ALWAYS AS (sender->>'full_name') STORED,
    
    -- Lead information (stored as JSONB)
    lead JSONB NOT NULL,
    lead_id TEXT GENERATED ALWAYS AS (lead->>'id') STORED,
    lead_email TEXT GENERATED ALWAYS AS (lead->>'email_address') STORED,
    lead_full_name TEXT GENERATED ALWAYS AS (lead->>'full_name') STORED,
    lead_company_name TEXT GENERATED ALWAYS AS (lead->>'company_name') STORED,
    
    -- Recent messages (array of message objects)
    recent_messages JSONB NOT NULL DEFAULT '[]'::JSONB,
    
    -- AI Evaluation fields
    ai_evaluated BOOLEAN DEFAULT FALSE,
    ai_evaluation_timestamp TIMESTAMPTZ,
    is_open_conversation BOOLEAN,
    is_interested BOOLEAN,
    ai_confidence DECIMAL(3,2), -- 0.00 to 1.00
    ai_reasoning TEXT, -- AI's explanation for the classification
    ai_model_version TEXT, -- Track which AI model/version was used
    
    -- Full conversation thread (for AI evaluation)
    -- This will be populated by aggregating all messages for a conversation_id
    conversation_thread JSONB,
    
    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_heyreach_messages_conversation_id ON heyreach_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_heyreach_messages_sender_id ON heyreach_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_heyreach_messages_lead_id ON heyreach_messages(lead_id);
CREATE INDEX IF NOT EXISTS idx_heyreach_messages_timestamp ON heyreach_messages(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_heyreach_messages_ai_evaluated ON heyreach_messages(ai_evaluated) WHERE ai_evaluated = FALSE;
CREATE INDEX IF NOT EXISTS idx_heyreach_messages_open_conversation ON heyreach_messages(is_open_conversation) WHERE is_open_conversation = TRUE;
CREATE INDEX IF NOT EXISTS idx_heyreach_messages_interested ON heyreach_messages(is_interested) WHERE is_interested = TRUE;
CREATE INDEX IF NOT EXISTS idx_heyreach_messages_correlation_id ON heyreach_messages(correlation_id);

-- Create GIN index for JSONB queries (for searching within JSON fields)
CREATE INDEX IF NOT EXISTS idx_heyreach_messages_sender_gin ON heyreach_messages USING GIN(sender);
CREATE INDEX IF NOT EXISTS idx_heyreach_messages_lead_gin ON heyreach_messages USING GIN(lead);
CREATE INDEX IF NOT EXISTS idx_heyreach_messages_campaign_gin ON heyreach_messages USING GIN(campaign);
CREATE INDEX IF NOT EXISTS idx_heyreach_messages_recent_messages_gin ON heyreach_messages USING GIN(recent_messages);

-- Create a function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update updated_at
CREATE TRIGGER update_heyreach_messages_updated_at
    BEFORE UPDATE ON heyreach_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create a view for easy querying of open conversations
CREATE OR REPLACE VIEW open_conversations AS
SELECT 
    id,
    conversation_id,
    sender_id,
    sender_full_name,
    sender_email,
    lead_id,
    lead_full_name,
    lead_company_name,
    lead_email,
    campaign->>'name' as campaign_name,
    timestamp,
    ai_evaluation_timestamp,
    ai_confidence,
    ai_reasoning,
    conversation_thread
FROM heyreach_messages
WHERE is_open_conversation = TRUE
ORDER BY timestamp DESC;

-- Create a view for interested leads
CREATE OR REPLACE VIEW interested_leads AS
SELECT 
    id,
    conversation_id,
    sender_id,
    sender_full_name,
    sender_email,
    lead_id,
    lead_full_name,
    lead_company_name,
    lead_email,
    campaign->>'name' as campaign_name,
    timestamp,
    ai_evaluation_timestamp,
    ai_confidence,
    ai_reasoning,
    conversation_thread
FROM heyreach_messages
WHERE is_interested = TRUE
ORDER BY timestamp DESC;

-- Create a function to get full conversation thread for a conversation_id
CREATE OR REPLACE FUNCTION get_conversation_thread(p_conversation_id TEXT)
RETURNS JSONB AS $$
DECLARE
    v_thread JSONB;
BEGIN
    SELECT jsonb_agg(
        jsonb_build_object(
            'id', id,
            'timestamp', timestamp,
            'recent_messages', recent_messages,
            'sender', sender,
            'lead', lead,
            'campaign', campaign
        ) ORDER BY timestamp
    ) INTO v_thread
    FROM heyreach_messages
    WHERE conversation_id = p_conversation_id;
    
    RETURN COALESCE(v_thread, '[]'::JSONB);
END;
$$ LANGUAGE plpgsql;

-- Create a function to mark messages for AI re-evaluation
CREATE OR REPLACE FUNCTION mark_for_ai_evaluation(p_conversation_id TEXT DEFAULT NULL)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    IF p_conversation_id IS NOT NULL THEN
        -- Mark specific conversation for re-evaluation
        UPDATE heyreach_messages
        SET ai_evaluated = FALSE,
            ai_evaluation_timestamp = NULL,
            is_open_conversation = NULL,
            is_interested = NULL,
            ai_confidence = NULL,
            ai_reasoning = NULL
        WHERE conversation_id = p_conversation_id;
        
        GET DIAGNOSTICS v_count = ROW_COUNT;
    ELSE
        -- Mark all unevaluated messages
        UPDATE heyreach_messages
        SET ai_evaluated = FALSE
        WHERE ai_evaluated = FALSE OR ai_evaluated IS NULL;
        
        GET DIAGNOSTICS v_count = ROW_COUNT;
    END IF;
    
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE heyreach_messages IS 'Stores all message replies from HeyReach webhooks with AI evaluation for open conversations and interested leads';
COMMENT ON COLUMN heyreach_messages.conversation_thread IS 'Full conversation thread aggregated from all messages with the same conversation_id';
COMMENT ON COLUMN heyreach_messages.ai_evaluated IS 'Whether this message has been evaluated by AI';
COMMENT ON COLUMN heyreach_messages.is_open_conversation IS 'AI-determined: Is this an open/active conversation?';
COMMENT ON COLUMN heyreach_messages.is_interested IS 'AI-determined: Does this lead show interest?';
COMMENT ON COLUMN heyreach_messages.ai_confidence IS 'AI confidence score (0.00 to 1.00)';
COMMENT ON COLUMN heyreach_messages.ai_reasoning IS 'AI explanation for the classification';

