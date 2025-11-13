# Quick Installation Guide

## 🚀 5-Minute Setup

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure Your API Keys

1. Open `config.yaml`
2. Replace placeholder values with your actual API keys:
   - HeyReach API key
   - Smartlead API key
   - Google Sheets credentials (optional)
   - Email settings (optional)

### Step 3: Get Your API Keys

#### HeyReach API Key
1. Login to [HeyReach](https://app.heyreach.io)
2. Navigate to Settings → API
3. Generate a new API key
4. Copy and paste into `config.yaml`

#### Smartlead API Key
1. Login to [Smartlead](https://app.smartlead.ai)
2. Go to Settings → API Keys
3. Create a new API key
4. Copy and paste into `config.yaml`

#### Google Sheets (Optional)
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable Google Sheets API
4. Create Service Account credentials
5. Download JSON file
6. Save as `google_credentials.json` in project root
7. Create a new Google Sheet
8. Share it with the service account email (found in JSON file)
9. Copy the Spreadsheet ID from the URL and add to `config.yaml`

#### Gmail (Optional for Email Reports)
1. Use your Gmail account
2. Enable 2-Factor Authentication
3. Generate an [App Password](https://myaccount.google.com/apppasswords)
4. Use the app password (not your regular password) in `config.yaml`

### Step 4: Run Setup

```bash
python setup.py
```

This will verify all your connections and create the Google Sheets dashboard template.

### Step 5: Generate Your First Report

```bash
python generate_report.py
```

Your report will be saved in the `reports/` folder!

### Step 6: Schedule Automated Reports (Optional)

For daily reports at 9 AM:
```bash
python scheduler.py --frequency daily --time "09:00"
```

For weekly reports every Monday at 9 AM:
```bash
python scheduler.py --frequency weekly --day monday --time "09:00"
```

---

## 🎯 What You Get

✅ **Automated Data Collection** from HeyReach and Smartlead  
✅ **Beautiful HTML Reports** with charts and visualizations  
✅ **Live Google Sheets Dashboard** (optional)  
✅ **Email Reports** sent automatically (optional)  
✅ **Performance Recommendations** based on your data  

---

## 🆘 Troubleshooting

### "Module not found" error
```bash
pip install -r requirements.txt
```

### "API connection failed"
- Verify your API keys are correct
- Check that you have API access enabled in your account
- Ensure you're not hitting rate limits

### Google Sheets errors
- Verify the service account has editor access to your spreadsheet
- Check that Google Sheets API is enabled in Google Cloud Console
- Make sure the `google_credentials.json` file exists

### Email not sending
- Use Gmail App Password, not your regular password
- Enable "Less secure app access" if needed
- Verify SMTP settings are correct

---

## 📞 Need Help?

Check the main [README.md](README.md) for detailed documentation!
