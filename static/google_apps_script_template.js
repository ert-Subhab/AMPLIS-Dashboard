/**
 * Google Apps Script Template for HeyReach Data Integration
 * 
 * This script populates Google Sheets with HeyReach data in the CSV format:
 * - Row 1: Year in column A, week dates (M/D format) in columns B+
 * - Row 2: Sender name in column A
 * - Row 3+: Metric names in column A, with data values in columns B+ (weeks)
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
    const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
    const allSheets = spreadsheet.getSheets();
    
    const results = {
      success: true,
      processed_sheets: [],
      errors: []
    };
    
    // Process each sender
    data.senders.forEach(sender => {
      const senderName = sender.name;
      const senderId = sender.sender_id;
      const weeks = sender.weeks || [];
      
      if (weeks.length === 0) {
        results.errors.push(`Sender "${senderName}" has no week data to process`);
        return; // Skip senders with no data
      }
      
      // Search all sheets for this sender
      let senderFound = false;
      
      for (let sheetIdx = 0; sheetIdx < allSheets.length; sheetIdx++) {
        const sheet = allSheets[sheetIdx];
        const sheetName = sheet.getName();
        
        try {
          // Find sender in this sheet
          const senderInfo = findSenderInSheet(sheet, senderName, senderId, data.sender_id_mapping);
          
          if (senderInfo) {
            senderFound = true;
            
            try {
              // Populate data for this sender
              const updateResult = populateSenderData(sheet, senderInfo, weeks, data.date_range);
              
              results.processed_sheets.push({
                sheet: sheetName,
                sender: senderName,
                sender_id: senderId,
                found_by: senderInfo.found_by,
                weeks_updated: updateResult.weeks_updated,
                cells_updated: updateResult.cells_updated
              });
            } catch (error) {
              results.errors.push(`Error populating data for ${senderName} (ID: ${senderId}) in sheet "${sheetName}": ${error.toString()}`);
            }
          }
        } catch (error) {
          results.errors.push(`Error searching for ${senderName} in sheet "${sheetName}": ${error.toString()}`);
        }
      }
      
      if (!senderFound) {
        results.errors.push(`Sender "${senderName}" (ID: ${senderId}) not found in any sheet. Make sure the sender name matches exactly (case-insensitive) in column A of one of the sheets.`);
      }
    });
    
    // Return success response
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      message: `Processed ${data.senders.length} senders across ${results.processed_sheets.length} sheet(s)`,
      results: results
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    // Return error response
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      error: error.toString(),
      stack: error.stack
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

/**
 * Find sender in a sheet by name or ID
 */
function findSenderInSheet(sheet, senderName, senderId, senderIdMapping) {
  const allValues = sheet.getDataRange().getValues();
  
  if (!allValues || allValues.length === 0) {
    return null;
  }
  
  // Normalize the incoming sender name for comparison
  const normalizedSenderName = senderName.toLowerCase().trim();
  
  // Search for sender name in column A (row 2 and below, since row 1 is header)
  for (let rowIdx = 1; rowIdx < allValues.length; rowIdx++) {
    const row = allValues[rowIdx];
    const firstCell = row[0] ? String(row[0]).trim() : '';
    
    if (!firstCell) continue;
    
    // Check if it's a sender name (not a metric, not a date, not empty)
    if (isSenderName(firstCell, allValues, rowIdx)) {
      const normalizedCellValue = firstCell.toLowerCase().trim();
      
      // Try exact match first (case-insensitive)
      if (normalizedCellValue === normalizedSenderName) {
        return {
          row: rowIdx + 1, // 1-indexed
          name: firstCell,
          found_by: 'exact_name'
        };
      }
      
      // Try partial match (either direction)
      if (normalizedCellValue.includes(normalizedSenderName) || 
          normalizedSenderName.includes(normalizedCellValue)) {
        return {
          row: rowIdx + 1,
          name: firstCell,
          found_by: 'partial_name'
        };
      }
      
      // Try matching by sender ID if we have it
      if (senderId && senderIdMapping) {
        // Check if this name corresponds to the sender ID
        // senderIdMapping maps: { "Sender Name": senderId }
        for (const [mappedName, mappedId] of Object.entries(senderIdMapping)) {
          const normalizedMappedName = mappedName.toLowerCase().trim();
          
          // Check if the mapped ID matches our sender ID
          if (mappedId == senderId) { // Use == for type coercion (string vs number)
            // Check if the cell value matches the mapped name
            if (normalizedCellValue === normalizedMappedName ||
                normalizedCellValue.includes(normalizedMappedName) ||
                normalizedMappedName.includes(normalizedCellValue)) {
              return {
                row: rowIdx + 1,
                name: firstCell,
                found_by: 'id_mapping'
              };
            }
          }
        }
      }
    }
  }
  
  return null;
}

