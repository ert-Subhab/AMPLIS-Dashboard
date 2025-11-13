# HeyReach Performance Dashboard

A fully functional web dashboard for tracking HeyReach performance metrics with weekly aggregation, sender filtering, and customizable date ranges.

## Features

- **Sender Selection**: Filter by individual sender or view all senders
- **Custom Date Ranges**: Select any start and end date for reporting
- **Weekly Performance Tracking**: Data aggregated by week (Saturday to Friday)
- **Real-time Data**: Fetches live data from HeyReach API
- **Visual Charts**: Interactive charts showing performance trends
- **Separate Outputs**: Each sender's data is displayed separately
- **Auto-population**: Dashboard automatically populates with the latest data

## Metrics Tracked

- Connections Sent
- Connections Accepted
- Acceptance Rate
- Messages Sent
- Message Replies
- Reply Rate
- Open Conversations
- Interested
- Leads Not Yet Enrolled

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Key

The API key is already configured in `config.yaml`:
```yaml
heyreach:
  api_key: "IPaXhR9LEYf/H5NLCbdE8BScAz6VfEZ9t/AhFYGOeU0="
  base_url: "https://api.heyreach.io"
```

### 3. Run the Dashboard

```bash
python app.py
```

The dashboard will be available at: `http://localhost:5000`

### 4. Access the Dashboard

Open your web browser and navigate to:
```
http://localhost:5000
```

## Usage

### Filtering by Sender

1. Select a sender from the dropdown (or "All" for all senders)
2. Click "Apply Filters" to update the data

### Custom Date Range

1. Select a start date and end date
2. Click "Apply Filters" to load data for that range

### Weekly View

- Data is automatically grouped by week (Saturday to Friday)
- Each week shows all metrics for that period
- Charts show trends over time

### Refresh Data

- Click the "Refresh Data" button to reload the latest data from HeyReach

## API Endpoints

The dashboard uses the following API endpoints:

- `GET /api/senders` - Get list of all senders
- `GET /api/performance?sender_id=<id>&start_date=<date>&end_date=<date>` - Get performance data
- `GET /api/summary?sender_id=<id>&start_date=<date>&end_date=<date>` - Get summary metrics
- `GET /api/health` - Health check

## File Structure

```
.
├── app.py                      # Flask application
├── heyreach_client.py          # HeyReach API client
├── config.yaml                 # Configuration file
├── templates/
│   └── dashboard.html          # Dashboard HTML template
├── static/
│   ├── css/
│   │   └── dashboard.css       # Dashboard styles
│   └── js/
│       └── dashboard.js        # Dashboard JavaScript
└── requirements.txt            # Python dependencies
```

## Troubleshooting

### Dashboard shows no data

1. Check that the API key is correct in `config.yaml`
2. Verify you have active campaigns in HeyReach
3. Check the browser console for errors
4. Check the Flask server logs for API errors

### API connection errors

1. Verify your internet connection
2. Check that the HeyReach API is accessible
3. Verify the API key has proper permissions
4. Check the Flask server logs for detailed error messages

### Date range issues

- Ensure start date is before end date
- Dates should be in YYYY-MM-DD format
- Default range is last 12 weeks if not specified

## Weekly Auto-population

The dashboard automatically:
- Groups data by week (Saturday to Friday)
- Aggregates metrics per week
- Updates charts and tables with new data
- Maintains separate data for each sender

## Customization

### Change Default Date Range

Edit `static/js/dashboard.js`:
```javascript
// Change 84 days (12 weeks) to your preferred range
startDate.setDate(startDate.getDate() - 84);
```

### Modify Metrics

Edit `heyreach_client.py` in the `get_sender_weekly_performance` method to add or modify metrics.

### Styling

Edit `static/css/dashboard.css` to customize the appearance.

## Support

For issues or questions:
1. Check the Flask server logs
2. Check the browser console for JavaScript errors
3. Verify API connectivity and permissions
4. Review the HeyReach API documentation

## License

This project is part of the outreach-reporting-automation system.
