# Google Service Account Setup Guide

## What are Google Service Account Credentials?

A **Google Service Account** is a special type of Google account that represents an application (like our dashboard) rather than a user. It's used to authenticate and authorize your application to access Google services (like Google Sheets) programmatically.

Think of it like this:
- **Regular Google Account**: You log in as yourself
- **Service Account**: Your application logs in as itself (with its own email address)

## Why Do We Need Them?

To write data to your Google Sheets automatically, Google needs to know:
1. **Who is making the request** (authentication)
2. **What permissions they have** (authorization)

Service account credentials provide both - they prove your application's identity and grant it permission to edit your sheets.

## Step-by-Step Setup Guide

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click the project dropdown at the top (it may say "Select a project")
4. Click **"New Project"**
5. Enter a project name (e.g., "HeyReach Sheets Integration")
6. Click **"Create"**
7. Wait a few seconds, then select your new project from the dropdown

### Step 2: Enable Google Sheets API

1. In the Google Cloud Console, make sure your project is selected
2. Go to **"APIs & Services"** > **"Library"** (in the left sidebar)
3. Search for **"Google Sheets API"**
4. Click on **"Google Sheets API"**
5. Click the **"Enable"** button
6. Wait for it to enable (usually takes a few seconds)

### Step 3: Create a Service Account

1. Go to **"APIs & Services"** > **"Credentials"** (in the left sidebar)
2. Click **"+ CREATE CREDENTIALS"** at the top
3. Select **"Service account"** from the dropdown
4. Fill in the service account details:
   - **Service account name**: `sheets-integration` (or any name you prefer)
   - **Service account ID**: Will auto-fill (you can leave it as is)
   - **Description**: "Service account for HeyReach Sheets integration" (optional)
5. Click **"Create and Continue"**
6. **Skip the optional steps** (Grant this service account access to project, Grant users access to this service account)
   - Just click **"Done"** without filling anything

### Step 4: Create and Download JSON Key

1. You should now see your service account in the list
2. Click on the service account email (it will look like: `sheets-integration@your-project-id.iam.gserviceaccount.com`)
3. Go to the **"Keys"** tab
4. Click **"Add Key"** > **"Create new key"**
5. Select **"JSON"** as the key type
6. Click **"Create"**
7. A JSON file will automatically download to your computer
   - **Important**: Keep this file safe! It contains your credentials.
   - **File name**: Usually something like `your-project-id-xxxxx.json`

### Step 5: Share Your Google Sheet with the Service Account

1. Open your Google Sheet (the one you want to populate)
2. Click the **"Share"** button (top right)
3. In the service account JSON file you downloaded, find the `"client_email"` field
   - It looks like: `"client_email": "sheets-integration@your-project-id.iam.gserviceaccount.com"`
4. Copy that email address
5. Paste it into the "Add people and groups" field in the Share dialog
6. Make sure the permission is set to **"Editor"** (not "Viewer")
7. **Uncheck** "Notify people" (the service account doesn't need email notifications)
8. Click **"Share"**

### Step 6: Set Up Credentials in Your Application

You have three options for providing credentials to the application:

#### Option A: Environment Variable (Recommended for Production)

1. Place your JSON file in a secure location on your computer
2. Set an environment variable pointing to it:

   **Windows (PowerShell):**
   ```powershell
   $env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\your\service-account-key.json"
   ```

   **Windows (Command Prompt):**
   ```cmd
   set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\your\service-account-key.json
   ```

   **Linux/Mac:**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
   ```

3. Make sure to set this before running your application

#### Option B: Default Location (Easiest for Local Development)

1. Create the directory structure:
   - **Windows**: `C:\Users\YourUsername\.config\gspread\`
   - **Linux/Mac**: `~/.config/gspread/`

2. Copy your JSON file to that location and rename it to `service_account.json`:
   - **Windows**: `C:\Users\YourUsername\.config\gspread\service_account.json`
   - **Linux/Mac**: `~/.config/gspread/service_account.json`

3. The application will automatically find it there

#### Option C: Modify Code (For Custom Setup)

If you want to load credentials from a different location, you can modify the code to read from a config file or environment variable.

## What the JSON File Contains

Your service account JSON file looks like this:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "xxxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n",
  "client_email": "sheets-integration@your-project-id.iam.gserviceaccount.com",
  "client_id": "xxxxx",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

**Important Security Notes:**
- **Never share this file publicly**
- **Never commit it to version control (Git)**
- **Keep it secure** - anyone with this file can access your Google Sheets
- If you accidentally share it, delete the key in Google Cloud Console and create a new one

## Testing Your Setup

Once you've set up the credentials:

1. Make sure your Google Sheet is shared with the service account email
2. Run your application
3. Try populating a sheet
4. If it works, you'll see data appear in your sheet!

## Troubleshooting

### "No Google Sheets credentials provided"

**Solution**: Make sure you've set up the credentials using one of the methods above.

### "Failed to connect to Google Sheets"

**Possible causes:**
- Sheet is not shared with the service account
- Service account doesn't have Editor permissions
- JSON file path is incorrect

**Solutions:**
- Double-check the sheet is shared with the service account email
- Verify the service account has "Editor" (not "Viewer") permissions
- Check that the JSON file path is correct

### "Permission denied"

**Solution**: Make sure the service account email has "Editor" access to the sheet, not just "Viewer".

## Quick Reference

**Service Account Email Format:**
```
your-service-account-name@your-project-id.iam.gserviceaccount.com
```

**Where to find it:**
- In the JSON file: `"client_email"` field
- In Google Cloud Console: Service Accounts page

**Required Permissions:**
- Google Sheets API: Enabled
- Sheet Access: Editor (not Viewer)

## Next Steps

Once you have your credentials set up:
1. Share your Google Sheet with the service account email
2. Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable OR place the JSON in the default location
3. Run your application
4. Use the Google Sheets integration feature in the dashboard!

## Need Help?

If you encounter issues:
1. Check that Google Sheets API is enabled
2. Verify the service account exists and has a key
3. Confirm the sheet is shared with the service account email
4. Make sure the JSON file path is correct
5. Check the application logs for detailed error messages

