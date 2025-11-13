# HeyReach & Smartlead Automated Reporting System

Complete automation solution for tracking and reporting LinkedIn (HeyReach) and Email (Smartlead) outreach campaigns.

## 🚀 Features

- **Automated Data Collection**: Pulls campaign data from HeyReach and Smartlead APIs
- **Unified Dashboard**: Combines LinkedIn + Email metrics in one view
- **Google Sheets Integration**: Auto-updates a master reporting spreadsheet
- **Daily/Weekly Reports**: Automated email reports with key metrics
- **Campaign Performance Tracking**: Response rates, conversion rates, ROI metrics
- **Visual Analytics**: Charts and graphs for campaign performance
- **Scheduled Automation**: Set it and forget it - runs automatically

## 📊 Metrics Tracked

### HeyReach (LinkedIn)
- Connection requests sent/accepted
- Message sequences sent
- Reply rates
- Conversation stages
- Campaign-level performance

### Smartlead (Email)
- Emails sent/delivered/opened/clicked
- Reply rates
- Bounce rates
- Unsubscribe rates
- Lead status and conversions

## 🛠️ Setup Instructions

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `config.yaml` with your credentials:

```yaml
heyreach:
  api_key: "your_heyreach_api_key"
  
smartlead:
  api_key: "your_smartlead_api_key"

google_sheets:
  credentials_file: "google_credentials.json"
  spreadsheet_id: "your_spreadsheet_id"

email_reports:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "your_email@gmail.com"
  sender_password: "your_app_password"
  recipient_emails:
    - "recipient1@email.com"
    - "recipient2@email.com"
```

### 3. Get API Keys

**HeyReach:**
1. Log in to HeyReach
2. Go to Settings > API
3. Generate new API key

**Smartlead:**
1. Log in to Smartlead
2. Go to Settings > API Keys
3. Create new API key

**Google Sheets:**
1. Go to Google Cloud Console
2. Create a new project
3. Enable Google Sheets API
4. Create Service Account credentials
5. Download JSON file and save as `google_credentials.json`

### 4. Run Initial Setup

```bash
python setup.py
```

This will:
- Verify API connections
- Create Google Sheet template
- Test email configuration

### 5. Run Manual Report

```bash
python generate_report.py
```

### 6. Schedule Automated Reports

**Daily Report (9 AM):**
```bash
python scheduler.py --frequency daily --time "09:00"
```

**Weekly Report (Monday 9 AM):**
```bash
python scheduler.py --frequency weekly --day monday --time "09:00"
```

## 📁 Project Structure

```
outreach-reporting-automation/
├── README.md
├── requirements.txt
├── config.yaml
├── .env.example
├── setup.py
├── generate_report.py
├── scheduler.py
├── src/
│   ├── __init__.py
│   ├── heyreach_client.py
│   ├── smartlead_client.py
│   ├── google_sheets_handler.py
│   ├── data_processor.py
│   ├── report_generator.py
│   └── email_sender.py
├── templates/
│   └── report_template.html
└── reports/
    └── (generated reports saved here)
```

## 🔄 Automation Options

### Option 1: Python Scheduler (Included)
Run the scheduler script - keeps running in background

### Option 2: Cron Job (Linux/Mac)
```bash
# Daily at 9 AM
0 9 * * * cd /path/to/project && python generate_report.py
```

### Option 3: Task Scheduler (Windows)
Create a task that runs `generate_report.py` daily

### Option 4: Cloud Deployment
Deploy to AWS Lambda, Google Cloud Functions, or Heroku for fully automated cloud execution

## 📈 Report Outputs

1. **Google Sheets**: Live updating dashboard
2. **HTML Report**: Visual report with charts (saved locally)
3. **Email Report**: Summary sent to team
4. **CSV Export**: Raw data for custom analysis

## 🎯 Customization

Edit `src/report_generator.py` to:
- Add custom metrics
- Change visualization styles
- Modify report layout
- Add additional data sources

## ⚠️ Troubleshooting

**API Connection Fails:**
- Verify API keys are correct
- Check API rate limits
- Ensure account has API access enabled

**Google Sheets Error:**
- Verify service account has editor access to spreadsheet
- Check credentials file path
- Ensure Google Sheets API is enabled

**Email Not Sending:**
- Use App Password for Gmail (not regular password)
- Enable "Less secure app access" if needed
- Check SMTP settings

## 📞 Support

For issues or questions, check the inline code comments or modify as needed!

## 🔐 Security Notes

- Never commit `config.yaml` or `google_credentials.json` to version control
- Use environment variables for production
- Rotate API keys regularly
- Use app-specific passwords for email

## 📝 License

MIT License - Use freely for your business!
