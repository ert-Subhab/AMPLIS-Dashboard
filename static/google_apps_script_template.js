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
      found_skipped: [],
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
      
      // Skip only if no sender name (but allow empty weeks - we'll handle that later)
      if (!senderName) continue;
      
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
        if (batchResult.found_skipped) {
          results.found_skipped.push(...batchResult.found_skipped);
        }
        results.not_found.push(...batchResult.not_found);
        results.columns_created.push(...batchResult.columns_created);
      } catch (err) {
        results.errors.push({ sheet: sheetName, error: err.toString() });
      }
    }
    
    // Build detailed message
    const processedCount = results.processed.length;
    const skippedCount = (results.found_skipped || []).length;
    const notFoundCount = results.not_found.length;
    const columnsCount = results.columns_created.length;
    
    let message = `Processed ${processedCount} senders`;
    if (skippedCount > 0) {
      message += `, ${skippedCount} found but skipped (already filled)`;
    }
    if (notFoundCount > 0) {
      message += `, ${notFoundCount} not found`;
    }
    if (columnsCount > 0) {
      message += `, ${columnsCount} new columns created`;
    }
    
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      message: message,
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
  const result = { 
    processed: [],      // Found and updated (cells written)
    found_skipped: [],  // Found but all cells already filled
    not_found: [],      // Not found in sheet
    columns_created: [] 
  };
  
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
  let weekColumns = {};
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
  
  // Find the actual last column in the sheet (not just week columns)
  // This ensures we append new columns at the end, not at the start
  let actualLastCol = numCols - 1; // 0-indexed, so numCols - 1 is the last column index
  
  // If we found week columns, use the last week column position
  // Otherwise, we'll append after the last column in the sheet
  if (lastWeekCol > 0) {
    actualLastCol = lastWeekCol; // Use last week column as insertion point
  }
  
  // Collect all unique week dates from all senders
  const allWeekDates = new Set();
  for (const sender of senders) {
    for (const week of sender.weeks) {
      const weekDate = week.week_end || week.week_start;
      if (weekDate) {
        const weekKey = formatWeekKey(weekDate);
        if (weekKey) {
          allWeekDates.add(weekKey);
          // Log first few weeks for debugging
          if (allWeekDates.size <= 3) {
            Logger.log(`Week data: week_start=${week.week_start}, week_end=${week.week_end}, formatted=${weekKey}`);
          }
        }
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
  
  // Track columns we need to create
  const columnsToCreate = [];
  for (const weekKey of sortedWeekDates) {
    if (!weekColumns[weekKey]) {
      columnsToCreate.push(weekKey);
    }
  }
  
  // Create all missing columns at the end
  for (const weekKey of columnsToCreate) {
    // Insert a new column at the END (after the last column in the sheet)
    // actualLastCol is 0-indexed, insertColumnAfter needs 1-indexed
    const insertAfterCol = actualLastCol + 1;
    sheet.insertColumnAfter(insertAfterCol);
    actualLastCol++; // New column is now at actualLastCol (0-indexed)
    const newColIndex = actualLastCol + 1; // 1-indexed for setValue
    sheet.getRange(headerRowIndex + 1, newColIndex).setValue(weekKey);
    weekColumns[weekKey] = actualLastCol; // Store as 0-indexed for array access
    // Also store normalized version
    const parts = weekKey.split('/');
    const normalized = parseInt(parts[0]) + '/' + parseInt(parts[1]);
    weekColumns[normalized] = actualLastCol;
    result.columns_created.push({ sheet: sheet.getName(), column: weekKey, position: newColIndex });
  }
  
  // Refresh data if we added columns and rebuild weekColumns map
  if (result.columns_created.length > 0) {
    SpreadsheetApp.flush();
    allValues = sheet.getDataRange().getValues();
    numCols = allValues[0] ? allValues[0].length : 0;
    headerRow = allValues[headerRowIndex];
    
    // Rebuild weekColumns map with updated column positions
    weekColumns = {};
    for (let col = 1; col < numCols; col++) {
      const headerVal = headerRow[col];
      if (headerVal) {
        const headerStr = String(headerVal).trim();
        if (/^\d{1,2}\/\d{1,2}$/.test(headerStr)) {
          weekColumns[headerStr] = col;
          // Also store normalized version
          const parts = headerStr.split('/');
          const normalized = parseInt(parts[0]) + '/' + parseInt(parts[1]);
          weekColumns[normalized] = col;
        }
      }
    }
    
    // Update actualLastCol to reflect the new last column position
    actualLastCol = numCols - 1; // 0-indexed, so numCols - 1 is the last column
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
    
    // Sender was found - track updates
    let cellsUpdated = 0;
    let cellsSkipped = 0;
    let weeksProcessed = 0;
    
    for (const week of sender.weeks) {
      const weekDate = week.week_end || week.week_start;
      if (!weekDate) continue;
      
      const weekKey = formatWeekKey(weekDate);
      if (!weekKey) {
        continue; // Couldn't format the date
      }
      
      // Try to find column - check both exact and normalized versions
      let col = weekColumns[weekKey];
      
      if (col === undefined || col === null) {
        // Try normalized version
        const parts = weekKey.split('/');
        const normalized = parseInt(parts[0]) + '/' + parseInt(parts[1]);
        col = weekColumns[normalized];
      }
      
      // If still not found, try to find closest date within 3 days (handles week boundary issues)
      if (col === undefined || col === null) {
        const [targetMonth, targetDay] = weekKey.split('/').map(Number);
        let closestCol = null;
        let closestDiff = Infinity;
        
        for (const [headerStr, headerCol] of Object.entries(weekColumns)) {
          if (typeof headerCol === 'number') {
            const [headerMonth, headerDay] = headerStr.split('/').map(Number);
            // Check if same month and within 3 days
            if (headerMonth === targetMonth) {
              const diff = Math.abs(headerDay - targetDay);
              if (diff <= 3 && diff < closestDiff) {
                closestDiff = diff;
                closestCol = headerCol;
              }
            }
          }
        }
        
        if (closestCol !== null) {
          col = closestCol;
          Logger.log(`Matched week ${weekKey} to existing column (closest match within 3 days)`);
        }
      }
      
      // If column still not found, create it at the end
      if (col === undefined || col === null) {
        // Log that we're creating a new column
        Logger.log(`Creating new column for week ${weekKey} at the end of the sheet`);
        
        // Get current last column (refresh data to get accurate count)
        const currentDataRange = sheet.getDataRange();
        const currentNumCols = currentDataRange.getNumColumns();
        const currentLastCol = currentNumCols - 1; // 0-indexed
        
        // Insert new column at the end
        const insertAfterCol = currentLastCol + 1; // 1-indexed for insertColumnAfter
        sheet.insertColumnAfter(insertAfterCol);
        
        // Update actualLastCol to reflect the new column
        actualLastCol = currentLastCol + 1; // New column is now at this position (0-indexed)
        const newColIndex = actualLastCol + 1; // 1-indexed for setValue
        
        // Set the header
        sheet.getRange(headerRowIndex + 1, newColIndex).setValue(weekKey);
        
        // Add to weekColumns map
        col = actualLastCol; // Store as 0-indexed for array access
        weekColumns[weekKey] = col;
        
        // Also store normalized version
        const parts = weekKey.split('/');
        const normalized = parseInt(parts[0]) + '/' + parseInt(parts[1]);
        weekColumns[normalized] = col;
        
        // Track that we created this column
        result.columns_created.push({ sheet: sheet.getName(), column: weekKey, position: newColIndex });
        
        // Refresh data to ensure we have accurate column count
        SpreadsheetApp.flush();
        allValues = sheet.getDataRange().getValues();
        numCols = allValues[0] ? allValues[0].length : 0;
      }
      
      let weekHadUpdates = false;
      
      for (const metric of metrics) {
        const row = senderRow + metric.offset;
        
        // Always update the cell (user wants to update even if column already exists)
        // Check current value for reporting purposes
        const currentVal = (row - 1 < allValues.length && col < allValues[row - 1].length) 
          ? allValues[row - 1][col] 
          : '';
        
        const wasEmpty = (currentVal === '' || currentVal === null || currentVal === undefined);
        
        let value = week[metric.key];
        if (value === undefined || value === null) value = 0;
        
        if (metric.isPercent) {
          value = (typeof value === 'number') ? value.toFixed(2) + '%' : String(value) + '%';
        }
        
        // Always write the value (update existing or write new)
        sheet.getRange(row, col + 1).setValue(value);
        
        // Count as updated regardless of whether it was empty or not
        // (user wants to update even if column already exists)
        cellsUpdated++;
        weekHadUpdates = true;
      }
      
      if (weekHadUpdates) {
        weeksProcessed++;
      }
    }
    
    // Report based on what happened
    if (cellsUpdated > 0) {
      // Successfully updated (we always update now, even if cells were filled)
      result.processed.push({ 
        sender: sender.name, 
        sheet: sheet.getName(), 
        row: senderRow,
        cells_updated: cellsUpdated,
        weeks_processed: weeksProcessed
      });
    } else if (sender.weeks.length === 0) {
      // Found sender but no weeks data
      result.found_skipped.push({ 
        sender: sender.name, 
        sheet: sheet.getName(), 
        row: senderRow,
        reason: 'No week data provided'
      });
    } else {
      // Found sender but no matching week columns (all week dates didn't match)
      // Collect the week keys that were checked for better error reporting
      const checkedWeeks = [];
      for (const week of sender.weeks) {
        const weekDate = week.week_end || week.week_start;
        if (weekDate) {
          const weekKey = formatWeekKey(weekDate);
          if (weekKey) checkedWeeks.push(weekKey);
        }
      }
      result.found_skipped.push({ 
        sender: sender.name, 
        sheet: sheet.getName(), 
        row: senderRow,
        reason: 'No matching week columns found',
        weeks_checked: sender.weeks.length,
        week_keys: checkedWeeks,
        available_columns: Object.keys(weekColumns).filter(k => typeof weekColumns[k] === 'number').slice(0, 10) // First 10 for brevity
      });
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
  
  // Split name into parts for better matching
  const nameParts = normalized.split(/\s+/).filter(p => p.length > 0);
  const firstName = nameParts[0] || '';
  const lastName = nameParts[nameParts.length - 1] || '';
  
  for (let row = 0; row < allValues.length; row++) {
    const cell = allValues[row][0];
    if (!cell) continue;
    
    const cellVal = String(cell).toLowerCase().trim();
    
    // Skip metrics and dates
    if (isMetric(cellVal) || isDate(cellVal)) continue;
    
    // Exact match (case-insensitive)
    if (cellVal === normalized) return row + 1;
    
    // Normalize both for comparison (remove extra spaces, punctuation)
    const normalizedCell = cellVal.replace(/[.,]/g, '').replace(/\s+/g, ' ').trim();
    const normalizedSender = normalized.replace(/[.,]/g, '').replace(/\s+/g, ' ').trim();
    
    if (normalizedCell === normalizedSender) return row + 1;
    
    // Partial match (one contains the other)
    if (normalizedCell.includes(normalizedSender) || normalizedSender.includes(normalizedCell)) {
      return row + 1;
    }
    
    // First and last name match (handles middle names/initials)
    const cellParts = normalizedCell.split(/\s+/).filter(p => p.length > 0);
    if (cellParts.length >= 2 && nameParts.length >= 2) {
      const cellFirst = cellParts[0];
      const cellLast = cellParts[cellParts.length - 1];
      
      // Match if first and last names match (ignoring middle names/initials)
      if (firstName && lastName && cellFirst === firstName && cellLast === lastName) {
        return row + 1;
      }
      
      // Match if first name matches and last name is similar (fuzzy)
      if (firstName && cellFirst === firstName) {
        // Check if last names are similar (one contains the other or vice versa)
        if (cellLast.includes(lastName) || lastName.includes(cellLast)) {
          return row + 1;
        }
      }
    }
    
    // First name only match (if first name is substantial, >= 4 chars)
    if (firstName.length >= 4) {
      const cellFirst = cellParts[0] || '';
      if (cellFirst === firstName && cellFirst.length >= 4) {
        return row + 1;
      }
    }
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
