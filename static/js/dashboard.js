// Dashboard JavaScript
let performanceChart = null;
let currentData = null;

// Initialize dashboard on load
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
});

// Initialize dashboard
async function initializeDashboard() {
    try {
        // Set default dates to last week (more reasonable default)
        const endDate = new Date();
        const startDate = new Date();
        // Set to last week (7 days ago to today)
        startDate.setDate(startDate.getDate() - 7);
        
        document.getElementById('startDate').value = formatDate(startDate);
        document.getElementById('endDate').value = formatDate(endDate);
        
        // Set up event listeners
        document.getElementById('connectBtn').addEventListener('click', initializeApiKey);
        document.getElementById('changeApiKeyBtn').addEventListener('click', changeApiKey);
        document.getElementById('toggleApiKeyBtn').addEventListener('click', toggleApiKeyVisibility);
        document.getElementById('applyFiltersBtn').addEventListener('click', loadPerformanceData);
        document.getElementById('refreshBtn').addEventListener('click', loadPerformanceData);
        
        // Google Sheets event listeners (only if elements exist)
        const populateBtn = document.getElementById('populateSheetsBtn');
        const connectGoogleBtn = document.getElementById('connectGoogleBtn');
        const disconnectGoogleBtn = document.getElementById('disconnectGoogleBtn');
        const saveOAuthBtn = document.getElementById('saveOAuthCredentialsBtn');
        const toggleOAuthSecretBtn = document.getElementById('toggleOAuthSecretBtn');
        
        // Export event listeners
        const exportCsvBtn = document.getElementById('exportCsvBtn');
        const toggleAppsScriptBtn = document.getElementById('toggleAppsScriptBtn');
        const sendToAppsScriptBtn = document.getElementById('sendToAppsScriptBtn');
        const showAppsScriptHelpBtn = document.getElementById('showAppsScriptHelpBtn');
        const copyScriptBtn = document.getElementById('copyScriptBtn');
        const openOAuthSectionBtn = document.getElementById('openOAuthSectionBtn');
        
        if (populateBtn) populateBtn.addEventListener('click', populateSheets);
        if (connectGoogleBtn) connectGoogleBtn.addEventListener('click', connectGoogleSheets);
        if (disconnectGoogleBtn) disconnectGoogleBtn.addEventListener('click', disconnectGoogleSheets);
        if (saveOAuthBtn) saveOAuthBtn.addEventListener('click', saveOAuthCredentials);
        if (toggleOAuthSecretBtn) toggleOAuthSecretBtn.addEventListener('click', toggleOAuthSecretVisibility);
        if (exportCsvBtn) exportCsvBtn.addEventListener('click', exportToCsv);
        if (toggleAppsScriptBtn) toggleAppsScriptBtn.addEventListener('click', toggleAppsScriptInput);
        if (sendToAppsScriptBtn) sendToAppsScriptBtn.addEventListener('click', sendToAppsScript);
        if (showAppsScriptHelpBtn) showAppsScriptHelpBtn.addEventListener('click', showAppsScriptHelp);
        if (copyScriptBtn) copyScriptBtn.addEventListener('click', copyAppsScriptTemplate);
        if (openOAuthSectionBtn) openOAuthSectionBtn.addEventListener('click', scrollToOAuthSection);
        
        // Supabase event listeners
        const toggleSupabaseBtn = document.getElementById('toggleSupabaseBtn');
        const saveSupabaseConfigBtn = document.getElementById('saveSupabaseConfigBtn');
        const testSupabaseConnectionBtn = document.getElementById('testSupabaseConnectionBtn');
        const evaluateMessagesBtn = document.getElementById('evaluateMessagesBtn');
        const getWeeklyStatsBtn = document.getElementById('getWeeklyStatsBtn');
        const toggleSupabaseKeyBtn = document.getElementById('toggleSupabaseKeyBtn');
        const toggleOpenAIKeyBtn = document.getElementById('toggleOpenAIKeyBtn');
        
        if (toggleSupabaseBtn) toggleSupabaseBtn.addEventListener('click', toggleSupabaseConfig);
        if (saveSupabaseConfigBtn) saveSupabaseConfigBtn.addEventListener('click', saveSupabaseConfig);
        if (testSupabaseConnectionBtn) testSupabaseConnectionBtn.addEventListener('click', testSupabaseConnection);
        if (evaluateMessagesBtn) evaluateMessagesBtn.addEventListener('click', evaluateMessages);
        if (getWeeklyStatsBtn) getWeeklyStatsBtn.addEventListener('click', getWeeklyStatsFromSupabase);
        if (toggleSupabaseKeyBtn) toggleSupabaseKeyBtn.addEventListener('click', () => togglePasswordVisibility('supabaseKeyInput', 'toggleSupabaseKeyBtn'));
        if (toggleOpenAIKeyBtn) toggleOpenAIKeyBtn.addEventListener('click', () => togglePasswordVisibility('openaiKeyInput', 'toggleOpenAIKeyBtn'));
        
        // Load saved Supabase config
        loadSupabaseConfig();
        
        // Check Google Sheets connection status on load
        checkGoogleSheetsStatus();
        
        // Check for OAuth callback success/error
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('google_connected') === '1') {
            showMessage('Google Sheets connected successfully!', 'success');
            checkGoogleSheetsStatus();
            // Clean URL
            window.history.replaceState({}, document.title, window.location.pathname);
        } else if (urlParams.get('google_error') === '1') {
            showError('Failed to connect Google Sheets. Please try again.');
            // Clean URL
            window.history.replaceState({}, document.title, window.location.pathname);
        }
        
        // Allow Enter key to submit API key
        document.getElementById('apiKeyInput').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                initializeApiKey();
            }
        });
        
        // Hide filters section initially
        document.getElementById('filtersSection').style.display = 'none';
        document.getElementById('apiKeyChangeSection').style.display = 'none';
    } catch (error) {
        showError('Error initializing dashboard: ' + error.message);
    }
}

