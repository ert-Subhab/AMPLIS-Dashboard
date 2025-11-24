# Setting Up Environment Variables on Render.com

This guide will help you add all the required environment variables to your Render.com deployment.

## Step-by-Step Instructions

1. **Go to your Render Dashboard**
   - Navigate to https://dashboard.render.com
   - Log in to your account

2. **Select Your Service**
   - Click on your service (e.g., "amplis-dashboard" or similar)

3. **Navigate to Environment**
   - In the left sidebar, click on **"Environment"**
   - Or click on **"Settings"** and then scroll to **"Environment Variables"**

4. **Add Each Environment Variable**
   - Click **"Add Environment Variable"** or **"Add New Variable"** button
   - Add each variable one at a time using the values from `env_vars.txt`

## Environment Variables to Add

### 1. HEYREACH_API_KEY
**Key:** `HEYREACH_API_KEY`  
**Value:** `IPaXhR9LEYf/H5NLCbdE8BScAz6VfEZ9t/AhFYGOeU0=`

### 2. HEYREACH_BASE_URL (Optional - has default)
**Key:** `HEYREACH_BASE_URL`  
**Value:** `https://api.heyreach.io`

### 3. HEYREACH_SENDER_IDS
**Key:** `HEYREACH_SENDER_IDS`  
**Value:** Copy the entire line from `env_vars.txt` (the JSON array of sender IDs)

Full value:
```
[50083, 50084, 50118, 50372, 50557, 51449, 51455, 55373, 56166, 56357, 56697, 57032, 57437, 57884, 58429, 58747, 60189, 61235, 61422, 62296, 62297, 62732, 62813, 63376, 64089, 64729, 64934, 64956, 65679, 66744, 67219, 68314, 68626, 70393, 70969, 72965, 73546, 74762, 77491, 81222, 82012, 82460, 84876, 85934, 91373, 92261, 93723, 94234, 95519, 95684, 95994, 97728, 98259, 98434, 98562, 98854, 100475, 100794, 103309, 104329, 105159, 108768, 108769, 108840, 109700, 111993, 115781, 116050, 116169, 121505]
```

### 4. HEYREACH_SENDER_NAMES
**Key:** `HEYREACH_SENDER_NAMES`  
**Value:** Copy the entire line from `env_vars.txt` (the JSON object mapping IDs to names)

**Note:** This is a long JSON string. Make sure to copy it completely from `env_vars.txt` file (line 4).

### 5. HEYREACH_CLIENT_GROUPS
**Key:** `HEYREACH_CLIENT_GROUPS`  
**Value:** Copy the entire line from `env_vars.txt` (the JSON object for client grouping)

**Note:** This is a long JSON string. Make sure to copy it completely from `env_vars.txt` file (line 5).

## Quick Copy Method

1. Open the `env_vars.txt` file in your project
2. For each variable:
   - Copy the KEY name (everything before the `=`)
   - Copy the VALUE (everything after the `=`)
   - Paste them into Render's environment variable form

## Important Notes

- **No quotes needed:** When pasting the JSON values, don't add extra quotes. Render will handle the string formatting.
- **Complete values:** Make sure to copy the entire JSON value, especially for `HEYREACH_SENDER_NAMES` and `HEYREACH_CLIENT_GROUPS` which are long.
- **After adding:** After adding all variables, Render will automatically redeploy your service.

## Verification

After adding all environment variables:

1. Go to your service's **"Logs"** tab
2. Look for initialization messages that should show:
   - `Loaded X sender IDs from environment`
   - `Loaded X sender names from environment`
   - `Loaded X client groups from environment`
3. Check the `/api/health` endpoint to verify the client initialized correctly

## Troubleshooting

If you see errors about missing sender IDs:
- Double-check that you copied the complete JSON value
- Verify there are no extra spaces or line breaks in the values
- Check that JSON syntax is valid (you can validate at jsonlint.com)

If the service doesn't redeploy automatically:
- Manually trigger a redeploy from the Render dashboard
- Or make a small change to trigger a new deployment

