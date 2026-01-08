/**
 * Supabase Integration for HeyReach Messages
 * Client-side integration for querying Supabase and AI evaluation
 */

// Supabase client instance (will be initialized when user provides credentials)
let supabaseClient = null;

/**
 * Initialize Supabase client with user-provided credentials
 */
function initializeSupabase(url, apiKey) {
    try {
        // Use Supabase JS client (CDN loaded)
        if (typeof supabase === 'undefined') {
            throw new Error('Supabase JS library not loaded. Add <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2"></script> to your HTML');
        }
        
        supabaseClient = supabase.createClient(url, apiKey);
        console.log('Supabase client initialized');
        return true;
    } catch (error) {
        console.error('Error initializing Supabase:', error);
        return false;
    }
}

/**
 * Get conversation thread for a conversation_id
 */
async function getConversationThread(conversationId) {
    if (!supabaseClient) {
        throw new Error('Supabase not initialized');
    }
    
    try {
        const { data, error } = await supabaseClient
            .from('heyreach_messages')
            .select('*')
            .eq('conversation_id', conversationId)
            .order('timestamp', { ascending: true });
        
        if (error) throw error;
        return data || [];
    } catch (error) {
        console.error('Error getting conversation thread:', error);
        throw error;
    }
}

/**
 * Get unevaluated messages
 */
async function getUnevaluatedMessages(limit = 100) {
    if (!supabaseClient) {
        throw new Error('Supabase not initialized');
    }
    
    try {
        const { data, error } = await supabaseClient
            .from('heyreach_messages')
            .select('*')
            .eq('ai_evaluated', false)
            .order('timestamp', { ascending: true })
            .limit(limit);
        
        if (error) throw error;
        return data || [];
    } catch (error) {
        console.error('Error getting unevaluated messages:', error);
        throw error;
    }
}

/**
 * Evaluate conversation thread using ChatGPT API
 */
async function evaluateConversationWithAI(conversationThread, openaiApiKey) {
    if (!conversationThread || conversationThread.length === 0) {
        throw new Error('Empty conversation thread');
    }
    
    // Build conversation text from thread
    let conversationText = '';
    for (const message of conversationThread) {
        const timestamp = new Date(message.timestamp).toLocaleString();
        const senderName = message.sender?.full_name || 'Unknown';
        const recentMessages = message.recent_messages || [];
        
        conversationText += `\n[${timestamp}] ${senderName}:\n`;
        for (const msg of recentMessages) {
            if (msg.message) {
                conversationText += `  - ${msg.message}\n`;
            }
            if (msg.message_type) {
                conversationText += `  - [${msg.message_type}]\n`;
            }
        }
    }
    
    // Prepare prompt for ChatGPT
    const prompt = `You are analyzing a LinkedIn outreach conversation thread. Evaluate the entire conversation and determine:

1. Is this an OPEN CONVERSATION? (The lead is actively engaging, asking questions, showing interest in continuing the dialogue)
2. Is the lead INTERESTED? (The lead shows genuine interest in the product/service, asks about pricing, scheduling, next steps, or expresses clear buying intent)

Conversation thread:
${conversationText}

Respond in JSON format:
{
  "is_open_conversation": true/false,
  "is_interested": true/false,
  "confidence": 0.0-1.0,
  "reasoning": "Brief explanation of your evaluation"
}`;

    try {
        const response = await fetch('https://api.openai.com/v1/chat/completions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${openaiApiKey}`
            },
            body: JSON.stringify({
                model: 'gpt-4o-mini', // Using cheaper model, can be changed to gpt-4 for better accuracy
                messages: [
                    {
                        role: 'system',
                        content: 'You are an expert at analyzing business conversations and determining engagement levels and buying intent.'
                    },
                    {
                        role: 'user',
                        content: prompt
                    }
                ],
                temperature: 0.3, // Lower temperature for more consistent results
                response_format: { type: 'json_object' }
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || 'OpenAI API error');
        }
        
        const data = await response.json();
        const content = JSON.parse(data.choices[0].message.content);
        
        return {
            is_open_conversation: content.is_open_conversation === true,
            is_interested: content.is_interested === true,
            ai_confidence: parseFloat(content.confidence) || 0.5,
            ai_reasoning: content.reasoning || 'No reasoning provided'
        };
    } catch (error) {
        console.error('Error evaluating with AI:', error);
        throw error;
    }
}

/**
 * Update AI evaluation in Supabase
 */
async function updateAIEvaluation(messageId, evaluation, conversationThread) {
    if (!supabaseClient) {
        throw new Error('Supabase not initialized');
    }
    
    try {
        const { data, error } = await supabaseClient
            .from('heyreach_messages')
            .update({
                ai_evaluated: true,
                ai_evaluation_timestamp: new Date().toISOString(),
                is_open_conversation: evaluation.is_open_conversation,
                is_interested: evaluation.is_interested,
                ai_confidence: evaluation.ai_confidence,
                ai_reasoning: evaluation.ai_reasoning,
                ai_model_version: 'gpt-4o-mini',
                conversation_thread: conversationThread
            })
            .eq('id', messageId)
            .select();
        
        if (error) throw error;
        return data;
    } catch (error) {
        console.error('Error updating AI evaluation:', error);
        throw error;
    }
}

/**
 * Process and evaluate a single message
 */
