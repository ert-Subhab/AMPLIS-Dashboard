# OAuth 2.0 Setup for SaaS Platform

This guide explains how to set up Google OAuth 2.0 credentials **once** for your SaaS platform. After setup, all users can connect their own Google accounts without needing individual service accounts.

## Overview

With OAuth 2.0, each user authorizes your application to access their Google Sheets. This is the standard approach for SaaS platforms and requires **one-time setup** by the platform owner (you).

## One-Time Setup (Platform Owner)

### Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or use existing)
3. Name it something like "HeyReach Dashboard SaaS"

### Step 2: Configure OAuth Consent Screen

1. Go to **"APIs & Services"** > **"OAuth consent screen"**
2. Choose **"External"** (unless you have a Google Workspace)
3. Fill in required information:
   - **App name**: "HeyReach Performance Dashboard"
   - **User support email**: Your email
   - **Developer contact information**: Your email
4. Click **"Save and Continue"**
5. **Scopes**: Click "Add or Remove Scopes"
   - Add: `https://www.googleapis.com/auth/spreadsheets`
   - Click "Update" then "Save and Continue"
6. **Test users** (for testing): Add your email
7. Click **"Save and Continue"**
8. **Summary**: Review and click "Back to Dashboard"

### Step 3: Create OAuth 2.0 Credentials

1. Go to **"APIs & Services"** > **"Credentials"**
2. Click **"+ CREATE CREDENTIALS"** > **"OAuth client ID"**
3. Choose **"Web application"**
4. Fill in:
   - **Name**: "HeyReach Dashboard Web Client"
   - **Authorized JavaScript origins**:
     - `http://localhost:5000` (for local development)
     - `https://your-domain.com` (for production)
   - **Authorized redirect URIs**:
     - `http://localhost:5000/api/google/callback` (for local development)
     - `https://your-domain.com/api/google/callback` (for production)
5. Click **"Create"**
6. **Copy the Client ID and Client Secret** - you'll need these!

### Step 4: Set Environment Variables

Set these environment variables on your server (Render, Heroku, etc.):

```bash
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=https://your-domain.com/api/google/callback
```

**For Render:**
1. Go to your service settings
2. Add environment variables:
   - `GOOGLE_CLIENT_ID`
   - `GOOGLE_CLIENT_SECRET`
   - `GOOGLE_REDIRECT_URI`

**For local development:**
Create a `.env` file (don't commit it!):
```
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:5000/api/google/callback
```

## How It Works for Users

1. **User clicks "Connect Google Sheets"**
2. **Redirected to Google** to authorize access
3. **User grants permission** to your app
4. **Redirected back** to your app with authorization
5. **Token stored in session** (encrypted, user-specific)
6. **User can now populate their sheets**

## Security Notes

- **Tokens are stored in Flask session** (encrypted, per-user)
- **Each user's tokens are separate** - users can only access their own sheets
- **Tokens auto-refresh** when expired
- **Users can revoke access** anytime via "Disconnect" button

## Production Checklist

- [ ] OAuth consent screen published (or in testing mode with test users)
- [ ] Environment variables set on production server
- [ ] Redirect URI matches your production domain
- [ ] HTTPS enabled (required for OAuth in production)
- [ ] Test the flow end-to-end

## Troubleshooting

### "redirect_uri_mismatch" Error

**Solution**: Make sure the redirect URI in Google Cloud Console exactly matches:
- For local: `http://localhost:5000/api/google/callback`
- For production: `https://your-domain.com/api/google/callback`

### "access_denied" Error

**Solution**: User denied permission. They need to click "Allow" on the Google authorization page.

### Tokens Not Storing

**Solution**: 
- Check Flask session secret key is set
- Verify cookies are enabled
- Check that session is being saved

## Benefits of OAuth 2.0 for SaaS

✅ **No service accounts needed** - Users authorize with their own Google accounts  
✅ **Secure** - Each user's access is separate  
✅ **User-friendly** - Standard Google authorization flow  
✅ **Scalable** - Works for unlimited users  
✅ **Revocable** - Users can disconnect anytime  

## Next Steps

After setup:
1. Deploy your application with the environment variables
2. Users can now click "Connect Google Sheets"
3. They'll authorize with their Google account
4. They can populate their own sheets!