// Initialize API key and load senders
async function initializeApiKey() {
    try {
        const apiKey = document.getElementById('apiKeyInput').value.trim();
        
        if (!apiKey) {
            showError('Please enter your HeyReach API key');
            return;
        }
        
        showLoading(true);
        hideError();
        
        // Call initialize endpoint
        const response = await fetch('/api/initialize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                api_key: apiKey,
                base_url: 'https://api.heyreach.io'
            })
        });
        
        const data = await response.json();
        
        if (!response.ok || data.error) {
            throw new Error(data.error || 'Failed to initialize API key');
        }
        
        // Success! Show filters section and populate senders
        document.getElementById('apiKeySection').style.display = 'none';
        document.getElementById('apiKeyChangeSection').style.display = 'block';
        document.getElementById('filtersSection').style.display = 'flex';
        document.getElementById('sheetsSection').style.display = 'block';
        
        // Check Google Sheets status
        checkGoogleSheetsStatus();
        
        // Populate senders dropdown
        const senderSelect = document.getElementById('senderSelect');
        senderSelect.innerHTML = '<option value="all">All</option>';
        
        if (data.senders && data.senders.length > 0) {
            data.senders.forEach(sender => {
                if (sender.id !== 'all') {
                    const option = document.createElement('option');
                    option.value = sender.id;
                    option.textContent = sender.name;
                    senderSelect.appendChild(option);
                }
            });
        }
        
        showMessage(data.message || `Successfully connected! Found ${data.senders.length - 1} sender(s). Please select a sender and date range, then click "Apply Filters" to load data.`);
        showLoading(false);
    } catch (error) {
        console.error('Error initializing API key:', error);
        showError('Error connecting to HeyReach: ' + error.message);
        showLoading(false);
    }
}

// Load senders (called after API key is initialized)
async function loadSenders() {
    try {
        const response = await fetch('/api/senders');
        const data = await response.json();
        
        const senderSelect = document.getElementById('senderSelect');
        senderSelect.innerHTML = '<option value="all">All</option>';
        
        if (data.senders && data.senders.length > 0) {
            data.senders.forEach(sender => {
                if (sender.id !== 'all') {
                    const option = document.createElement('option');
                    option.value = sender.id;
                    option.textContent = sender.name;
                    senderSelect.appendChild(option);
                }
            });
        }
    } catch (error) {
        console.error('Error loading senders:', error);
        showError('Error loading senders: ' + error.message);
    }
}

