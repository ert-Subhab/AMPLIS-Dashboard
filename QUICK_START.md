# HeyReach Dashboard - Quick Start Guide

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Dashboard

**Windows:**
```bash
run_dashboard.bat
```

**Linux/Mac:**
```bash
chmod +x run_dashboard.sh
./run_dashboard.sh
```

**Or directly:**
```bash
python app.py
```

### 3. Open Dashboard

Open your web browser and navigate to:
```
http://localhost:5000
```

## 📊 Features

✅ **Sender Selection**: Filter by individual sender or view all senders  
✅ **Custom Date Ranges**: Select any start and end date  
✅ **Weekly Performance**: Data grouped by week (Saturday to Friday)  
✅ **Real-time Data**: Fetches live data from HeyReach API  
✅ **Visual Charts**: Interactive performance charts  
✅ **Separate Outputs**: Each sender's data displayed separately  
✅ **Auto-population**: Dashboard automatically loads latest data  

## 📈 Metrics Tracked

- Connections Sent
- Connections Accepted
- Acceptance Rate (%)
- Messages Sent
- Message Replies
- Reply Rate (%)
- Open Conversations
- Interested
- Leads Not Yet Enrolled

## 🎯 How to Use

1. **Select Sender**: Choose a sender from the dropdown (or "All" for all senders)
2. **Select Date Range**: Choose start and end dates
3. **Apply Filters**: Click "Apply Filters" to load data
4. **View Results**: See performance tables and charts for each sender

## 🔧 Configuration

The API key is already configured in `config.yaml`:
```yaml
heyreach:
  api_key: "IPaXhR9LEYf/H5NLCbdE8BScAz6VfEZ9t/AhFYGOeU0="
  base_url: "https://api.heyreach.io"
```

## 🐛 Troubleshooting

### No Data Showing

1. Check that you have active campaigns in HeyReach
2. Verify the date range has data
3. Check the browser console for errors
4. Check the Flask server logs for API errors

### API Connection Errors

1. Verify your internet connection
2. Check that the HeyReach API is accessible
3. Verify the API key has proper permissions
4. Check the Flask server logs for detailed errors

### Dashboard Not Loading

1. Ensure Flask is installed: `pip install flask flask-cors`
2. Check that port 5000 is available
3. Check the Flask server logs for errors

## 📝 Notes

- Data is automatically grouped by week (Saturday to Friday)
- Each sender's data is displayed in a separate table
- Charts show trends over time
- The dashboard refreshes data when filters are applied

## 🔄 Weekly Auto-population

The dashboard automatically:
- Groups data by week (Saturday to Friday)
- Aggregates metrics per week
- Updates charts and tables with new data
- Maintains separate data for each sender

## 📚 API Endpoints

- `GET /api/senders` - Get list of all senders
- `GET /api/performance?sender_id=<id>&start_date=<date>&end_date=<date>` - Get performance data
- `GET /api/summary?sender_id=<id>&start_date=<date>&end_date=<date>` - Get summary metrics
- `GET /api/health` - Health check

## 🎨 Customization

### Change Default Date Range

Edit `static/js/dashboard.js`:
```javascript
// Change 84 days (12 weeks) to your preferred range
startDate.setDate(startDate.getDate() - 84);
```

### Modify Styling

Edit `static/css/dashboard.css` to customize appearance.

### Modify Metrics

Edit `heyreach_client.py` in the `get_sender_weekly_performance` method to add or modify metrics.

## 📞 Support

For issues or questions:
1. Check the Flask server logs
2. Check the browser console for JavaScript errors
3. Verify API connectivity and permissions
4. Review the HeyReach API documentation

## 🎉 You're All Set!

The dashboard is ready to use. Just run `python app.py` and open `http://localhost:5000` in your browser!
