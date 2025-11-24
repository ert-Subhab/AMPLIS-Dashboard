/**
 * Google Apps Script Template for HeyReach Data Integration
 * 
 * Instructions:
 * 1. Open your Google Sheet
 * 2. Go to Extensions > Apps Script
 * 3. Paste this code
 * 4. Click "Deploy" > "New deployment"
 * 5. Choose "Web app" as type
 * 6. Set "Execute as" to "Me"
 * 7. Set "Who has access" to "Anyone"
 * 8. Click "Deploy"
 * 9. Copy the Web app URL and use it in the dashboard
 */

function doPost(e) {
  try {
    // Parse incoming data
    const data = JSON.parse(e.postData.contents);
    const sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    
    // Clear existing data (optional - remove if you want to append)
    // sheet.clear();
    
    // Get or create headers
    const headers = ['Sender Name', 'Week Start', 'Connections Sent', 'Connections Accepted', 
                     'Acceptance Rate (%)', 'Messages Sent', 'Message Replies', 'Reply Rate (%)',
                     'Open Conversations', 'Interested', 'Leads Not Enrolled'];
    
    // Check if headers exist, if not add them
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(headers);
    }
    
    // Process each sender
    const rows = [];
    data.senders.forEach(sender => {
      sender.weeks.forEach(week => {
        rows.push([
          sender.name,
          week.week_start || '',
          week.connections_sent || 0,
          week.connections_accepted || 0,
          week.acceptance_rate || 0,
          week.messages_sent || 0,
          week.message_replies || 0,
          week.reply_rate || 0,
          week.open_conversations || 0,
          week.interested || 0,
          week.leads_not_enrolled || 0
        ]);
      });
    });
    
    // Append data to sheet
    if (rows.length > 0) {
      sheet.getRange(sheet.getLastRow() + 1, 1, rows.length, headers.length).setValues(rows);
    }
    
    // Return success response
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      message: `Processed ${data.senders.length} senders with ${rows.length} weeks of data`
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    // Return error response
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      error: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Test function - can be run manually to test the script
 */
function testScript() {
  const testData = {
    date_range: {
      start: '2025-11-15',
      end: '2025-11-21'
    },
    senders: [
      {
        name: 'Test Sender',
        weeks: [
          {
            week_start: '2025-11-21',
            connections_sent: 100,
            connections_accepted: 25,
            acceptance_rate: 25.0,
            messages_sent: 50,
            message_replies: 10,
            reply_rate: 20.0,
            open_conversations: 15,
            interested: 5,
            leads_not_enrolled: 2
          }
        ]
      }
    ]
  };
  
  const mockEvent = {
    postData: {
      contents: JSON.stringify(testData)
    }
  };
  
  const result = doPost(mockEvent);
  Logger.log(result.getContent());
}