/**
 * Check if a cell value is a sender name (not a metric, date, etc.)
 */
function isSenderName(cellValue, allValues, rowIdx) {
  const value = String(cellValue).toLowerCase().trim();
  
  // Skip if it's empty or just whitespace
  if (!value || value.length === 0) {
    return false;
  }
  
  // Skip if it's a year (4 digits)
  if (/^\d{4}$/.test(value)) {
    return false;
  }
  
  // Skip if it's a date (M/D format)
  if (/^\d{1,2}\/\d{1,2}$/.test(value)) {
    return false;
  }
  
  // Skip if it's a metric name (exact or partial match)
  const metricNames = [
    'connections sent', 'connections accepted', 'acceptance rate',
    'messages sent', 'message replies', 'reply rate',
    'open conversations', 'interested', 'leads not yet enrolled',
    'leads not enrolled', 'notes'
  ];
  
  for (const metric of metricNames) {
    if (value === metric || value.startsWith(metric) || metric.startsWith(value)) {
      return false;
    }
  }
  
  // Check the next row to see if it contains a metric name
  // This helps identify sender names (they're followed by metrics)
  if (rowIdx + 1 < allValues.length) {
    const nextRow = allValues[rowIdx + 1];
    const nextCell = nextRow && nextRow[0] ? String(nextRow[0]).toLowerCase().trim() : '';
    
    // If the next row starts with a metric, this is likely a sender name
    for (const metric of metricNames) {
      if (nextCell === metric || nextCell.startsWith(metric)) {
        return true; // This is likely a sender name
      }
    }
  }
  
  // If it has letters and is not a metric, it's likely a sender name
  // But be more strict: sender names typically don't contain special characters like %, /, etc.
  if (/[a-zA-Z]/.test(value) && !/[%\/]/.test(value)) {
    // Additional check: if the row below is empty or contains metrics, this is likely a sender
    if (rowIdx + 1 < allValues.length) {
      const nextRow = allValues[rowIdx + 1];
      const nextCell = nextRow && nextRow[0] ? String(nextRow[0]).toLowerCase().trim() : '';
      if (!nextCell || nextCell === '' || metricNames.some(m => nextCell.includes(m))) {
        return true;
      }
    } else {
      // Last row, but has letters - could be a sender
      return true;
    }
  }
  
  return false;
}

/**
 * Populate sender data in the sheet
 */
function populateSenderData(sheet, senderInfo, weeks, dateRange) {
  const allValues = sheet.getDataRange().getValues();
  const senderRow = senderInfo.row; // 1-indexed
  const result = {
    weeks_updated: 0,
    cells_updated: 0
  };
  
  // Get or create header row (row 1)
  let headerRow = allValues[0] || [];
  
  // Ensure year is in column A (only if empty)
  const yearCell = headerRow[0] ? String(headerRow[0]).trim() : '';
  if (!yearCell || yearCell === '') {
    // Try to get year from the first week's date, otherwise use current year
    let year = new Date().getFullYear();
    if (weeks.length > 0 && weeks[0].week_end) {
      try {
        const weekDate = new Date(weeks[0].week_end);
        if (!isNaN(weekDate.getTime())) {
          year = weekDate.getFullYear();
        }
      } catch (e) {
        // Use current year if parsing fails
      }
    }
    sheet.getRange(1, 1).setValue(year);
    headerRow[0] = year;
  }
  
  // Find or create week columns
  const weekColumns = findOrCreateWeekColumns(sheet, headerRow, weeks);
  
  // Define metrics in order (as they appear in CSV)
  const metrics = [
    { name: 'Connections Sent', key: 'connections_sent', rowOffset: 1 },
    { name: 'Connections Accepted', key: 'connections_accepted', rowOffset: 2 },
    { name: 'Acceptance Rate', key: 'acceptance_rate', rowOffset: 3, isPercentage: true },
    { name: 'Messages Sent', key: 'messages_sent', rowOffset: 4 },
    { name: 'Message Replies', key: 'message_replies', rowOffset: 5 },
    { name: 'Reply Rate', key: 'reply_rate', rowOffset: 6, isPercentage: true },
    { name: 'Open Conversations', key: 'open_conversations', rowOffset: 7 },
    { name: 'Interested', key: 'interested', rowOffset: 8 }
  ];
  
  // Ensure metric rows exist and are labeled in the correct order
  // Metrics should appear in fixed order right after the sender name (matching CSV format)
  const metricStartRow = senderRow + 1; // Row after sender name
  
  for (let i = 0; i < metrics.length; i++) {
    const metric = metrics[i];
    const metricRow = metricStartRow + i;
    
    // Get current value in column A for this row
    const currentMetricName = allValues[metricRow - 1] ? 
      (allValues[metricRow - 1][0] ? String(allValues[metricRow - 1][0]).trim() : '') : '';
    
    // Only set metric name if it's empty or doesn't match
    // This preserves existing metric names if they're already correct
    if (!currentMetricName || currentMetricName.toLowerCase() !== metric.name.toLowerCase()) {
      sheet.getRange(metricRow, 1).setValue(metric.name);
    }
    
    // Populate data for each week
    for (const week of weeks) {
      const weekKey = formatWeekDate(week.week_end || week.week_start);
      const weekCol = weekColumns[weekKey];
      
      if (!weekCol) continue;
      
      // Get current value from the sheet (refresh to get latest)
      const cellRange = sheet.getRange(metricRow, weekCol);
      const cellValue = cellRange.getValue();
      const currentValue = cellValue !== null && cellValue !== undefined ? String(cellValue).trim() : '';
      
      // Only update if cell is empty or contains only whitespace
      // Note: We don't update if it's '0' because 0 is a valid value
      if (!currentValue || currentValue === '') {
        let valueToWrite = week[metric.key];
        
        // Handle undefined/null values
        if (valueToWrite === undefined || valueToWrite === null) {
          valueToWrite = 0;
        }
        
        if (metric.isPercentage) {
          // Format percentage: if it's already a number, add %, otherwise use as-is
          if (typeof valueToWrite === 'number') {
            valueToWrite = valueToWrite.toFixed(2) + '%';
          } else {
            valueToWrite = String(valueToWrite);
            if (!valueToWrite.endsWith('%')) {
              valueToWrite = valueToWrite + '%';
            }
          }
        } else {
          // For non-percentage values, ensure it's a number
          valueToWrite = Number(valueToWrite) || 0;
        }
        
        sheet.getRange(metricRow, weekCol).setValue(valueToWrite);
        result.cells_updated++;
      }
    }
  }
  
  result.weeks_updated = Object.keys(weekColumns).length;
  return result;
}

