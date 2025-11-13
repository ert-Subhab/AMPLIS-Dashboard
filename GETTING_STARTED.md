# 🚀 Getting Started with Outreach Reporting Automation

Welcome! This guide will walk you through setting up your automated reporting system in just a few minutes.

## 📋 What You'll Need

Before you begin, make sure you have:
- [ ] Python 3.8 or higher installed
- [ ] Active HeyReach account with API access
- [ ] Active Smartlead account with API access
- [ ] (Optional) Google Account for Sheets integration
- [ ] (Optional) Gmail account for email reports

---

## 🎯 Quick Start (5 Minutes)

### 1️⃣ Install Dependencies

Open your terminal and run:

```bash
pip install -r requirements.txt
```

### 2️⃣ Get Your API Keys

#### For HeyReach:
1. Go to https://app.heyreach.io
2. Click on **Settings** → **API**
3. Click **Generate API Key**
4. Copy the key

#### For Smartlead:
1. Go to https://app.smartlead.ai
2. Click on **Settings** → **API Keys**
3. Click **Create New API Key**
4. Copy the key

### 3️⃣ Configure the System

Open `config.yaml` in a text editor and update these fields:

```yaml
heyreach:
  api_key: "PASTE_YOUR_HEYREACH_KEY_HERE"

smartlead:
  api_key: "PASTE_YOUR_SMARTLEAD_KEY_HERE"
```

### 4️⃣ Test Your Setup

Run the setup script to verify everything works:

```bash
python setup.py
```

You should see:
```
✅ HeyReach API connection successful
✅ Smartlead API connection successful
✅ Setup completed successfully!
```

### 5️⃣ Generate Your First Report

```bash
python generate_report.py
```

That's it! Your report is now in the `reports/` folder! 🎉

---

## 📊 Understanding Your Reports

### What's Included

Your reports contain:

1. **Overview Metrics**
   - Total outreach actions (LinkedIn + Email)
   - Total responses
   - Overall response rate
   - Active campaigns

2. **LinkedIn Performance**
   - Connection requests sent/accepted
   - Acceptance rate
   - Messages sent
   - Reply rate

3. **Email Performance**
   - Emails sent/delivered
   - Open rate
   - Click rate
   - Reply rate
   - Bounce rate

4. **Interactive Charts**
   - Platform comparison
   - Conversion funnels
   - Performance trends

5. **Recommendations**
   - Actionable insights based on your data
   - Benchmarked against industry standards

---

## 🔧 Advanced Setup (Optional)

### Add Google Sheets Integration

Get a live, auto-updating dashboard:

1. **Create Google Cloud Project**
   - Go to https://console.cloud.google.com
   - Create new project
   - Enable "Google Sheets API"

2. **Create Service Account**
   - Go to "IAM & Admin" → "Service Accounts"
   - Create new service account
   - Download JSON credentials
   - Save as `google_credentials.json` in project folder

3. **Create Google Sheet**
   - Create a new Google Sheet
   - Share it with the email from your JSON file
   - Copy the Spreadsheet ID from URL

4. **Update config.yaml**
   ```yaml
   google_sheets:
     enabled: true
     credentials_file: "google_credentials.json"
     spreadsheet_id: "YOUR_SHEET_ID_HERE"
   ```

### Add Email Reports

Get reports delivered to your inbox:

1. **Setup Gmail App Password**
   - Go to https://myaccount.google.com/security
   - Enable 2-Factor Authentication
   - Go to https://myaccount.google.com/apppasswords
   - Generate app password

2. **Update config.yaml**
   ```yaml
   email_reports:
     enabled: true
     smtp_server: "smtp.gmail.com"
     smtp_port: 587
     sender_email: "your_email@gmail.com"
     sender_password: "YOUR_APP_PASSWORD_HERE"
     recipient_emails:
       - "team_member1@company.com"
       - "team_member2@company.com"
   ```

---

## ⏰ Automate Your Reports

### Option 1: Run the Scheduler

Keep your terminal open and run:

```bash
# For daily reports at 9 AM
python scheduler.py --frequency daily --time "09:00"

# For weekly reports every Monday at 9 AM
python scheduler.py --frequency weekly --day monday --time "09:00"
```

### Option 2: Use Cron (Mac/Linux)

```bash
# Edit crontab
crontab -e

# Add this line for daily reports at 9 AM:
0 9 * * * cd /path/to/outreach-reporting-automation && python generate_report.py
```

### Option 3: Use Task Scheduler (Windows)

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (daily/weekly)
4. Action: Start Program
5. Program: `python`
6. Arguments: `/path/to/generate_report.py`

### Option 4: Deploy to Cloud

See [DEPLOYMENT.md](DEPLOYMENT.md) for cloud deployment options (AWS, Google Cloud, Heroku, etc.)

---

## 🎨 Customization

### Change Date Range

In `config.yaml`:

```yaml
reporting:
  default_date_range: "last_7_days"  # Options: today, yesterday, last_7_days, last_30_days
```

### Modify Report Style

Edit `src/report_generator.py` to customize:
- Colors and themes
- Chart types
- Metrics displayed
- Layout and design

### Add Custom Metrics

Edit `src/data_processor.py` to add your own calculations and KPIs.

---

## 📖 Next Steps

Now that you're set up:

1. ✅ Generate your first report
2. ✅ Review the insights and recommendations
3. ✅ Set up Google Sheets for live dashboard (optional)
4. ✅ Configure email reports (optional)
5. ✅ Schedule automated reports
6. ✅ Customize to your needs

---

## 🆘 Common Issues

### "Module not found" error
**Solution:** Run `pip install -r requirements.txt`

### API keys not working
**Solution:** 
- Make sure you copied the full key
- Check that API access is enabled in your account
- Try regenerating the API key

### Google Sheets not updating
**Solution:**
- Verify service account email has editor access to sheet
- Check that Google Sheets API is enabled
- Ensure `google_credentials.json` is in project root

### Reports not being emailed
**Solution:**
- Use Gmail App Password (not regular password)
- Check SMTP settings in config.yaml
- Verify recipient emails are correct

---

## 💡 Pro Tips

1. **Run reports at the end of your workday** to see full day's data
2. **Compare week-over-week** to spot trends
3. **Share reports with your team** via email or Google Sheets
4. **Use recommendations** to continuously improve campaigns
5. **Export to CSV** for deeper analysis in Excel/Sheets

---

## 🌟 You're All Set!

You now have a powerful automated reporting system for your outreach campaigns. 

**Quick Command Reference:**
```bash
# Test setup
python setup.py

# Generate report once
python generate_report.py

# Schedule automated reports
python scheduler.py --frequency daily --time "09:00"
```

Need more help? Check out:
- [README.md](README.md) - Full documentation
- [INSTALL.md](INSTALL.md) - Detailed installation
- [DEPLOYMENT.md](DEPLOYMENT.md) - Cloud deployment

Happy reporting! 📊