async function processMessageEvaluation(message, openaiApiKey) {
    try {
        // Get full conversation thread
        const thread = await getConversationThread(message.conversation_id);
        
        if (thread.length === 0) {
            throw new Error('No conversation thread found');
        }
        
        // Evaluate with AI
        const evaluation = await evaluateConversationWithAI(thread, openaiApiKey);
        
        // Update in Supabase
        await updateAIEvaluation(message.id, evaluation, thread);
        
        return {
            message_id: message.id,
            conversation_id: message.conversation_id,
            evaluation: evaluation
        };
    } catch (error) {
        console.error(`Error processing message ${message.id}:`, error);
        throw error;
    }
}

/**
 * Get weekly stats for open conversations and interested leads
 */
async function getWeeklyStats(startDate, endDate, senderId = null) {
    if (!supabaseClient) {
        throw new Error('Supabase not initialized');
    }
    
    try {
        let query = supabaseClient
            .from('heyreach_messages')
            .select('*')
            .gte('timestamp', startDate)
            .lte('timestamp', endDate)
            .eq('ai_evaluated', true);
        
        if (senderId) {
            query = query.eq('sender_id', senderId);
        }
        
        const { data, error } = await query;
        
        if (error) throw error;
        
        // Group by week and calculate stats
        const weeklyStats = {};
        
        for (const message of data || []) {
            const messageDate = new Date(message.timestamp);
            const weekEnd = getWeekEndDate(messageDate); // Friday of the week
            const weekKey = formatWeekKey(weekEnd);
            
            if (!weeklyStats[weekKey]) {
                weeklyStats[weekKey] = {
                    week_end: weekKey,
                    open_conversations: 0,
                    interested: 0,
                    total_messages: 0
                };
            }
            
            weeklyStats[weekKey].total_messages++;
            
            // Count unique conversations (not individual messages)
            if (message.is_open_conversation) {
                // We'll need to deduplicate by conversation_id
                if (!weeklyStats[weekKey]._open_conversations) {
                    weeklyStats[weekKey]._open_conversations = new Set();
                }
                weeklyStats[weekKey]._open_conversations.add(message.conversation_id);
            }
            
            if (message.is_interested) {
                if (!weeklyStats[weekKey]._interested) {
                    weeklyStats[weekKey]._interested = new Set();
                }
                weeklyStats[weekKey]._interested.add(message.conversation_id);
            }
        }
        
        // Convert sets to counts
        const result = Object.values(weeklyStats).map(stat => ({
            week_end: stat.week_end,
            open_conversations: stat._open_conversations ? stat._open_conversations.size : 0,
            interested: stat._interested ? stat._interested.size : 0,
            total_messages: stat.total_messages
        }));
        
        return result.sort((a, b) => {
            const [aMonth, aDay] = a.week_end.split('/').map(Number);
            const [bMonth, bDay] = b.week_end.split('/').map(Number);
            if (aMonth !== bMonth) return aMonth - bMonth;
            return aDay - bDay;
        });
    } catch (error) {
        console.error('Error getting weekly stats:', error);
        throw error;
    }
}

/**
 * Get week end date (Friday) for a given date
 */
function getWeekEndDate(date) {
    const d = new Date(date);
    const day = d.getDay();
    const diff = d.getDate() - day + (day === 0 ? -6 : 5); // Adjust to Friday
    return new Date(d.setDate(diff));
}

/**
 * Format date as M/D for week key
 */
function formatWeekKey(date) {
    const d = new Date(date);
    return `${d.getMonth() + 1}/${d.getDate()}`;
}

/**
 * Get stats by client (from campaign data)
 */
async function getStatsByClient(startDate, endDate) {
    if (!supabaseClient) {
        throw new Error('Supabase not initialized');
    }
    
    try {
        const { data, error } = await supabaseClient
            .from('heyreach_messages')
            .select('*')
            .gte('timestamp', startDate)
            .lte('timestamp', endDate)
            .eq('ai_evaluated', true);
        
        if (error) throw error;
        
        // Group by client (campaign name or lead company)
        const clientStats = {};
        
        for (const message of data || []) {
            const clientName = message.campaign?.name || message.lead?.company_name || 'Unknown';
            const weekEnd = getWeekEndDate(new Date(message.timestamp));
            const weekKey = formatWeekKey(weekEnd);
            
            if (!clientStats[clientName]) {
                clientStats[clientName] = {};
            }
            
            if (!clientStats[clientName][weekKey]) {
                clientStats[clientName][weekKey] = {
                    open_conversations: new Set(),
                    interested: new Set()
                };
            }
            
            if (message.is_open_conversation) {
                clientStats[clientName][weekKey].open_conversations.add(message.conversation_id);
            }
            
            if (message.is_interested) {
                clientStats[clientName][weekKey].interested.add(message.conversation_id);
            }
        }
        
        // Convert to final format
        const result = {};
        for (const [clientName, weeks] of Object.entries(clientStats)) {
            result[clientName] = Object.entries(weeks).map(([weekKey, stats]) => ({
                week_end: weekKey,
                open_conversations: stats.open_conversations.size,
                interested: stats.interested.size
            })).sort((a, b) => {
                const [aMonth, aDay] = a.week_end.split('/').map(Number);
                const [bMonth, bDay] = b.week_end.split('/').map(Number);
                if (aMonth !== bMonth) return aMonth - bMonth;
                return aDay - bDay;
            });
        }
        
        return result;
    } catch (error) {
        console.error('Error getting stats by client:', error);
        throw error;
    }
}

