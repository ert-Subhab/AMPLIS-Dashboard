# Testing Guide: Dashboard Auto-Load Fix

## Quick Test

1. **Start the dashboard**:
   ```bash
   python app.py
   ```

2. **Open browser**: Navigate to `http://localhost:5000`

3. **Verify the following**:
   - ✅ Page loads quickly (< 2 seconds)
   - ✅ No data is automatically loaded on page load
   - ✅ Message appears: "Please select a sender and date range, then click 'Apply Filters' to load data."
   - ✅ Date fields are pre-filled with last 7 days (not 12 weeks)
   - ✅ Sender dropdown is populated

4. **Test data loading**:
   - Select a specific sender (or leave "All")
   - Verify date range (should default to last 7 days)
   - Click "Apply Filters"
   - ✅ Data should load only after clicking the button
   - ✅ Loading indicator appears while fetching
   - ✅ Data displays in tables and charts

5. **Test warning dialog**:
   - Select "All" senders
   - Set start date to 31+ days ago
   - Click "Apply Filters"
   - ✅ Confirmation dialog should appear: "You're about to load data for ALL senders over X days..."
   - Click "OK" to proceed or "Cancel" to abort

## Expected Behavior

### On Page Load:
- **API Calls**: Only 1 call to `/api/senders` (to populate dropdown)
- **Performance Data Calls**: 0 calls
- **Page Load Time**: < 2 seconds
- **User Message**: Displayed prompting user to select filters

### When User Clicks "Apply Filters":
- **API Calls**: 
  - 1 sender selected: ~1 API call per week in date range
  - "All" senders: ~70 API calls per week in date range
- **Loading Indicator**: Displayed during data fetch
- **Data Display**: Shows in summary cards, tables, and charts

### With Default Settings (7 days, All senders):
- **API Calls**: ~70 calls (1 per sender)
- **Load Time**: ~10-30 seconds (depending on API response time)
- **User Experience**: Controlled by user, not forced on page load

## Performance Comparison

### Before Fix:
- **Page Load**: 840+ API calls (70 senders × 12 weeks)
- **Load Time**: 30+ seconds
- **User Control**: None - forced to wait for all data

### After Fix:
- **Page Load**: 1 API call (sender list only)
- **Load Time**: < 2 seconds
- **User Control**: Full control - loads data only when requested

## Troubleshooting

### If page still loads slowly:
1. Check browser console for errors
2. Verify no automatic data loading is happening
3. Check network tab - should only see `/api/senders` call on load

### If message doesn't appear:
1. Check browser console for JavaScript errors
2. Verify `showMessage()` function exists in dashboard.js
3. Check if filters section exists in HTML

### If data doesn't load when clicking "Apply Filters":
1. Check browser console for errors
2. Verify API endpoints are working: `http://localhost:5000/api/senders`
3. Check server logs for API errors
4. Verify date range is valid (not too far in past)

## Success Criteria

✅ Dashboard loads in < 2 seconds
✅ No performance data loaded on page load
✅ User message displayed correctly
✅ Data loads only when user clicks "Apply Filters"
✅ Warning dialog appears for large date ranges
✅ All functionality works as expected

