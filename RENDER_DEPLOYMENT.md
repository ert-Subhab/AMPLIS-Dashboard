# Render Deployment Guide

This guide will help you deploy your HeyReach Dashboard to Render.

## Prerequisites

1. A GitHub account
2. Your code pushed to a GitHub repository
3. A Render account (free at [render.com](https://render.com))

## Step-by-Step Deployment

### Step 1: Push Your Code to GitHub

If you haven't already, push your code to GitHub:

```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Step 2: Create Render Account

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Sign up for a free account (you can use GitHub to sign in)
3. Verify your email if required

### Step 3: Create a New Web Service

1. In the Render dashboard, click **"New +"** button
2. Select **"Web Service"**
3. Connect your GitHub account if not already connected
4. Select your repository
5. Click **"Connect"**

### Step 4: Configure Your Service

Fill in the configuration:

- **Name**: `heyreach-dashboard` (or any name you prefer)
- **Environment**: Select **"Python 3"**
- **Region**: Choose closest to you (e.g., `Oregon (US West)`)
- **Branch**: `main` (or your default branch)
- **Root Directory**: Leave empty (or specify if your app is in a subdirectory)
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

### Step 5: Set Environment Variables

Click on **"Advanced"** to expand environment variables section, then add:

**Required:**
- `HEYREACH_API_KEY`: Your HeyReach API key (from your config.yaml)
- `HEYREACH_BASE_URL`: `https://api.heyreach.io`

**Optional (if you want to configure senders in production):**
- `HEYREACH_SENDER_IDS`: JSON array string, e.g., `[50083, 50084, 50118]`
- `HEYREACH_SENDER_NAMES`: JSON object string, e.g., `{"50083": "Christopher Bell", "50084": "John Doe"}`
- `HEYREACH_CLIENT_GROUPS`: JSON object string for client groups

**Important Notes:**
- For `HEYREACH_SENDER_IDS`: Enter as JSON array without quotes, e.g., `[50083, 50084]`
- For `HEYREACH_SENDER_NAMES`: Enter as JSON object, e.g., `{"50083": "Name", "50084": "Name2"}`
- For `HEYREACH_CLIENT_GROUPS`: Enter as JSON object with nested structure

### Step 6: Deploy

1. Review your settings
2. Click **"Create Web Service"**
3. Render will start building and deploying your app
4. Wait for the build to complete (usually 2-5 minutes)
5. You'll see a URL like: `https://heyreach-dashboard.onrender.com`

### Step 7: Access Your Dashboard

Once deployed:
1. Click on your service name in the Render dashboard
2. Your app URL will be displayed (e.g., `https://heyreach-dashboard.onrender.com`)
3. Share this URL with others who need access

## Updating Your App

After making changes to your code:

1. Push changes to GitHub:
   ```bash
   git add .
   git commit -m "Your commit message"
   git push origin main
   ```

2. Render will automatically detect the push and redeploy your app
3. Wait for the new deployment to complete

## Free Tier Limitations

Render's free tier includes:
- ✅ 750 hours/month (enough for 24/7 operation)
- ✅ Free SSL certificate
- ✅ Custom domain support
- ✅ Auto-deploy on git push

**Important:** Free tier services "spin down" after 15 minutes of inactivity. The first request after spin-down may take 30-60 seconds to respond while the service starts up.

## Custom Domain (Optional)

To use your own domain:

1. In your service settings, go to **"Custom Domains"**
2. Add your domain name
3. Follow Render's DNS configuration instructions
4. Your app will be accessible at your custom domain

## Environment Variables Format

### Simple Configuration (Just API Key)
```
HEYREACH_API_KEY=your_api_key_here
HEYREACH_BASE_URL=https://api.heyreach.io
```

### Full Configuration (With Senders)
```
HEYREACH_API_KEY=your_api_key_here
HEYREACH_BASE_URL=https://api.heyreach.io
HEYREACH_SENDER_IDS=[50083, 50084, 50118, 50372]
HEYREACH_SENDER_NAMES={"50083": "Christopher Bell", "50084": "John Doe"}
HEYREACH_CLIENT_GROUPS={"Client Name": {"sender_ids": [50083, 50084], "sender_count": 2}}
```

## Troubleshooting

### Build Fails
- Check the build logs in Render dashboard
- Ensure `requirements.txt` is correct
- Verify Python version compatibility

### App Doesn't Start
- Check the runtime logs in Render dashboard
- Verify `HEYREACH_API_KEY` is set correctly
- Ensure start command is `gunicorn app:app`

### Service Spins Down
- This is normal on free tier after 15 minutes of inactivity
- First request will take longer while service starts
- Consider upgrading to paid plan for always-on service

### API Errors
- Verify your API key is correct
- Check that `HEYREACH_BASE_URL` is set correctly
- Review application logs for detailed error messages

## Getting Your Sender IDs and Names as JSON

If you want to include sender configuration, you can export from your `config.yaml`:

**Sender IDs** (from config.yaml):
```yaml
sender_ids:
  - 50083
  - 50084
  - 50118
```

Becomes in environment variable:
```
[50083, 50084, 50118]
```

**Sender Names** (from config.yaml):
```yaml
sender_names:
  50083: Christopher Bell
  50084: John Doe
```

Becomes in environment variable:
```
{"50083": "Christopher Bell", "50084": "John Doe"}
```

## Support

- Render Documentation: [https://render.com/docs](https://render.com/docs)
- Render Status: [https://status.render.com](https://status.render.com)

