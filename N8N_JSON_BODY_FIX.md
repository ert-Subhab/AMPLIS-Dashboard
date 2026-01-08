# Fix for n8n JSON Body Error

## The Problem

You're getting "JSON parameter needs to be valid JSON" because:
1. **Line breaks inside expressions**: `{{ $json.body.corr elation_id }}` (should be `correlation_id` on one line)
2. **Extra opening brace**: There's a `{` before the last field
3. **Nested objects need stringification**: Objects like `campaign`, `sender`, `lead` need `JSON.stringify()`

## The Solution

In your n8n HTTP Request node:

1. **Set Body Content Type**: `JSON`
2. **Set Specify Body**: `Using JSON`
3. **Paste this EXACT JSON** in the JSON text area:

```json
{
  "correlation_id": "{{ $json.body.correlation_id }}",
  "event_type": "{{ $json.body.event_type }}",
  "timestamp": "{{ $json.body.timestamp }}",
  "is_inmail": {{ $json.body.is_inmail }},
  "conversation_id": "{{ $json.body.conversation_id }}",
  "campaign": {{ JSON.stringify($json.body.campaign) }},
  "sender": {{ JSON.stringify($json.body.sender) }},
  "lead": {{ JSON.stringify($json.body.lead) }},
  "recent_messages": {{ JSON.stringify($json.body.recent_messages) }}
}
```

## Key Points

1. **No line breaks inside `{{ }}`** - The entire expression must be on one line
2. **Use `JSON.stringify()`** for nested objects - This converts JavaScript objects to JSON strings
3. **No extra braces** - Only one opening `{` and one closing `}`
4. **Boolean values** - `is_inmail` doesn't need quotes (it's a boolean, not a string)

## Alternative: Using "Using Fields Below" Method

If the JSON method is giving you trouble, you can use the "Using Fields Below" method:

1. **Set Specify Body**: `Using Fields Below`
2. **Add these fields one by one**:
   - `correlation_id`: `{{ $json.body.correlation_id }}`
   - `event_type`: `{{ $json.body.event_type }}`
   - `timestamp`: `{{ $json.body.timestamp }}`
   - `is_inmail`: `{{ $json.body.is_inmail }}`
   - `conversation_id`: `{{ $json.body.conversation_id }}`
   - `campaign`: `{{ JSON.stringify($json.body.campaign) }}`
   - `sender`: `{{ JSON.stringify($json.body.sender) }}`
   - `lead`: `{{ JSON.stringify($json.body.lead) }}`
   - `recent_messages`: `{{ JSON.stringify($json.body.recent_messages) }}`

This method is more forgiving and n8n will handle the JSON conversion automatically.

## Testing

After fixing the JSON:
1. Click "Execute step" (▲ button)
2. Check the OUTPUT panel - you should see a successful response
3. Verify in Supabase that the data was inserted

