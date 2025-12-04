/**
 * Google Apps Script for HeyReach Data Integration
 * 
 * FORMAT SUPPORTED:
 * - Each CLIENT has its own SHEET TAB (e.g., "Amplis", "PAC", "Arena")
 * - Row 1: Year in column A, week dates (M/D format) in columns B+
 * - Senders are in separate rows within each client's sheet
 * - Metrics follow each sender (Connections Sent, Connections Accepted, etc.)
 * 
 * Instructions:
 * 1. Open your Google Sheet
 * 2. Go to Extensions > Apps Script
 * 3. Paste this code (replace any existing code)
 * 4. Click "Deploy" > "New deployment"
 * 5. Choose "Web app" as type
 * 6. Set "Execute as" to "Me"
 * 7. Set "Who has access" to "Anyone"
 * 8. Click "Deploy" and copy the Web app URL
 */

function doPost(e) {
  try {
    // Parse incoming data
    let data;
    try {
      data = JSON.parse(e.postData.contents);
    } catch (parseError) {
      return ContentService.createTextOutput(JSON.stringify({
        success: false,
        error: 'Failed to parse JSON data: ' + parseError.toString()
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const allSheets = spreadsheet.getSheets();
    const sheetNames = allSheets.map(s => s.getName().toLowerCase().trim());
    
    const results = {
      success: true,
      processed: [],
      not_found: [],
      errors: [],
      debug: {
        total_senders: data.senders ? data.senders.length : 0,
        sheets_available: allSheets.map(s => s.getName()),
        client_groups: data.client_groups ? Object.keys(data.client_groups) : []
      }
    };
    
    // Get client groups mapping from incoming data
    const clientGroups = data.client_groups || {};
    
    // Build sender_id to client mapping
    const senderToClient = {};
    for (const [clientName, clientData] of Object.entries(clientGroups)) {
      const senderIds = clientData.sender_ids || clientData || [];
      if (Array.isArray(senderIds)) {
        for (const senderId of senderIds) {
          senderToClient[senderId] = clientName;
        }
      }
    }
    
    results.debug.sender_to_client_count = Object.keys(senderToClient).length;
    
    // Process each sender
    if (!data.senders || !Array.isArray(data.senders)) {
      return ContentService.createTextOutput(JSON.stringify({
        success: false,
        error: 'No senders array in data'
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    for (const sender of data.senders) {
      const senderName = sender.name;
      const senderId = sender.sender_id;
      const weeks = sender.weeks || [];
      
      if (!senderName || weeks.length === 0) {
        results.not_found.push({
          sender: senderName,
          reason: 'No name or no week data'
        });
        continue;
      }
      
      // Find which client this sender belongs to
      let clientName = null;
      
      // Method 1: Use sender_id to find client
      if (senderId && senderToClient[senderId]) {
        clientName = senderToClient[senderId];
      }
      
      // Method 2: Check if sender is in client_groups by name
      if (!clientName) {
        for (const [client, clientData] of Object.entries(clientGroups)) {
          const senderIds = clientData.sender_ids || clientData || [];
          if (Array.isArray(senderIds) && senderIds.includes(senderId)) {
            clientName = client;
            break;
          }
        }
      }
      
      // Method 3: Try to find a sheet that contains this sender name
      if (!clientName) {
        for (const sheet of allSheets) {
          const sheetName = sheet.getName();
          if (findSenderRow(sheet, senderName)) {
            clientName = sheetName;
            break;
          }
        }
      }
      
      if (!clientName) {
        results.not_found.push({
          sender: senderName,
          sender_id: senderId,
          reason: 'Could not determine client for this sender'
        });
        continue;
      }
      
      // Find the sheet for this client
      const sheet = findSheetByClientName(spreadsheet, clientName, sheetNames);
      
      if (!sheet) {
        results.not_found.push({
          sender: senderName,
          client: clientName,
          reason: 'Sheet not found for client: ' + clientName
        });
        continue;
      }
      
      // Find sender row in the sheet
      const senderRow = findSenderRow(sheet, senderName);
      
      if (!senderRow) {
        results.not_found.push({
          sender: senderName,
          client: clientName,
          sheet: sheet.getName(),
          reason: 'Sender not found in sheet'
        });
        continue;
      }
      
      // Update data for this sender
      try {
        const updateResult = updateSenderData(sheet, senderRow, weeks);
        results.processed.push({
          sender: senderName,
          sender_id: senderId,
          client: clientName,
          sheet: sheet.getName(),
          row: senderRow,
          weeks_updated: updateResult.weeks_updated,
          cells_updated: updateResult.cells_updated
        });
      } catch (updateError) {
        results.errors.push({
          sender: senderName,
          client: clientName,
          error: updateError.toString()
        });
      }
    }
    
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      message: `Processed ${results.processed.length} senders, ${results.not_found.length} not found`,
      results: results
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      error: error.toString(),
      stack: error.stack
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Find sheet by client name (handles partial matches and common variations)
 */
function findSheetByClientName(spreadsheet, clientName, sheetNames) {
  const normalizedClient = clientName.toLowerCase().trim();
  
  // Try exact match first
  let sheet = spreadsheet.getSheetByName(clientName);
  if (sheet) return sheet;
  
  // Try case-insensitive match
  for (const existingSheet of spreadsheet.getSheets()) {
    const sheetName = existingSheet.getName();
    if (sheetName.toLowerCase().trim() === normalizedClient) {
      return existingSheet;
    }
  }
  
  // Try partial match (sheet name contains client name or vice versa)
  for (const existingSheet of spreadsheet.getSheets()) {
    const sheetName = existingSheet.getName().toLowerCase().trim();
    if (sheetName.includes(normalizedClient) || normalizedClient.includes(sheetName)) {
      return existingSheet;
    }
  }
  
  // Try matching first word
  const clientFirstWord = normalizedClient.split(' ')[0];
  if (clientFirstWord.length >= 3) {
    for (const existingSheet of spreadsheet.getSheets()) {
      const sheetName = existingSheet.getName().toLowerCase().trim();
      const sheetFirstWord = sheetName.split(' ')[0];
      if (sheetFirstWord === clientFirstWord || sheetName.startsWith(clientFirstWord)) {
        return existingSheet;
      }
    }
  }
  
  return null;
}

/**
 * Find the row where a sender's data starts
 */
function findSenderRow(sheet, senderName) {
  const dataRange = sheet.getDataRange();
  const values = dataRange.getValues();
  const normalizedSenderName = senderName.toLowerCase().trim();
  
  for (let rowIdx = 0; rowIdx < values.length; rowIdx++) {
    const firstCell = values[rowIdx][0];
    if (!firstCell) continue;
    
    const cellValue = String(firstCell).toLowerCase().trim();
    
    // Skip metric rows, year rows, and date rows
    if (isMetricName(cellValue) || isYearOrDate(cellValue)) {
      continue;
    }
    
    // Check for match
    if (cellValue === normalizedSenderName) {
      return rowIdx + 1; // 1-indexed
    }
    
    // Partial match (contains or is contained)
    if (cellValue.includes(normalizedSenderName) || normalizedSenderName.includes(cellValue)) {
      return rowIdx + 1;
    }
    
    // Match first and last name separately
    const senderParts = normalizedSenderName.split(' ');
    const cellParts = cellValue.split(' ');
    if (senderParts.length >= 2 && cellParts.length >= 2) {
      // Match first name and partial last name or vice versa
      if (senderParts[0] === cellParts[0] && 
          (cellParts[1].startsWith(senderParts[1].charAt(0)) || senderParts[1].startsWith(cellParts[1].charAt(0)))) {
        return rowIdx + 1;
      }
    }
  }
  
  return null;
}

/**
 * Check if a value is a metric name
 */
function isMetricName(value) {
  const metrics = [
    'connections sent', 'connections accepted', 'acceptance rate',
    'messages sent', 'message replies', 'reply rate',
    'open conversations', 'interested', 'leads not yet enrolled',
    'leads not enrolled', 'notes', 'connection sent', 'connection accepted'
  ];
  
  const normalizedValue = value.toLowerCase().trim();
  return metrics.some(m => normalizedValue === m || normalizedValue.startsWith(m));
}

/**
 * Check if a value is a year or date
 */
function isYearOrDate(value) {
  const strValue = String(value).trim();
  
  // Check for year (4 digits)
  if (/^\d{4}$/.test(strValue)) return true;
  
  // Check for M/D or MM/DD format
  if (/^\d{1,2}\/\d{1,2}$/.test(strValue)) return true;
  
  return false;
}

/**
 * Update sender data in the sheet
 */
function updateSenderData(sheet, senderRow, weeks) {
  const result = {
    weeks_updated: 0,
    cells_updated: 0
  };
  
  // Get header row (row 1) to find week columns
  const headerRange = sheet.getRange(1, 1, 1, sheet.getLastColumn());
  const headerValues = headerRange.getValues()[0];
  
  // Define metrics and their row offsets from sender row
  const metrics = [
    { name: 'connections_sent', offset: 1 },
    { name: 'connections_accepted', offset: 2 },
    { name: 'acceptance_rate', offset: 3, isPercentage: true },
    { name: 'messages_sent', offset: 4 },
    { name: 'message_replies', offset: 5 },
    { name: 'reply_rate', offset: 6, isPercentage: true },
    { name: 'open_conversations', offset: 7 },
    { name: 'interested', offset: 8 }
  ];
  
  // Process each week
  for (const week of weeks) {
    // Get the week date - use week_end (Friday) which matches your column headers
    const weekDate = week.week_end || week.week_start;
    if (!weekDate) continue;
    
    // Format as M/D to match column headers
    const weekKey = formatWeekDate(weekDate);
    if (!weekKey) continue;
    
    // Find the column for this week
    let weekCol = findWeekColumn(headerValues, weekKey);
    
    if (!weekCol) {
      // Week column not found - optionally create it
      // For now, skip if not found
      continue;
    }
    
    result.weeks_updated++;
    
    // Update each metric for this week
    for (const metric of metrics) {
      const metricRow = senderRow + metric.offset;
      const cellRange = sheet.getRange(metricRow, weekCol);
      const currentValue = cellRange.getValue();
      
      // Only update if cell is empty
      if (currentValue === '' || currentValue === null || currentValue === undefined) {
        let value = week[metric.name];
        
        if (value === undefined || value === null) {
          value = 0;
        }
        
        if (metric.isPercentage) {
          // Format as percentage string
          if (typeof value === 'number') {
            value = value.toFixed(2) + '%';
          } else if (!String(value).includes('%')) {
            value = String(value) + '%';
          }
        }
        
        cellRange.setValue(value);
        result.cells_updated++;
      }
    }
  }
  
  return result;
}

/**
 * Find column for a week date
 */
function findWeekColumn(headerValues, weekKey) {
  // weekKey is in M/D format (e.g., "11/21")
  for (let colIdx = 1; colIdx < headerValues.length; colIdx++) {
    const headerValue = headerValues[colIdx];
    if (!headerValue) continue;
    
    const headerStr = String(headerValue).trim();
    
    // Direct match
    if (headerStr === weekKey) {
      return colIdx + 1; // 1-indexed
    }
    
    // Try to parse and compare dates
    const headerParts = headerStr.split('/');
    const weekParts = weekKey.split('/');
    
    if (headerParts.length === 2 && weekParts.length === 2) {
      const headerMonth = parseInt(headerParts[0], 10);
      const headerDay = parseInt(headerParts[1], 10);
      const weekMonth = parseInt(weekParts[0], 10);
      const weekDay = parseInt(weekParts[1], 10);
      
      if (headerMonth === weekMonth && headerDay === weekDay) {
        return colIdx + 1;
      }
    }
  }
  
  return null;
}

/**
 * Format date as M/D (e.g., "11/21" for November 21)
 */
function formatWeekDate(dateString) {
  if (!dateString) return null;
  
  try {
    // Handle YYYY-MM-DD format
    if (dateString.includes('-')) {
      const parts = dateString.split('-');
      if (parts.length >= 3) {
        const month = parseInt(parts[1], 10);
        const day = parseInt(parts[2], 10);
        return month + '/' + day;
      }
    }
    
    // Handle Date object or other formats
    const date = new Date(dateString);
    if (!isNaN(date.getTime())) {
      const month = date.getMonth() + 1;
      const day = date.getDate();
      return month + '/' + day;
    }
    
    return null;
  } catch (e) {
    return null;
  }
}

/**
 * Test function - run this to test with sample data
 */
function testScript() {
  const testData = {
    date_range: {
      start: '2025-11-15',
      end: '2025-11-21'
    },
    client_groups: {
      'AMPLIS': {
        sender_ids: [50083, 50084, 85934]
      },
      'PAC': {
        sender_ids: [95519, 95684, 95994, 116050]
      }
    },
    senders: [
      {
        name: 'Corinne Kazoleas',
        sender_id: 50083,
        weeks: [
          {
            week_start: '2025-11-15',
            week_end: '2025-11-21',
            connections_sent: 176,
            connections_accepted: 49,
            acceptance_rate: 27.84,
            messages_sent: 46,
            message_replies: 16,
            reply_rate: 34.78,
            open_conversations: 8,
            interested: 2
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

/**
 * Utility: List all sheets and senders found (run manually to debug)
 */
function listSheetsAndSenders() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const sheets = spreadsheet.getSheets();
  
  const report = [];
  
  for (const sheet of sheets) {
    const sheetName = sheet.getName();
    const dataRange = sheet.getDataRange();
    const values = dataRange.getValues();
    
    const senders = [];
    for (let rowIdx = 0; rowIdx < values.length; rowIdx++) {
      const firstCell = values[rowIdx][0];
      if (!firstCell) continue;
      
      const cellValue = String(firstCell).trim();
      if (cellValue && !isMetricName(cellValue.toLowerCase()) && !isYearOrDate(cellValue)) {
        // Check if next row is a metric (to confirm this is a sender)
        if (rowIdx + 1 < values.length) {
          const nextCell = values[rowIdx + 1][0];
          if (nextCell && isMetricName(String(nextCell).toLowerCase())) {
            senders.push({
              name: cellValue,
              row: rowIdx + 1
            });
          }
        }
      }
    }
    
    report.push({
      sheet: sheetName,
      senders: senders
    });
  }
  
  Logger.log(JSON.stringify(report, null, 2));
  return report;
}
