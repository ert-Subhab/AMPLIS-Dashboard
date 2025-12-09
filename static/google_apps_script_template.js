/**
 * Google Apps Script for HeyReach Data Integration
 * AUTO-CREATES new date columns if they don't exist
 */

function doPost(e) {
  try {
    let data;
    try {
      data = JSON.parse(e.postData.contents);
    } catch (parseError) {
      return ContentService.createTextOutput(JSON.stringify({
        success: false,
        error: 'Failed to parse JSON: ' + parseError.toString()
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const allSheets = spreadsheet.getSheets();
    
    const results = {
      processed: [],
      not_found: [],
      columns_created: [],
      errors: []
    };
    
    // Build client groups mapping
    const clientGroups = data.client_groups || {};
    const senderToClient = {};
    for (const [clientName, clientData] of Object.entries(clientGroups)) {
      const senderIds = clientData.sender_ids || [];
      for (const senderId of senderIds) {
        senderToClient[senderId] = clientName;
      }
    }
    
    if (!data.senders || !Array.isArray(data.senders)) {
      return ContentService.createTextOutput(JSON.stringify({
        success: false,
        error: 'No senders array'
      })).setMimeType(ContentService.MimeType.JSON);
    }
    
    // Group senders by sheet for batch processing
    const sendersBySheet = {};
    
    for (const sender of data.senders) {
      const senderName = sender.name;
      const senderId = sender.sender_id;
      const weeks = sender.weeks || [];
      
      if (!senderName || weeks.length === 0) continue;
      
      // Find client/sheet for this sender
      let clientName = senderToClient[senderId];
      
      if (!clientName) {
        // Try to find sheet containing this sender
        for (const sheet of allSheets) {
          if (findSenderRow(sheet, senderName)) {
            clientName = sheet.getName();
            break;
          }
        }
      }
      
      if (!clientName) {
        results.not_found.push({ sender: senderName, reason: 'No client found' });
        continue;
      }
      
      // Find the actual sheet
      const sheet = findSheet(spreadsheet, clientName);
      if (!sheet) {
        results.not_found.push({ sender: senderName, client: clientName, reason: 'Sheet not found' });
        continue;
      }
      
      const sheetName = sheet.getName();
      if (!sendersBySheet[sheetName]) {
        sendersBySheet[sheetName] = { sheet: sheet, senders: [] };
      }
      sendersBySheet[sheetName].senders.push({ name: senderName, id: senderId, weeks: weeks });
    }
    
    // Process each sheet with batch updates
    for (const [sheetName, sheetData] of Object.entries(sendersBySheet)) {
      try {
        const batchResult = processSheetBatch(sheetData.sheet, sheetData.senders);
        results.processed.push(...batchResult.processed);
        results.not_found.push(...batchResult.not_found);
        results.columns_created.push(...batchResult.columns_created);
      } catch (err) {
        results.errors.push({ sheet: sheetName, error: err.toString() });
      }
    }
    
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      message: `Processed ${results.processed.length} senders, ${results.not_found.length} not found, ${results.columns_created.length} new columns created`,
      results: results
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      error: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Process all senders for a sheet using batch updates
 * AUTO-CREATES new date columns if they don't exist
 */
function processSheetBatch(sheet, senders) {
  const result = { processed: [], not_found: [], columns_created: [] };
  
  // Get all data from sheet at once
  const dataRange = sheet.getDataRange();
  let allValues = dataRange.getValues();
  let numRows = allValues.length;
  let numCols = allValues[0] ? allValues[0].length : 0;
  
  if (numRows === 0) return result;
  
  // Find the header row that contains week columns (scan first 5 rows for MM/DD)
  let headerRowIndex = 0;
  let maxDates = 0;
  for (let r = 0; r < Math.min(5, numRows); r++) {
    let dateCount = 0;
    for (let c = 1; c < numCols; c++) {
      const cell = allValues[r][c];
      if (cell) {
        const cellStr = String(cell).trim();
        if (/^\d{1,2}\/\d{1,2}$/.test(cellStr)) {
          dateCount++;
        }
      }
    }
    if (dateCount > maxDates) {
      maxDates = dateCount;
      headerRowIndex = r;
    }
  }
  
  let headerRow = allValues[headerRowIndex];
  
  // Build week column map and find last week column
  const weekColumns = {};
  let lastWeekCol = 0;
  
  for (let col = 1; col < numCols; col++) {
    const headerVal = headerRow[col];
    if (headerVal) {
      const headerStr = String(headerVal).trim();
      // Check if it's a date format (M/D)
      if (/^\d{1,2}\/\d{1,2}$/.test(headerStr)) {
        lastWeekCol = col;
        weekColumns[headerStr] = col;
        // Also store normalized version
        const parts = headerStr.split('/');
        const normalized = parseInt(parts[0]) + '/' + parseInt(parts[1]);
        weekColumns[normalized] = col;
      }
    }
  }
  
  // If no week columns found, start after column A
  if (lastWeekCol === 0) {
    lastWeekCol = 0; // Will become 1 when we add first column
  }
  
  // Collect all unique week dates from all senders
  const allWeekDates = new Set();
  for (const sender of senders) {
    for (const week of sender.weeks) {
      const weekDate = week.week_end || week.week_start;
      if (weekDate) {
        const weekKey = formatWeekKey(weekDate);
        if (weekKey) allWeekDates.add(weekKey);
      }
    }
  }
  
  // Create columns for any missing week dates
  const sortedWeekDates = Array.from(allWeekDates).sort((a, b) => {
    const [aMonth, aDay] = a.split('/').map(Number);
    const [bMonth, bDay] = b.split('/').map(Number);
    if (aMonth !== bMonth) return aMonth - bMonth;
    return aDay - bDay;
  });
  
  for (const weekKey of sortedWeekDates) {
    if (!weekColumns[weekKey]) {
      // Need to create this column
      // Insert a new column after the current last week column
      sheet.insertColumnAfter(lastWeekCol + 1);
      lastWeekCol++;
      sheet.getRange(headerRowIndex + 1, lastWeekCol + 1).setValue(weekKey);
      weekColumns[weekKey] = lastWeekCol;
      result.columns_created.push({ sheet: sheet.getName(), column: weekKey, position: lastWeekCol + 1 });
    }
  }
  
  // Refresh data if we added columns
  if (result.columns_created.length > 0) {
    SpreadsheetApp.flush();
    allValues = sheet.getDataRange().getValues();
    numCols = allValues[0] ? allValues[0].length : 0;
  }
  
  // Metrics offsets from sender row
  const metrics = [
    { key: 'connections_sent', offset: 1 },
    { key: 'connections_accepted', offset: 2 },
    { key: 'acceptance_rate', offset: 3, isPercent: true },
    { key: 'messages_sent', offset: 4 },
    { key: 'message_replies', offset: 5 },
    { key: 'reply_rate', offset: 6, isPercent: true },
    { key: 'open_conversations', offset: 7 },
    { key: 'interested', offset: 8 }
  ];
  
  // Process each sender
  for (const sender of senders) {
    const senderRow = findSenderRowInData(allValues, sender.name);
    
    if (!senderRow) {
      result.not_found.push({ sender: sender.name, sheet: sheet.getName(), reason: 'Sender not found in sheet' });
      continue;
    }
    
    let cellsUpdated = 0;
    
    for (const week of sender.weeks) {
      const weekDate = week.week_end || week.week_start;
      if (!weekDate) continue;
      
      const weekKey = formatWeekKey(weekDate);
      const col = weekColumns[weekKey];
      
      if (!col) continue;
      
      for (const metric of metrics) {
        const row = senderRow + metric.offset;
        
        // Check if cell is empty
        const currentVal = (row - 1 < allValues.length && col < allValues[row - 1].length) 
          ? allValues[row - 1][col] 
          : '';
        
        if (currentVal === '' || currentVal === null || currentVal === undefined) {
          let value = week[metric.key];
          if (value === undefined || value === null) value = 0;
          
          if (metric.isPercent) {
            value = (typeof value === 'number') ? value.toFixed(2) + '%' : String(value) + '%';
          }
          
          sheet.getRange(row, col + 1).setValue(value);
          cellsUpdated++;
        }
      }
    }
    
    if (cellsUpdated > 0) {
      result.processed.push({ sender: sender.name, sheet: sheet.getName(), cells: cellsUpdated });
    }
  }
  
  SpreadsheetApp.flush();
  return result;
}

/**
 * Find sender row in pre-loaded data
 */
function findSenderRowInData(allValues, senderName) {
  const normalized = senderName.toLowerCase().trim();
  
  for (let row = 0; row < allValues.length; row++) {
    const cell = allValues[row][0];
    if (!cell) continue;
    
    const cellVal = String(cell).toLowerCase().trim();
    
    // Skip metrics and dates
    if (isMetric(cellVal) || isDate(cellVal)) continue;
    
    // Exact match
    if (cellVal === normalized) return row + 1;
    
    // Partial match
    if (cellVal.includes(normalized) || normalized.includes(cellVal)) return row + 1;
    
    // First name match
    const senderFirst = normalized.split(' ')[0];
    const cellFirst = cellVal.split(' ')[0];
    if (senderFirst.length >= 3 && cellFirst.length >= 3 && senderFirst === cellFirst) return row + 1;
  }
  
  return null;
}

/**
 * Find sheet by name (case-insensitive, partial match)
 */
function findSheet(spreadsheet, clientName) {
  const normalized = clientName.toLowerCase().trim();
  
  // Exact match
  let sheet = spreadsheet.getSheetByName(clientName);
  if (sheet) return sheet;
  
  // Case-insensitive
  for (const s of spreadsheet.getSheets()) {
    if (s.getName().toLowerCase().trim() === normalized) return s;
  }
  
  // Partial match
  for (const s of spreadsheet.getSheets()) {
    const name = s.getName().toLowerCase().trim();
    if (name.includes(normalized) || normalized.includes(name)) return s;
  }
  
  return null;
}

/**
 * Find sender row (for initial sheet detection)
 */
function findSenderRow(sheet, senderName) {
  const values = sheet.getDataRange().getValues();
  return findSenderRowInData(values, senderName);
}

function isMetric(val) {
  const metrics = ['connections sent', 'connections accepted', 'acceptance rate', 
    'messages sent', 'message replies', 'reply rate', 'open conversations', 
    'interested', 'leads not', 'notes'];
  return metrics.some(m => val.startsWith(m));
}

function isDate(val) {
  return /^\d{4}$/.test(val) || /^\d{1,2}\/\d{1,2}$/.test(val);
}

function formatWeekKey(dateStr) {
  if (!dateStr) return null;
  if (dateStr.includes('-')) {
    const parts = dateStr.split('-');
    if (parts.length >= 3) {
      return parseInt(parts[1]) + '/' + parseInt(parts[2]);
    }
  }
  return null;
}

/**
 * Debug function - list all sheets and senders
 */
function listSheetsAndSenders() {
  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  const report = [];
  
  for (const sheet of spreadsheet.getSheets()) {
    const values = sheet.getDataRange().getValues();
    const senders = [];
    
    for (let row = 0; row < values.length; row++) {
      const cell = values[row][0];
      if (!cell) continue;
      
      const cellVal = String(cell).trim();
      if (cellVal && !isMetric(cellVal.toLowerCase()) && !isDate(cellVal)) {
        if (row + 1 < values.length) {
          const nextCell = values[row + 1][0];
          if (nextCell && isMetric(String(nextCell).toLowerCase())) {
            senders.push({ name: cellVal, row: row + 1 });
          }
        }
      }
    }
    
    report.push({ sheet: sheet.getName(), senders: senders });
  }
  
  Logger.log(JSON.stringify(report, null, 2));
  return report;
}