/**
 * Find or create week columns in the header row
 */
function findOrCreateWeekColumns(sheet, headerRow, weeks) {
  const weekColumns = {};
  let lastWeekCol = 1; // Start from column B (index 1, which is column 2)
  
  // Find the last existing week column (M/D format)
  for (let colIdx = 1; colIdx < headerRow.length; colIdx++) {
    const cellValue = headerRow[colIdx] ? String(headerRow[colIdx]).trim() : '';
    if (/^\d{1,2}\/\d{1,2}$/.test(cellValue)) {
      lastWeekCol = colIdx + 1; // 1-indexed column number (keep updating to find the LAST one)
    }
  }
  
  // If no week columns found, start from column B
  if (lastWeekCol === 1) {
    lastWeekCol = 2; // Column B
  } else {
    // lastWeekCol already points to the last week column, so new columns start after it
    // No need to increment here, we'll increment when creating new columns
  }

  // Process each week (use week_end which is Friday, not week_start)
  for (const week of weeks) {
    const weekKey = formatWeekDate(week.week_end || week.week_start);
    
    if (!weekKey) continue; // Skip if week key is invalid
    
    // Check if week column already exists
    let foundCol = null;
    for (let colIdx = 1; colIdx < headerRow.length; colIdx++) {
      const cellValue = headerRow[colIdx] ? String(headerRow[colIdx]).trim() : '';
      if (cellValue === weekKey) {
        foundCol = colIdx + 1; // 1-indexed
        break;
      }
    }
    
    if (foundCol) {
      weekColumns[weekKey] = foundCol;
    } else {
      // Create new week column after the last existing week column
      lastWeekCol++;
      sheet.getRange(1, lastWeekCol).setValue(weekKey);
      weekColumns[weekKey] = lastWeekCol;
      // Update headerRow array for next iteration
      if (headerRow.length < lastWeekCol) {
        // Extend array if needed
        while (headerRow.length < lastWeekCol) {
          headerRow.push('');
        }
      }
      headerRow[lastWeekCol - 1] = weekKey; // Update in-memory array (0-indexed)
    }
  }
  
  return weekColumns;
}

/**
 * Format week date as M/D (e.g., "11/21" for November 21)
 */
function formatWeekDate(dateString) {
  if (!dateString) return '';
  
  try {
    const date = new Date(dateString);
    const month = date.getMonth() + 1; // 0-indexed to 1-indexed
    const day = date.getDate();
    return month + '/' + day;
  } catch (e) {
    // Try parsing as YYYY-MM-DD
    const parts = dateString.split('-');
    if (parts.length === 3) {
      const month = parseInt(parts[1], 10);
      const day = parseInt(parts[2], 10);
      return month + '/' + day;
    }
    return dateString;
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
    sender_id_mapping: {
      'Corinne K': 50083,
      'Tyler M': 50084
    },
    senders: [
      {
        name: 'Corinne K',
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
            open_conversations: 46,
            interested: 0,
            leads_not_enrolled: 0
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
