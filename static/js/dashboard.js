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
        
        // Load senders dropdown (this is fast, no API calls)
        await loadSenders();
        
        // DON'T automatically load performance data - wait for user to click "Apply Filters"
        // Show a message to the user instead
        showMessage('Please select a sender and date range, then click "Apply Filters" to load data.');
        
        // Set up event listeners
        document.getElementById('applyFiltersBtn').addEventListener('click', loadPerformanceData);
        document.getElementById('refreshBtn').addEventListener('click', loadPerformanceData);
    } catch (error) {
        showError('Error initializing dashboard: ' + error.message);
    }
}

// Load senders
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
    
    // Aggregate data from all senders
    for (const senderName in data.senders) {
        const weeks = data.senders[senderName];
        weeks.forEach(week => {
            totalConnectionsSent += week.connections_sent || 0;
            totalConnectionsAccepted += week.connections_accepted || 0;
            totalMessagesSent += week.messages_sent || 0;
            totalMessageReplies += week.message_replies || 0;
            totalOpenConversations += week.open_conversations || 0;
            totalInterested += week.interested || 0;
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
            const weekDate = new Date(week.week_start);
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
            allWeeks.add(week.week_start);
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
        const weekMap = new Map(weeks.map(w => [w.week_start, w]));
        
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
function showMessage(message) {
    const messageDiv = document.getElementById('messageDiv');
    if (!messageDiv) {
        // Create message div if it doesn't exist
        const container = document.querySelector('.dashboard-container');
        const filtersSection = document.querySelector('.filters-section');
        const msg = document.createElement('div');
        msg.id = 'messageDiv';
        msg.className = 'alert alert-info';
        msg.style.cssText = 'margin: 20px 0; padding: 15px; background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 4px; color: #0c5460; text-align: center;';
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
        messageDiv.style.display = 'block';
    }
}

function hideMessage() {
    const messageDiv = document.getElementById('messageDiv');
    if (messageDiv) {
        messageDiv.style.display = 'none';
    }
}