// Load performance data
async function loadPerformanceData() {
    try {
        hideMessage(); // Hide message when user clicks to load data
        showLoading(true);
        hideError();
        
        // Check if filters section is visible (API key must be initialized)
        if (document.getElementById('filtersSection').style.display === 'none') {
            showError('Please enter your API key and connect first');
            showLoading(false);
            return;
        }
        
        const senderId = document.getElementById('senderSelect').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        if (!startDate || !endDate) {
            showError('Please select both start and end dates');
            showLoading(false);
            return;
        }
        
        // Warn user if they selected "All" with a large date range
        const start = new Date(startDate);
        const end = new Date(endDate);
        const daysDiff = Math.ceil((end - start) / (1000 * 60 * 60 * 24));
        
        if (senderId === 'all' && daysDiff > 30) {
            const confirmLoad = confirm(
                `You're about to load data for ALL senders over ${daysDiff} days. ` +
                `This may take a while and make many API calls. Continue?`
            );
            if (!confirmLoad) {
                showLoading(false);
                return;
            }
        }
        
        // Fetch performance data
        const response = await fetch(`/api/performance?sender_id=${senderId}&start_date=${startDate}&end_date=${endDate}`);
        
        // Handle non-JSON (e.g., HTML error page) responses gracefully
        const contentType = response.headers.get('content-type') || '';
        if (!response.ok || !contentType.includes('application/json')) {
            const rawText = await response.text();
            throw new Error(`Unexpected response from server: ${rawText.slice(0, 200)}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        currentData = data;
        
        // Check if we have data
        if (!data || !data.senders || Object.keys(data.senders).length === 0) {
            showError('No data found for the selected date range and sender. Please try a different date range or check your HeyReach account.');
            showLoading(false);
            return;
        }
        
        // Update UI
        updateSummary(data);
        updatePerformanceTables(data);
        updateChart(data);
        
        // Show export section
        document.getElementById('exportSection').style.display = 'block';
        
        showLoading(false);
    } catch (error) {
        console.error('Error loading performance data:', error);
        showError('Error loading performance data: ' + error.message);
        showLoading(false);
    }
}

// Update summary cards
function updateSummary(data) {
    let totalConnectionsSent = 0;
    let totalConnectionsAccepted = 0;
    let totalMessagesSent = 0;
    let totalMessageReplies = 0;
    let totalOpenConversations = 0;
    let totalInterested = 0;
    
    // Use a Set to track which sender+week combinations we've already counted
    // This prevents double-counting when senders appear in both data.senders and data.clients
    const countedWeeks = new Set();
    
    // Aggregate data from all senders
    for (const senderName in data.senders) {
        const weeks = data.senders[senderName];
        weeks.forEach(week => {
            // Create a unique key for this sender+week combination
            const weekKey = `${senderName}_${week.week_end}`;
            
            // Only count if we haven't counted this sender+week combination before
            if (!countedWeeks.has(weekKey)) {
                countedWeeks.add(weekKey);
                totalConnectionsSent += week.connections_sent || 0;
                totalConnectionsAccepted += week.connections_accepted || 0;
                totalMessagesSent += week.messages_sent || 0;
                totalMessageReplies += week.message_replies || 0;
                totalOpenConversations += week.open_conversations || 0;
                totalInterested += week.interested || 0;
            }
        });
    }
    
    const acceptanceRate = totalConnectionsSent > 0 
        ? ((totalConnectionsAccepted / totalConnectionsSent) * 100).toFixed(2)
        : 0;
    
    const replyRate = totalMessagesSent > 0
        ? ((totalMessageReplies / totalMessagesSent) * 100).toFixed(2)
        : 0;
    
    document.getElementById('totalConnectionsSent').textContent = totalConnectionsSent.toLocaleString();
    document.getElementById('totalConnectionsAccepted').textContent = totalConnectionsAccepted.toLocaleString();
    document.getElementById('acceptanceRate').textContent = acceptanceRate + '%';
    document.getElementById('totalMessagesSent').textContent = totalMessagesSent.toLocaleString();
    document.getElementById('totalMessageReplies').textContent = totalMessageReplies.toLocaleString();
    document.getElementById('replyRate').textContent = replyRate + '%';
    document.getElementById('totalOpenConversations').textContent = totalOpenConversations.toLocaleString();
    document.getElementById('totalInterested').textContent = totalInterested.toLocaleString();
}

// Update performance tables
function updatePerformanceTables(data) {
    const performanceSection = document.getElementById('performanceSection');
    performanceSection.innerHTML = '';
    
    // Check if we have any data
    if (!data.senders || Object.keys(data.senders).length === 0) {
        performanceSection.innerHTML = '<p style="text-align: center; padding: 20px; color: #666;">No data available for the selected date range.</p>';
        return;
    }
    
    // Helper function to create a sender table
    function createSenderTable(senderName, weeks) {
        if (!weeks || weeks.length === 0) return null;
        
        const senderContainer = document.createElement('div');
        senderContainer.className = 'sender-table-container';
        
        const senderTitle = document.createElement('h2');
        senderTitle.textContent = senderName;
        senderContainer.appendChild(senderTitle);
        
        const table = document.createElement('table');
        table.className = 'performance-table';
        
        // Create header
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headerRow.innerHTML = `
            <th>Week</th>
            <th>Connections Sent</th>
            <th>Connections Accepted</th>
            <th>Acceptance Rate</th>
            <th>Messages Sent</th>
            <th>Message Replies</th>
            <th>Reply Rate</th>
            <th>Open Conversations</th>
            <th>Interested</th>
        `;
        thead.appendChild(headerRow);
        table.appendChild(thead);
        
        // Create body
        const tbody = document.createElement('tbody');
        weeks.forEach(week => {
            const row = document.createElement('tr');
            const weekDate = new Date(week.week_end);
            const weekLabel = formatWeekLabel(weekDate);
            
            const acceptanceRateClass = getRateClass(week.acceptance_rate, 30, 20);
            const replyRateClass = getRateClass(week.reply_rate, 20, 10);
            
            row.innerHTML = `
                <td>${weekLabel}</td>
                <td class="metric-value">${week.connections_sent || 0}</td>
                <td class="metric-value">${week.connections_accepted || 0}</td>
                <td class="metric-rate ${acceptanceRateClass}">${week.acceptance_rate || 0}%</td>
                <td class="metric-value">${week.messages_sent || 0}</td>
                <td class="metric-value">${week.message_replies || 0}</td>
                <td class="metric-rate ${replyRateClass}">${week.reply_rate || 0}%</td>
                <td class="metric-value">${week.open_conversations || 0}</td>
                <td class="metric-value">${week.interested || 0}</td>
            `;
            tbody.appendChild(row);
        });
        
        table.appendChild(tbody);
        senderContainer.appendChild(table);
        return senderContainer;
    }
    
    // Group by client if clients data is available
    if (data.clients && Object.keys(data.clients).length > 0) {
        // Create tables grouped by client
        for (const clientName in data.clients) {
            const clientContainer = document.createElement('div');
            clientContainer.className = 'client-group-container';
            clientContainer.style.marginBottom = '30px';
            
            const clientTitle = document.createElement('h1');
            clientTitle.textContent = clientName;
            clientTitle.style.fontSize = '24px';
            clientTitle.style.marginBottom = '20px';
            clientTitle.style.color = '#333';
            clientTitle.style.borderBottom = '2px solid #4A90E2';
            clientTitle.style.paddingBottom = '10px';
            clientContainer.appendChild(clientTitle);
            
            const clientSenders = data.clients[clientName];
            for (const senderName in clientSenders) {
                const weeks = clientSenders[senderName];
                const senderTable = createSenderTable(senderName, weeks);
                if (senderTable) {
                    clientContainer.appendChild(senderTable);
                }
            }
            
            performanceSection.appendChild(clientContainer);
        }
        
        // Also show senders without a client (if any)
        for (const senderName in data.senders) {
            // Check if this sender is not in any client group
            let inClientGroup = false;
            for (const clientName in data.clients) {
                if (data.clients[clientName][senderName]) {
                    inClientGroup = true;
                    break;
                }
            }
            
            if (!inClientGroup) {
                const weeks = data.senders[senderName];
                const senderTable = createSenderTable(senderName, weeks);
                if (senderTable) {
                    performanceSection.appendChild(senderTable);
                }
            }
        }
    } else {
        // No client grouping - show all senders
        for (const senderName in data.senders) {
            const weeks = data.senders[senderName];
            const senderTable = createSenderTable(senderName, weeks);
            if (senderTable) {
                performanceSection.appendChild(senderTable);
            }
        }
    }
}

// Update chart
function updateChart(data) {
    const ctx = document.getElementById('performanceChart').getContext('2d');
    
    // Prepare data for chart
    const allWeeks = new Set();
    const datasets = [];
    
    // Collect all unique weeks
    for (const senderName in data.senders) {
        data.senders[senderName].forEach(week => {
            allWeeks.add(week.week_end);
        });
    }
    
    const sortedWeeks = Array.from(allWeeks).sort();
    const weekLabels = sortedWeeks.map(week => formatWeekLabel(new Date(week)));
    
    // Create datasets for each sender
    const colors = [
        { connections: 'rgba(54, 162, 235, 0.8)', accepted: 'rgba(255, 99, 132, 0.8)' },
        { connections: 'rgba(75, 192, 192, 0.8)', accepted: 'rgba(255, 159, 64, 0.8)' },
        { connections: 'rgba(153, 102, 255, 0.8)', accepted: 'rgba(255, 205, 86, 0.8)' },
    ];
    
    let colorIndex = 0;
    for (const senderName in data.senders) {
        const weeks = data.senders[senderName];
        const weekMap = new Map(weeks.map(w => [w.week_end, w]));
        
        const connectionsData = sortedWeeks.map(week => {
            const weekData = weekMap.get(week);
            return weekData ? weekData.connections_sent : 0;
        });
        
        const acceptedData = sortedWeeks.map(week => {
            const weekData = weekMap.get(week);
            return weekData ? weekData.connections_accepted : 0;
        });
        
        const color = colors[colorIndex % colors.length];
        colorIndex++;
        
        datasets.push({
            label: `${senderName} - Connections Sent`,
            data: connectionsData,
            backgroundColor: color.connections,
            borderColor: color.connections,
            borderWidth: 2,
            fill: true,
            stack: 'connections'
        });
        
        datasets.push({
            label: `${senderName} - Connections Accepted`,
            data: acceptedData,
            backgroundColor: color.accepted,
            borderColor: color.accepted,
            borderWidth: 2,
            fill: true,
            stack: 'accepted'
        });
    }
    
    // Destroy existing chart if it exists
    if (performanceChart) {
        performanceChart.destroy();
    }
    
    // Create new chart
    performanceChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: weekLabels,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        boxWidth: 12,
                        padding: 10,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                }
            },
            scales: {
                x: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Week'
                    }
                },
                y: {
                    display: true,
                    title: {
                        display: true,
                        text: 'Count'
                    },
                    beginAtZero: true
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}

// Helper functions
function formatDate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function formatWeekLabel(date) {
    const month = date.getMonth() + 1;
    const day = date.getDate();
    return `${month}/${day}`;
}

function getRateClass(rate, high, medium) {
    if (rate >= high) return 'high';
    if (rate >= medium) return 'medium';
    return 'low';
}

function showLoading(show) {
    document.getElementById('loadingIndicator').style.display = show ? 'block' : 'none';
}

function showError(message) {
    const errorDiv = document.getElementById('errorMessage');
    const errorText = document.getElementById('errorText');
    errorText.textContent = message;
    errorDiv.style.display = 'block';
}

function hideError() {
    document.getElementById('errorMessage').style.display = 'none';
}

// Add a function to show informational messages
function showMessage(message, type = 'info') {
    const messageDiv = document.getElementById('messageDiv');
    if (!messageDiv) {
        // Create message div if it doesn't exist
        const container = document.querySelector('.dashboard-container');
        const filtersSection = document.querySelector('.filters-section');
        const msg = document.createElement('div');
        msg.id = 'messageDiv';
        msg.className = `alert alert-${type === 'success' ? 'success' : 'info'}`;
        msg.textContent = message;
        // Insert after filters section
        if (filtersSection && filtersSection.nextSibling) {
            container.insertBefore(msg, filtersSection.nextSibling);
        } else if (filtersSection) {
            container.appendChild(msg);
        } else {
            container.insertBefore(msg, container.firstChild);
        }
    } else {
        messageDiv.textContent = message;
        messageDiv.className = `alert alert-${type === 'success' ? 'success' : 'info'}`;
        messageDiv.style.display = 'flex';
    }
    
    // Auto-hide after 5 seconds for success messages
    if (type === 'success') {
        setTimeout(() => {
            hideMessage();
        }, 5000);
    }
}

function hideMessage() {
    const messageDiv = document.getElementById('messageDiv');
    if (messageDiv) {
        messageDiv.style.display = 'none';
    }
}

// Change API key
function changeApiKey() {
    // Show API key section again and hide filters
    document.getElementById('apiKeySection').style.display = 'block';
    document.getElementById('apiKeyChangeSection').style.display = 'none';
    document.getElementById('filtersSection').style.display = 'none';
    document.getElementById('sheetsSection').style.display = 'none';
    document.getElementById('apiKeyInput').value = '';
    document.getElementById('apiKeyInput').focus();
    hideMessage();
}

// Toggle API key visibility
function toggleApiKeyVisibility() {
    const apiKeyInput = document.getElementById('apiKeyInput');
    const toggleBtn = document.getElementById('toggleApiKeyBtn');
    
    if (apiKeyInput.type === 'password') {
        apiKeyInput.type = 'text';
        toggleBtn.textContent = 'Hide';
    } else {
        apiKeyInput.type = 'password';
        toggleBtn.textContent = 'Show';
    }
}

// Toggle OAuth secret visibility
function toggleOAuthSecretVisibility() {
    const secretInput = document.getElementById('googleClientSecretInput');
    const toggleBtn = document.getElementById('toggleOAuthSecretBtn');
    
    if (secretInput.type === 'password') {
        secretInput.type = 'text';
        toggleBtn.textContent = 'Hide';
    } else {
        secretInput.type = 'password';
        toggleBtn.textContent = 'Show';
    }
}

// Show OAuth help
function showOAuthHelp() {
    const modal = document.getElementById('oauthHelpModal');
    if (modal) {
        modal.style.display = 'block';
        
        // Update redirect URI
        fetch('/api/google/status')
            .then(response => response.json())
            .then(data => {
                if (data.redirect_uri) {
                    const display = document.getElementById('redirectUriDisplay');
                    if (display) {
                        display.textContent = data.redirect_uri;
                    }
                }
            });
    }
}

// Hide OAuth help
function hideOAuthHelp() {
    const modal = document.getElementById('oauthHelpModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Export to CSV
async function exportToCsv() {
    try {
        // Check if data is loaded
        if (!currentData) {
            showError('Please load data first by clicking "Load Data"');
            return;
        }
        
        showLoading(true);
        hideError();
        
        const senderId = document.getElementById('senderSelect').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        if (!startDate || !endDate) {
            showError('Please select both start and end dates');
            showLoading(false);
            return;
        }
        
        // Create form data
        const response = await fetch('/api/export-csv', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sender_id: senderId,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to export CSV');
        }
        
        // Get filename from Content-Disposition header or use default
        const contentDisposition = response.headers.get('Content-Disposition');
        let filename = 'heyreach_data.csv';
        if (contentDisposition) {
            const filenameMatch = contentDisposition.match(/filename="?(.+)"?/);
            if (filenameMatch) {
                filename = filenameMatch[1];
            }
        }
        
        // Download the file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        showMessage(`CSV file "${filename}" downloaded successfully!`, 'success');
        showLoading(false);
        
    } catch (error) {
        console.error('Error exporting CSV:', error);
        showError('Error exporting CSV: ' + error.message);
        showLoading(false);
    }
}

// Toggle Apps Script input
function toggleAppsScriptInput() {
    const inputGroup = document.getElementById('appsScriptInputGroup');
    const toggleBtn = document.getElementById('toggleAppsScriptBtn');
    
    if (inputGroup.style.display === 'none') {
        inputGroup.style.display = 'block';
        toggleBtn.innerHTML = '<span class="btn-icon">❌</span><span>Cancel</span>';
    } else {
        inputGroup.style.display = 'none';
        toggleBtn.innerHTML = '<span class="btn-icon">⚙️</span><span>Set Up Apps Script</span>';
    }
}

// Send to Apps Script
async function sendToAppsScript() {
    try {
        const appsScriptUrl = document.getElementById('appsScriptUrlInput').value.trim();
        
        if (!appsScriptUrl) {
            showError('Please enter your Apps Script web app URL');
            return;
        }
        
        // Validate URL
        if (!appsScriptUrl.startsWith('https://script.google.com')) {
            showError('Invalid Apps Script URL. Must start with https://script.google.com');
            return;
        }
        
        // Check if data is loaded
        if (!currentData) {
            showError('Please load data first by clicking "Load Data"');
            return;
        }
        
        showLoading(true);
        hideError();
        
        const senderId = document.getElementById('senderSelect').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        if (!startDate || !endDate) {
            showError('Please select both start and end dates');
            showLoading(false);
            return;
        }
        
        const response = await fetch('/api/send-to-apps-script', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                apps_script_url: appsScriptUrl,
                sender_id: senderId,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        let data;
        try {
            data = await response.json();
        } catch (e) {
            throw new Error('Failed to parse server response. Status: ' + response.status);
        }
        
        // Check for error in response (even if status is 200, we might return error messages)
        if (data.error) {
            let errorMsg = data.error;
            if (data.hints && Array.isArray(data.hints)) {
                errorMsg += '\n\n' + data.hints.join('\n');
            } else if (data.hint) {
                errorMsg += '\n\n' + data.hint;
            }
            if (data.instructions && Array.isArray(data.instructions)) {
                errorMsg += '\n\n' + data.instructions.join('\n');
            }
            throw new Error(errorMsg);
        }
        
        if (!response.ok && !data.error) {
            throw new Error('Server returned error: ' + response.status + ' ' + response.statusText);
        }
        
        // Build detailed message
        let message = data.message || 'Data sent successfully!';
        
        // Log full response to console for debugging
        console.log('Apps Script Response:', data);
        
        // Show details if available
        if (data.details) {
            const details = data.details;
            
            // Successfully processed (found and updated)
            if (details.processed && details.processed.length > 0) {
                message += '\n\n✅ Successfully Updated (' + details.processed.length + '):\n' + details.processed.join('\n');
            }
            
            // Found but skipped (already filled)
            if (details.found_skipped && details.found_skipped.length > 0) {
                message += '\n\n⏭️ Found But Skipped (' + details.found_skipped.length + ' - already filled):\n' + details.found_skipped.join('\n');
            }
            
            // Not found in sheet
            if (details.not_found && details.not_found.length > 0) {
                message += '\n\n❌ Not Found in Sheet (' + details.not_found.length + '):\n' + details.not_found.join('\n');
            }
            
            if (details.errors && details.errors.length > 0) {
                message += '\n\n⚠️ Errors:\n' + details.errors.join('\n');
            }
            
            // Show sheets found
            if (details.sheets_found && details.sheets_found.length > 0) {
                console.log('Sheets found in spreadsheet:', details.sheets_found);
            }
            if (details.client_groups_received && details.client_groups_received.length > 0) {
                console.log('Client groups received:', details.client_groups_received);
            }
        }
        
        // Use alert for detailed feedback (since it can show newlines)
        if (data.details && (data.details.not_found?.length > 0 || data.details.errors?.length > 0)) {
            alert(message);
            showMessage('Check the alert for details. Also check browser console (F12) for more info.', 'info');
        } else {
            showMessage(message, 'success');
        }
        
        showLoading(false);
        
    } catch (error) {
        console.error('Error sending to Apps Script:', error);
        showError('Error sending to Apps Script: ' + error.message);
        showLoading(false);
    }
}

// Show Apps Script help
function showAppsScriptHelp() {
    const modal = document.getElementById('appsScriptHelpModal');
    if (modal) {
        modal.style.display = 'flex';
    }
}

// Hide Apps Script help
function hideAppsScriptHelp() {
    const modal = document.getElementById('appsScriptHelpModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Copy Apps Script template
async function copyAppsScriptTemplate() {
    try {
        const response = await fetch('/static/google_apps_script_template.js');
        const scriptText = await response.text();
        
        await navigator.clipboard.writeText(scriptText);
        
        const copyBtn = document.getElementById('copyScriptBtn');
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<span>✅ Copied!</span>';
        copyBtn.style.background = 'linear-gradient(135deg, #28a745 0%, #20c997 100%)';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
            copyBtn.style.background = '';
        }, 2000);
        
        showMessage('Apps Script template copied to clipboard!', 'success');
    } catch (error) {
        console.error('Error copying script:', error);
        showError('Failed to copy script template');
    }
}

// Scroll to OAuth section
function scrollToOAuthSection() {
    const sheetsSection = document.getElementById('sheetsSection');
    if (sheetsSection) {
        sheetsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Highlight the section briefly
        sheetsSection.style.transition = 'box-shadow 0.3s ease';
        sheetsSection.style.boxShadow = '0 0 0 4px rgba(102, 126, 234, 0.3)';
        setTimeout(() => {
            sheetsSection.style.boxShadow = '';
        }, 2000);
    }
}

// Check Google Sheets connection status
async function checkGoogleSheetsStatus() {
    try {
        const response = await fetch('/api/google/status');
        const data = await response.json();
        
        const oauthCredentialsGroup = document.getElementById('oauthCredentialsGroup');
        const oauthSecretGroup = document.getElementById('oauthSecretGroup');
        const saveOAuthGroup = document.getElementById('saveOAuthCredentialsGroup');
        const googleAuthStatus = document.getElementById('googleAuthStatus');
        const notConnectedDiv = document.getElementById('googleNotConnected');
        const connectedDiv = document.getElementById('googleConnected');
        const sheetsUrlGroup = document.getElementById('sheetsUrlGroup');
        const populateGroup = document.getElementById('populateGroup');
        
        // Update redirect URI in help modal
        if (data.redirect_uri) {
            const redirectUriDisplay = document.getElementById('redirectUriDisplay');
            if (redirectUriDisplay) {
                redirectUriDisplay.textContent = data.redirect_uri;
            }
        }
        
        if (!data.has_credentials) {
            // User hasn't provided OAuth credentials yet
            if (oauthCredentialsGroup) oauthCredentialsGroup.style.display = 'block';
            if (oauthSecretGroup) oauthSecretGroup.style.display = 'block';
            if (saveOAuthGroup) saveOAuthGroup.style.display = 'block';
            if (googleAuthStatus) googleAuthStatus.style.display = 'none';
            if (sheetsUrlGroup) sheetsUrlGroup.style.display = 'none';
            if (populateGroup) populateGroup.style.display = 'none';
        } else if (data.authorized) {
            // User has credentials and is authorized
            if (oauthCredentialsGroup) oauthCredentialsGroup.style.display = 'none';
            if (oauthSecretGroup) oauthSecretGroup.style.display = 'none';
            if (saveOAuthGroup) saveOAuthGroup.style.display = 'none';
            if (googleAuthStatus) googleAuthStatus.style.display = 'block';
            if (notConnectedDiv) notConnectedDiv.style.display = 'none';
            if (connectedDiv) connectedDiv.style.display = 'block';
            if (sheetsUrlGroup) sheetsUrlGroup.style.display = 'block';
            if (populateGroup) populateGroup.style.display = 'block';
        } else {
            // User has credentials but not authorized yet
            if (oauthCredentialsGroup) oauthCredentialsGroup.style.display = 'none';
            if (oauthSecretGroup) oauthSecretGroup.style.display = 'none';
            if (saveOAuthGroup) saveOAuthGroup.style.display = 'none';
            if (googleAuthStatus) googleAuthStatus.style.display = 'block';
            if (notConnectedDiv) notConnectedDiv.style.display = 'block';
            if (connectedDiv) connectedDiv.style.display = 'none';
            if (sheetsUrlGroup) sheetsUrlGroup.style.display = 'none';
            if (populateGroup) populateGroup.style.display = 'none';
        }
    } catch (error) {
        console.error('Error checking Google Sheets status:', error);
    }
}

// Save OAuth credentials
async function saveOAuthCredentials() {
    try {
        const clientId = document.getElementById('googleClientIdInput').value.trim();
        const clientSecret = document.getElementById('googleClientSecretInput').value.trim();
        
        if (!clientId || !clientSecret) {
            showError('Please enter both Client ID and Client Secret');
            return;
        }
        
        showLoading(true);
        hideError();
        
        const response = await fetch('/api/google/save-credentials', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                client_id: clientId,
                client_secret: clientSecret
            })
        });
        
        const data = await response.json();
        
        if (!response.ok || data.error) {
            throw new Error(data.error || 'Failed to save credentials');
        }
        
        showMessage(data.message || 'OAuth credentials saved successfully!', 'success');
        showLoading(false);
        
        // Refresh status to show connect button
        checkGoogleSheetsStatus();
        
    } catch (error) {
        console.error('Error saving OAuth credentials:', error);
        showError('Error saving OAuth credentials: ' + error.message);
        showLoading(false);
    }
}

// Connect Google Sheets (OAuth flow)
async function connectGoogleSheets() {
    try {
        showLoading(true);
        hideError();
        
        // Get authorization URL
        const response = await fetch('/api/google/authorize');
        const data = await response.json();
        
        if (!response.ok) {
            if (response.status === 400) {
                // Credentials not saved
                showError('Please save your OAuth credentials first.');
            } else {
                throw new Error(data.error || 'Failed to initiate Google authorization');
            }
            showLoading(false);
            return;
        }
        
        if (data.error) {
            throw new Error(data.error || 'Failed to initiate Google authorization');
        }
        
        // Redirect to Google authorization page
        window.location.href = data.authorization_url;
        
    } catch (error) {
        console.error('Error connecting Google Sheets:', error);
        showError('Error connecting to Google Sheets: ' + error.message);
        showLoading(false);
    }
}

// Disconnect Google Sheets
async function disconnectGoogleSheets() {
    try {
        const response = await fetch('/api/google/revoke', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (!response.ok || data.error) {
            throw new Error(data.error || 'Failed to disconnect');
        }
        
        showMessage('Google Sheets disconnected successfully', 'success');
        checkGoogleSheetsStatus();
        
    } catch (error) {
        console.error('Error disconnecting Google Sheets:', error);
        showError('Error disconnecting Google Sheets: ' + error.message);
    }
}

// Populate Google Sheets with HeyReach data
async function populateSheets() {
    try {
        const sheetsUrl = document.getElementById('sheetsUrlInput').value.trim();
        
        if (!sheetsUrl) {
            showError('Please enter a Google Sheets URL');
            return;
        }
        
        // Validate URL
        if (!sheetsUrl.includes('docs.google.com/spreadsheets')) {
            showError('Invalid Google Sheets URL. Please use a URL like: https://docs.google.com/spreadsheets/d/...');
            return;
        }
        
        // Check if API key is initialized
        if (document.getElementById('filtersSection').style.display === 'none') {
            showError('Please enter your HeyReach API key and connect first');
            return;
        }
        
        // Get current filters
        const senderId = document.getElementById('senderSelect').value;
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        if (!startDate || !endDate) {
            showError('Please select both start and end dates');
            return;
        }
        
        showLoading(true);
        hideError();
        
        // Call populate sheets endpoint
        const response = await fetch('/api/populate-sheets', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sheets_url: sheetsUrl,
                sender_id: senderId,
                start_date: startDate,
                end_date: endDate
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            if (data.requires_auth) {
                showError('Please connect Google Sheets first by clicking "Connect Google Sheets"');
                checkGoogleSheetsStatus();
            } else {
                throw new Error(data.error || 'Failed to populate sheets');
            }
            showLoading(false);
            return;
        }
        
        // Show success message
        let message = data.message || `Successfully updated ${data.updated} cells`;
        if (data.worksheets) {
            const worksheetDetails = Object.entries(data.worksheets)
                .map(([name, info]) => `${name}: ${info.updated} cells updated`)
                .join(', ');
            message += ` (${worksheetDetails})`;
        }
        showMessage(message, 'success');
        
        if (data.errors && data.errors.length > 0) {
            message += `. ${data.errors.length} error(s) occurred. Check console for details.`;
            console.warn('Sheet population errors:', data.errors);
        }
        
        showMessage(message);
        showLoading(false);
        
    } catch (error) {
        console.error('Error populating sheets:', error);
        showError('Error populating Google Sheets: ' + error.message);
        showLoading(false);
    }
}
