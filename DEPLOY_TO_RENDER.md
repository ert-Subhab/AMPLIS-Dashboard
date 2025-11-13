# Quick Start: Deploy to Render

## ✅ What's Been Done

I've prepared your app for Render deployment:

1. ✅ Updated `app.py` to support environment variables
2. ✅ Added `gunicorn` to `requirements.txt`
3. ✅ Created `render.yaml` for Render configuration
4. ✅ Created `Procfile` as alternative deployment option
5. ✅ Updated `.gitignore` (already had `config.yaml` excluded)

## 📋 What YOU Need to Do

### Step 1: Push Code to GitHub
```bash
git add .
git commit -m "Ready for Render deployment"
git push origin main
```

### Step 2: Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up (free) - you can use GitHub to sign in

### Step 3: Create Web Service
1. Click **"New +"** → **"Web Service"**
2. Connect your GitHub account
3. Select your repository
4. Click **"Connect"**

### Step 4: Configure Service
- **Name**: `heyreach-dashboard` (or your choice)
- **Environment**: `Python 3`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn app:app`

### Step 5: Add Environment Variables
Click **"Advanced"** → **"Environment Variables"**, then add:

**Required:**
- `HEYREACH_API_KEY` = `IPaXhR9LEYf/H5NLCbdE8BScAz6VfEZ9t/AhFYGOeU0=`
- `HEYREACH_BASE_URL` = `https://api.heyreach.io`

**Optional (to match your current config):**
- `HEYREACH_SENDER_IDS` = `[50083, 50084, 50118, ...]` (your full list as JSON)
- `HEYREACH_SENDER_NAMES` = `{"50083": "Christopher Bell", ...}` (your full mapping as JSON)
- `HEYREACH_CLIENT_GROUPS` = `{"Client Name": {...}, ...}` (your groups as JSON)

### Step 6: Deploy
1. Click **"Create Web Service"**
2. Wait 2-5 minutes for build to complete
3. Your app will be live at: `https://heyreach-dashboard.onrender.com`

## 🔗 Quick Links
- Full Guide: See `RENDER_DEPLOYMENT.md`
- Render Dashboard: [dashboard.render.com](https://dashboard.render.com)

## 💡 Tips
- Free tier includes 750 hours/month (enough for 24/7)
- Service spins down after 15 min inactivity (first request takes longer)
- Auto-deploys on every git push
- Custom domain available for free

That's it! Your dashboard will be accessible to anyone with the URL.

