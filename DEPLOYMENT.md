# Cloud Deployment Guide

Deploy your outreach reporting automation to the cloud for 24/7 operation.

## Option 1: AWS Lambda (Serverless - Recommended for Cost)

### Benefits
- Pay only for execution time
- No server management
- Automatic scaling
- Free tier available

### Setup Steps

1. **Prepare Lambda Package**
```bash
# Install dependencies locally
pip install -r requirements.txt -t ./package

# Copy your code
cp -r src ./package/
cp generate_report.py ./package/
cp config.yaml ./package/

# Create deployment package
cd package
zip -r ../lambda_function.zip .
```

2. **Create Lambda Function**
- Go to AWS Lambda Console
- Create new function (Python 3.9+)
- Upload `lambda_function.zip`
- Set handler to `generate_report.lambda_handler`
- Add environment variables from `config.yaml`
- Increase timeout to 5 minutes
- Increase memory to 512 MB

3. **Add Lambda Handler to generate_report.py**
```python
def lambda_handler(event, context):
    main()
    return {
        'statusCode': 200,
        'body': 'Report generated successfully'
    }
```

4. **Schedule with EventBridge**
- Go to Amazon EventBridge
- Create new rule
- Set schedule (cron expression)
- Target: Your Lambda function
- Example: `cron(0 9 * * ? *)` for daily at 9 AM UTC

### Cost Estimate
- ~$0-2/month (within free tier for most use cases)

---

## Option 2: Google Cloud Functions

### Benefits
- Simple deployment
- Integrates well with Google Sheets
- Free tier available

### Setup Steps

1. **Prepare for Deployment**
```bash
# Create function directory
mkdir cloud_function
cp -r src cloud_function/
cp generate_report.py cloud_function/main.py
cp requirements.txt cloud_function/
cp config.yaml cloud_function/
```

2. **Modify main.py**
Add entry point:
```python
def http_trigger(request):
    main()
    return 'Report generated', 200
```

3. **Deploy**
```bash
gcloud functions deploy outreach-reporting \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated \
  --entry-point http_trigger \
  --timeout 540s \
  --memory 512MB
```

4. **Schedule with Cloud Scheduler**
```bash
gcloud scheduler jobs create http daily-report \
  --schedule="0 9 * * *" \
  --uri="YOUR_FUNCTION_URL" \
  --http-method=GET
```

### Cost Estimate
- ~$0-3/month (within free tier for most use cases)

---

## Option 3: Heroku (Easy PaaS)

### Benefits
- Very easy to deploy
- Good for Python apps
- Free tier available (with limitations)

### Setup Steps

1. **Create Heroku App**
```bash
# Install Heroku CLI
# Login
heroku login

# Create app
heroku create your-outreach-reporting
```

2. **Create Procfile**
```
worker: python scheduler.py --run-now
```

3. **Deploy**
```bash
git init
git add .
git commit -m "Initial commit"
heroku git:remote -a your-outreach-reporting
git push heroku main
```

4. **Set Config Vars**
```bash
heroku config:set HEYREACH_API_KEY=your_key
heroku config:set SMARTLEAD_API_KEY=your_key
```

5. **Scale Worker**
```bash
heroku ps:scale worker=1
```

### Cost Estimate
- Free tier: $0/month (dyno sleeps after 30 mins)
- Hobby tier: $7/month (always on)

---

## Option 4: DigitalOcean Droplet (Full VM Control)

### Benefits
- Full control
- Predictable pricing
- Can run multiple services

### Setup Steps

1. **Create Droplet**
- Choose Ubuntu 22.04
- Basic plan: $6/month
- SSH into droplet

2. **Install Dependencies**
```bash
sudo apt update
sudo apt install python3-pip git -y
```

3. **Clone and Setup**
```bash
git clone <your-repo-url>
cd outreach-reporting-automation
pip3 install -r requirements.txt
```

4. **Setup Cron Job**
```bash
crontab -e

# Add this line for daily at 9 AM:
0 9 * * * cd /path/to/project && python3 generate_report.py
```

5. **Keep Running (Optional)**
Use systemd or screen/tmux for scheduler:
```bash
screen -S reporting
python3 scheduler.py
# Press Ctrl+A then D to detach
```

### Cost Estimate
- $6-12/month

---

## Option 5: Azure Functions

Similar to AWS Lambda:
1. Create Function App
2. Deploy Python function
3. Use Azure Timer Trigger
4. Configure app settings

---

## Recommended: AWS Lambda + S3

**Best setup for cost and reliability:**

1. Lambda for execution
2. S3 for storing reports
3. SES for sending emails
4. EventBridge for scheduling

Total cost: **~$0-2/month**

---

## Environment Variables

For any cloud platform, set these environment variables:

```bash
HEYREACH_API_KEY=xxx
SMARTLEAD_API_KEY=xxx
GOOGLE_SHEETS_ID=xxx
EMAIL_SENDER=xxx
EMAIL_PASSWORD=xxx
```

Instead of using `config.yaml`, modify your code to read from environment variables in production.

---

## Security Best Practices

1. **Never commit credentials**
   - Use environment variables
   - Use secrets managers (AWS Secrets Manager, GCP Secret Manager)

2. **Restrict API access**
   - Use IAM roles where possible
   - Rotate API keys regularly

3. **Enable logging**
   - Monitor for errors
   - Set up alerts for failures

4. **Backup data**
   - Regular backups of Google Sheets
   - Store reports in cloud storage

---

## Monitoring

### CloudWatch (AWS)
```python
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
```

### Stackdriver (GCP)
Automatically logs to Google Cloud Logging

### Add Health Checks
Create a simple health check endpoint to monitor function health

---

## Cost Comparison

| Platform | Monthly Cost | Setup Difficulty | Best For |
|----------|-------------|------------------|----------|
| AWS Lambda | $0-2 | Medium | Cost optimization |
| GCP Functions | $0-3 | Medium | Google integration |
| Heroku | $0-7 | Easy | Quick deployment |
| DigitalOcean | $6-12 | Medium | Full control |
| Azure Functions | $0-3 | Medium | Azure ecosystem |

---

## Need Help?

- AWS: [Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- GCP: [Cloud Functions Docs](https://cloud.google.com/functions/docs)
- Heroku: [Heroku Python Docs](https://devcenter.heroku.com/categories/python)
