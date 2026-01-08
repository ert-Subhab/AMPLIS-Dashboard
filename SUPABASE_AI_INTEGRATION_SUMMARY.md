# Supabase & AI Integration Summary

## Overview

This integration allows users to:
1. Configure their own Supabase database (no backend storage)
2. Set up n8n webhooks to send HeyReach messages directly to Supabase
3. Use AI (ChatGPT, Claude, or Gemini) to evaluate message threads
4. Automatically merge Supabase stats (open conversations & interested) with HeyReach data
5. Send merged data to Google Sheets

## Key Features

### 1. Frontend-Only Configuration
- Users enter their own Supabase credentials
- No backend storage of credentials or data
- All Supabase operations happen client-side

### 2. Multiple AI Provider Support
- **OpenAI (ChatGPT)**: `gpt-4o-mini` model
- **Anthropic (Claude)**: `claude-3-5-sonnet-20241022` model
- **Google (Gemini)**: `gemini-pro` model
- Users can select their preferred AI provider
- API keys stored in browser localStorage only

### 3. n8n Setup Guide
- Complete guide in frontend (click "How to set up n8n → Supabase")
- Two options: Direct HTTP Request or Supabase Edge Function
- Step-by-step instructions with code examples

### 4. Automatic Stats Merging
- **Default**: `open_conversations` and `interested` are **0** in Google Sheets
- **When Supabase configured**: Stats are automatically merged from Supabase before sending to Google Sheets
- Matching by `sender_id` and `week_end` date

## How It Works

### Step 1: Set Up Supabase
1. Create Supabase table using `supabase_schema.sql`
2. Get Supabase URL and anon key from Settings → API
3. Enter credentials in dashboard

### Step 2: Set Up n8n Webhook
1. Configure n8n to receive HeyReach webhooks
2. Add HTTP Request node to send to Supabase
3. Map webhook data to Supabase schema
4. Webhooks flow: HeyReach → n8n → Supabase (no backend involved)

### Step 3: Configure AI
1. Select AI provider (ChatGPT, Claude, or Gemini)
2. Enter API key for selected provider
3. Click "Save Configuration"

### Step 4: Evaluate Messages
1. Click "Evaluate Messages"
2. System fetches unevaluated messages from Supabase
3. For each message:
   - Gets full conversation thread
   - Sends to selected AI provider
   - AI evaluates: `is_open_conversation` and `is_interested`
   - Updates Supabase with results

### Step 5: View Weekly Stats
1. Select date range
2. Click "Get Weekly Stats"
3. Shows open conversations and interested leads per week per client

### Step 6: Send to Google Sheets
1. Load HeyReach performance data
2. System automatically merges Supabase stats (if configured)
3. Send to Apps Script
4. Google Sheets gets:
   - HeyReach metrics (connections, messages, etc.)
   - Supabase AI metrics (open conversations, interested) - **only if Supabase is configured**

## Default Behavior

- **Without Supabase**: `open_conversations = 0`, `interested = 0` in Google Sheets
- **With Supabase**: Stats are merged from Supabase AI evaluation before sending to Google Sheets

## Files Created/Modified

### New Files:
- `supabase_schema.sql` - Database schema
- `supabase_client.py` - Backend client (optional, for future use)
- `static/js/supabase_integration.js` - Frontend Supabase functions
- `static/js/supabase_dashboard_functions.js` - UI functions
- `N8N_SUPABASE_SETUP_GUIDE.md` - Complete setup guide
- `SUPABASE_SETUP_GUIDE.md` - Original setup guide

### Modified Files:
- `templates/dashboard.html` - Added Supabase config UI and n8n help modal
- `static/js/dashboard.js` - Added Supabase integration and stats merging
- `heyreach_client.py` - Default `open_conversations` and `interested` to 0
- `app.py` - Accept merged performance data from frontend

## API Endpoints

### Frontend Functions (Client-Side):
- `initializeSupabase(url, key)` - Initialize Supabase client
- `getUnevaluatedMessages(limit)` - Get messages needing AI evaluation
- `evaluateConversationWithAI(thread, provider, apiKey)` - Evaluate with AI
- `getStatsByClient(startDate, endDate)` - Get weekly stats by client
- `mergeSupabaseStatsWithHeyReach(data, startDate, endDate, mapping)` - Merge stats

## Security Notes

1. **All credentials stored in browser localStorage** - never sent to backend
2. **Supabase anon key** - safe to use client-side (RLS policies protect data)
3. **AI API keys** - stored client-side only, sent directly to AI providers
4. **No backend webhook** - webhooks go directly to Supabase via n8n

## Troubleshooting

### "Supabase not initialized"
- Make sure you've entered Supabase URL and anon key
- Click "Save Configuration"
- Check browser console for errors

### "No unevaluated messages found"
- Check that webhooks are flowing to Supabase
- Verify messages are in `heyreach_messages` table
- Check that `ai_evaluated = false` for messages

### "Error merging Supabase stats"
- Verify Supabase is configured
- Check that messages have been evaluated (`ai_evaluated = true`)
- Ensure sender IDs match between HeyReach and Supabase

### Stats not appearing in Google Sheets
- Make sure Supabase is configured before sending to Apps Script
- Verify messages have been evaluated
- Check that sender IDs match correctly

