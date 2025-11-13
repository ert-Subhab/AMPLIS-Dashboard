# 🔄 UPDATE INSTRUCTIONS - Fixed API Integration

I've updated your code to work with the actual HeyReach and Smartlead APIs!

## 🎯 What I Fixed

1. ✅ **Correct API Endpoints** - Updated to match actual HeyReach and Smartlead documentation
2. ✅ **Sender-Based Reporting** - LinkedIn data now grouped by sender (LinkedIn account) instead of campaigns
3. ✅ **Weekly Format** - Added Saturday to Friday weekly reporting
4. ✅ **Proper Authentication** - Fixed API key headers

---

## 📥 How to Apply Updates

### Method 1: Replace Files (Easiest)

Download these 4 updated files and replace them in your project:

1. **heyreach_client.py** - Copy to `src/` folder
2. **smartlead_client.py** - Copy to `src/` folder  
3. **generate_report.py** - Copy to root folder
4. **config.yaml** - Copy to root folder (but keep your API keys!)

### Method 2: PowerShell Commands

In your project folder, run:

```powershell
# Backup your current config (to save API keys)
copy config.yaml config.yaml.backup

# Download and replace files
# Then restore your API keys from config.yaml.backup
```

---

## ⚙️ Updated Config Settings

Your `config.yaml` now supports these date ranges:

- `today` - Just today
- `yesterday` - Yesterday only
- `last_7_days` - Rolling 7 days
- `last_30_days` - Rolling 30 days
- **`this_week_sat_fri`** ⭐ - This week (Saturday to Friday)
- **`last_week_sat_fri`** ⭐ - Last week (Saturday to Friday)
- `this_month` - Current month
- `last_month` - Previous month

Current default: `this_week_sat_fri`

---

## 🔑 What Changed in APIs

### HeyReach Changes:
- **Base URL**: `https://api.heyreach.io` (removed /v1)
- **Auth Header**: `X-API-KEY` instead of `Authorization: Bearer`
- **Endpoint**: `POST /api/public/campaign/GetAll`
- **New**: Gets LinkedIn accounts and groups by sender

### Smartlead Changes:
- **Base URL**: `https://server.smartlead.ai` (removed /api/v1)
- **Endpoint**: `GET /api/v1/campaigns?api_key={key}`
- **Auth**: API key in query parameter

---

## 📊 New Report Features

### LinkedIn (By Sender)
Your report will now show:
- Metrics grouped by LinkedIn account/sender
- Each sender's performance separately
- Total campaigns per sender
- Acceptance rates per sender
- Reply rates per sender

### Weekly View
- Automatically calculates Saturday-Friday weeks
- Shows current week or last week
- Perfect for weekly team reports

---

## 🚀 Next Steps

1. **Download the 4 updated files** from the links above
2. **Replace them** in your project folder
3. **Keep your API keys** in config.yaml
4. **Run**: `python generate_report.py`

Your report should now populate with real data! 🎉

---

## ⚠️ Important Notes

- The HeyReach API field names might vary slightly from my assumptions
- If data still doesn't show, we may need to inspect the actual API response
- You can test individual endpoints at:
  - HeyReach: https://documenter.getpostman.com/view/23808049/2sA2xb5F75
  - Smartlead: https://help center.smartlead.ai/en/articles/125-full-api-documentation

---

## 🆘 Still Having Issues?

If the report is still empty after updating:

1. Check PowerShell output for error messages
2. Verify your API keys have proper permissions
3. Confirm you have active campaigns in both platforms
4. Let me know what errors you see!
