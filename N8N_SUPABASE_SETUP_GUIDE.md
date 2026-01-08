# n8n to Supabase Webhook Setup Guide

This guide will help you configure n8n to automatically send HeyReach message webhooks directly to your Supabase database.

## Prerequisites

1. A Supabase account and project
2. The `heyreach_messages` table created (use `supabase_schema.sql`)
3. Your Supabase project URL and anon key
4. An n8n workflow that receives HeyReach webhooks

## Step 1: Get Your Supabase Credentials

1. Go to your Supabase Dashboard: https://app.supabase.com
2. Select your project
3. Go to **Settings** → **API**
4. Copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public key** (starts with `eyJ...`)

## Step 2: Create n8n Workflow

### Option A: Direct HTTP Request to Supabase REST API (Recommended)

1. **Add Webhook Node** (to receive from HeyReach)
   - Set webhook path (e.g., `/webhook/heyreach`)
   - Method: POST
   - Response: "Respond to Webhook"

2. **Add HTTP Request Node** (to send to Supabase)
   - Method: POST
   - URL: `https://YOUR-PROJECT.supabase.co/rest/v1/heyreach_messages`
   - Authentication: Header Auth
   - Header Name: `apikey`
   - Header Value: `YOUR-ANON-KEY`
   - Additional Header:
     - Name: `Authorization`
     - Value: `Bearer YOUR-ANON-KEY`
   - Additional Header:
     - Name: `Content-Type`
     - Value: `application/json`
   - Additional Header:
     - Name: `Prefer`
     - Value: `return=representation`
   - Body Content Type: JSON
   - Body: Map the webhook data to match Supabase schema

3. **Map the Data** (in HTTP Request body):
```json
{
  "correlation_id": "{{ $json.body.correlation_id }}",
  "event_type": "{{ $json.body.event_type }}",
  "timestamp": "{{ $json.body.timestamp }}",
  "is_inmail": {{ $json.body.is_inmail }},
  "conversation_id": "{{ $json.body.conversation_id }}",
  "campaign": {{ $json.body.campaign }},
  "sender": {{ $json.body.sender }},
  "lead": {{ $json.body.lead }},
  "recent_messages": {{ $json.body.recent_messages }}
}
```

### Option B: Using Supabase Edge Function (More Secure)

1. **Create Supabase Edge Function**:
   - Go to Supabase Dashboard → Edge Functions
   - Create new function: `heyreach-webhook`
   - Code:
```typescript
import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_ANON_KEY') ?? ''
    )

    const webhookData = await req.json()
    const body = webhookData.body || webhookData

    const messageData = {
      correlation_id: body.correlation_id,
      event_type: body.event_type || 'unknown',
      timestamp: body.timestamp,
      is_inmail: body.is_inmail || false,
      conversation_id: body.conversation_id,
      campaign: body.campaign || {},
      sender: body.sender || {},
      lead: body.lead || {},
      recent_messages: body.recent_messages || []
    }

    const { data, error } = await supabaseClient
      .from('heyreach_messages')
      .insert(messageData)
      .select()

    if (error) throw error

    return new Response(
      JSON.stringify({ success: true, data }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 200 },
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' }, status: 400 },
    )
  }
})
```

2. **Deploy the Function**:
   - Click "Deploy" in Supabase Dashboard
   - Note the function URL: `https://YOUR-PROJECT.supabase.co/functions/v1/heyreach-webhook`

3. **In n8n**:
   - Add HTTP Request Node
   - URL: `https://YOUR-PROJECT.supabase.co/functions/v1/heyreach-webhook`
   - Method: POST
   - Authentication: Header Auth
   - Header Name: `Authorization`
   - Header Value: `Bearer YOUR-ANON-KEY`
   - Body: Pass through the webhook data

## Step 3: Test the Workflow

1. **Activate your n8n workflow**
2. **Send a test webhook** from HeyReach
3. **Check Supabase**:
   - Go to Table Editor → `heyreach_messages`
   - You should see the new record

## Step 4: Handle Duplicates (Optional)

Add a check in n8n to prevent duplicate inserts:

1. **Add Function Node** before HTTP Request:
```javascript
// Check if correlation_id already exists
const correlationId = $input.item.json.body.correlation_id;
// You can query Supabase first, or rely on database unique constraint
return $input.item;
```

2. **Or use Supabase upsert** (update if exists, insert if not):
   - In HTTP Request, add header:
     - Name: `Prefer`
     - Value: `resolution=merge-duplicates`
   - Use PATCH method instead of POST

## Troubleshooting

### Error: "new row violates row-level security policy"
- **Solution**: Disable RLS for the table temporarily, or create a policy:
```sql
CREATE POLICY "Allow webhook inserts"
ON heyreach_messages
FOR INSERT
TO anon
WITH CHECK (true);
```

### Error: "duplicate key value violates unique constraint"
- **Solution**: The `correlation_id` already exists. This is normal - the webhook was already processed.

### Data not appearing in Supabase
- Check n8n execution logs
- Verify Supabase credentials are correct
- Check that table name matches exactly: `heyreach_messages`
- Verify JSON structure matches the schema

## Security Best Practices

1. **Use Supabase Edge Function** (Option B) for better security
2. **Set up RLS policies** to restrict access
3. **Use service_role key only in Edge Functions**, never expose it
4. **Monitor webhook logs** in n8n for suspicious activity

## Next Steps

After webhooks are flowing to Supabase:
1. Configure Supabase credentials in the dashboard
2. Set up AI evaluation (ChatGPT/Claude)
3. Evaluate messages to get open conversations and interested leads
4. View weekly stats by client

