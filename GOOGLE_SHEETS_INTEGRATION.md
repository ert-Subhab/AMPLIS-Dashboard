# Google Sheets Integration Guide

This guide explains how to use the Google Sheets integration feature to automatically populate your HeyReach performance data into Google Sheets.

## Overview

The Google Sheets integration allows you to:
- Automatically populate HeyReach performance data into your Google Sheets
- Match senders by name across HeyReach and your sheets
- Populate data only in empty cells (won't overwrite existing data)
- Support multiple worksheets (one per client)
- Aggregate weekly data across your selected date range

## Setup

### 1. Install Dependencies

The required libraries are already in `requirements.txt`:
```bash
pip install -r requirements.txt
```

This will install:
- `gspread` - Google Sheets API client
- `google-auth` - Google authentication library

### 2. Google Sheets Setup

#### Option A: Using Service Account (Recommended for Write Access)

1. **Create a Google Cloud Project** (if you don't have one):
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Google Sheets API**:
   - In the Google Cloud Console, go to "APIs & Services" > "Library"
   - Search for "Google Sheets API" and enable it

3. **Create a Service Account**:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Give it a name (e.g., "sheets-integration")
   - Click "Create and Continue"
   - Skip the optional steps and click "Done"

4. **Create and Download JSON Key**:
   - Click on the service account you just created
   - Go to "Keys" tab
   - Click "Add Key" > "Create new key"
   - Select "JSON" format
   - Download the JSON file

5. **Share Your Google Sheet with Service Account**:
   - Open your Google Sheet
   - Click "Share" button
   - Add the service account email (found in the JSON file as `client_email`)
   - Give it "Editor" permissions
   - Click "Send"

6. **Set Up Credentials** (Choose one method):

   **Method 1: Environment Variable** (Recommended for production):
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/service-account-key.json"
   ```

   **Method 2: Default Location**:
   - Place the JSON file at: `~/.config/gspread/service_account.json`
   - On Windows: `C:\Users\YourUsername\.config\gspread\service_account.json`

   **Method 3: Code Integration** (For custom setup):
   - You can modify the code to load credentials from a config file

#### Option B: Public Sheet (Read-Only)

If your sheet is publicly accessible, you can read from it, but you'll need service account credentials to write to it.

## Usage

### 1. Access the Dashboard

1. Open the dashboard in your browser
2. Enter your HeyReach API key and click "Connect & Load Senders"
3. The Google Sheets section will appear below the API key section

### 2. Enter Google Sheets URL

1. Open your Google Sheet
2. Copy the URL from the address bar
3. Paste it into the "Google Sheets URL" field in the dashboard

Example URL format:
```
https://docs.google.com/spreadsheets/d/1bNPHqfcNxzAup1cz5eJONegrsLp06l1IoM6nRhVG-RM/edit#gid=1640415884
```

### 3. Select Date Range

1. Select the start date and end date for the data you want to populate
2. Optionally select a specific sender (or leave as "All")

### 4. Populate Sheets

1. Click "Populate Sheets with HeyReach Data"
2. Wait for the process to complete
3. Check the success message to see how many cells were updated

## How It Works

### Sheet Structure Detection

The integration automatically detects:
- **Senders**: Names in the first column (e.g., "Jason Meyer")
- **Metrics**: Column headers like "Connections Sent", "Messages Sent", etc.
- **Worksheets**: Each tab is treated as a separate client

### Sender Matching

The system matches HeyReach sender names to sheet sender names using:
1. Exact match (case-insensitive)
2. Partial match (if one name contains the other)

### Data Population

- **Aggregation**: Data from all weeks in your date range is aggregated (summed)
- **Rates**: Acceptance rate and reply rate are calculated automatically
- **Empty Cells Only**: Only populates cells that are currently empty
- **No Overwrites**: Won't overwrite existing data

### Supported Metrics

The following metrics are automatically populated:
- Connections Sent
- Connections Accepted
- Acceptance Rate (%)
- Messages Sent
- Message Replies
- Reply Rate (%)
- Open Conversations
- Interested
- Leads Not Yet Enrolled

## Example Sheet Structure

Your Google Sheet should be structured like this:

```
| A              | B      | C                    | D                    | ...
|----------------|--------|----------------------|----------------------|
| 2025           |        |                      |                      |
| Jason Meyer    |        |                      |                      |
| Connections Sent| 176   |                      |                      |
| Connections Accepted| 49|                      |                      |
| Acceptance Rate| 27.84% |                      |                      |
| Messages Sent  | 46     |                      |                      |
| Message Replies| 16     |                      |                      |
| Reply Rate     | 34.78% |                      |                      |
| Open Conversations| 46  |                      |                      |
| Interested     | 0      |                      |                      |
| Leads Not Yet Enrolled| 0|                      |                      |
```

## Troubleshooting

### "No Google Sheets credentials provided"

**Solution**: Set up service account credentials as described in the Setup section above.

### "Failed to connect to Google Sheets"

**Possible causes**:
- Invalid Google Sheets URL
- Sheet is not shared with the service account
- Service account credentials are incorrect

**Solutions**:
- Verify the URL is correct
- Share the sheet with the service account email
- Check that credentials are set up correctly

### "No senders found in worksheet"

**Possible causes**:
- Sheet structure doesn't match expected format
- Sender names are not in the first column

**Solutions**:
- Ensure sender names are in column A
- Make sure sender names are not empty
- Check that the sheet has data

### "No HeyReach data found for sender"

**Possible causes**:
- Sender name doesn't match between HeyReach and the sheet
- No data available for the selected date range

**Solutions**:
- Check sender names match exactly (case-insensitive)
- Verify the date range has data in HeyReach
- Check HeyReach API key is correct

### Cells not updating

**Possible causes**:
- Cells already have values (won't overwrite)
- Service account doesn't have write permissions
- Sheet is not shared with service account

**Solutions**:
- Clear cells you want to update
- Share sheet with service account email
- Grant "Editor" permissions to service account

## Security Notes

- **Service Account Credentials**: Keep your service account JSON file secure. Never commit it to version control.
- **Sheet Permissions**: Only share sheets with the service account that need to be updated.
- **API Keys**: Your HeyReach API key is stored in browser session only (not persisted).

## Advanced Usage

### Multiple Worksheets

If your sheet has multiple tabs (worksheets), each one will be processed separately. The system will:
1. Parse each worksheet to find senders
2. Match senders with HeyReach data
3. Populate metrics for each sender

### Custom Date Ranges

You can populate data for any date range:
- Select start and end dates in the dashboard
- Data from all weeks in that range will be aggregated
- Only data available in HeyReach will be populated

## Support

If you encounter issues:
1. Check the browser console for error messages
2. Check the Flask server logs for detailed error information
3. Verify your Google Sheets setup (credentials, sharing, etc.)
4. Verify your HeyReach API key is correct

