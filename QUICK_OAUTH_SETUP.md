# Quick OAuth Setup for Google Sheets

## The Issue

When you click "Connect Google Sheets", you see an error because OAuth credentials aren't configured yet. This is a **one-time setup** that you (the platform owner) need to do.

## Why OAuth Credentials?

OAuth credentials are like a "key" that allows your application to initiate the Google authorization flow. Once set up:
- **You set it up once** (as platform owner)
- **Each user authorizes with their own Google account**
- **Users can access their own sheets**

Think of it like this:
- **OAuth Credentials** = Your app's ID card (set up once)
- **User Authorization** = Each user's permission (done per user)

## Quick Setup (5 minutes)

### Step 1: Create OAuth Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select existing)
3. Go to **"APIs & Services"** > **"OAuth consent screen"**
   - Choose "External"
   - Fill in app name: "HeyReach Dashboard"
   - Add your email
   - Add scope: `https://www.googleapis.com/auth/spreadsheets`
   - Save
4. Go to **"APIs & Services"** > **"Credentials"**
5. Click **"+ CREATE CREDENTIALS"** > **"OAuth client ID"**
6. Choose **"Web application"**
7. Add **Authorized redirect URI**:
   - `https://amplis-dashboard.onrender.com/api/google/callback`
8. Click **"Create"**
9. **Copy the Client ID and Client Secret**

### Step 2: Set Environment Variables on Render

1. Go to your Render dashboard
2. Select your service
3. Go to **"Environment"** tab
4. Add these variables:

```
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=https://amplis-dashboard.onrender.com/api/google/callback
```

5. Click **"Save Changes"**
6. Render will automatically redeploy

### Step 3: Test

1. Wait for deployment to complete
2. Refresh your dashboard
3. Click "Connect Google Sheets"
4. You should be redirected to Google to authorize

## That's It!

After this one-time setup, all users can:
- Click "Connect Google Sheets"
- Authorize with their Google account
- Populate their own sheets

## Important Notes

- **OAuth credentials are for your app** (not per-user)
- **Each user still uses their own Google account**
- **Users can only access their own sheets**
- **One-time setup** - you don't need to do this for each user

## Troubleshooting

### "redirect_uri_mismatch"
- Make sure the redirect URI in Google Cloud Console **exactly matches**:
  - `https://amplis-dashboard.onrender.com/api/google/callback`

### Still not working?
- Check environment variables are set correctly
- Make sure the service has been redeployed after adding variables
- Check Render logs for errors

