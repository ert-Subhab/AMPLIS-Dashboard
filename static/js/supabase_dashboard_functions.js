// ==================== Supabase Integration Functions ====================
// Add these functions to the end of dashboard.js

// Update AI provider labels based on selection
function updateAIProviderLabels() {
    const providerSelect = document.getElementById('aiProviderSelect');
    const apiKeyLabel = document.getElementById('aiApiKeyLabel');
    const apiKeyInput = document.getElementById('aiApiKeyInput');
    const apiKeyHelp = document.getElementById('aiApiKeyHelp');
    
    if (!providerSelect || !apiKeyLabel || !apiKeyInput || !apiKeyHelp) return;
    
    const provider = providerSelect.value;
    
    switch (provider) {
        case 'openai':
            apiKeyLabel.textContent = 'OpenAI API Key:';
            apiKeyInput.placeholder = 'sk-...';
            apiKeyHelp.innerHTML = 'Your OpenAI API key. Get it from <a href="https://platform.openai.com/api-keys" target="_blank">OpenAI Platform</a>.';
            break;
        case 'claude':
            apiKeyLabel.textContent = 'Anthropic API Key:';
            apiKeyInput.placeholder = 'sk-ant-...';
            apiKeyHelp.innerHTML = 'Your Anthropic API key. Get it from <a href="https://console.anthropic.com/" target="_blank">Anthropic Console</a>.';
            break;
        case 'gemini':
            apiKeyLabel.textContent = 'Google API Key:';
            apiKeyInput.placeholder = 'Enter your API key...';
            apiKeyHelp.innerHTML = 'Your Google API key for Gemini. Get it from <a href="https://makersuite.google.com/app/apikey" target="_blank">Google AI Studio</a>.';
            break;
    }
}

// Load Supabase configuration from localStorage
function loadSupabaseConfig() {
    try {
        const config = JSON.parse(localStorage.getItem('supabaseConfig') || '{}');
        const urlInput = document.getElementById('supabaseUrlInput');
        const keyInput = document.getElementById('supabaseKeyInput');
        const aiKeyInput = document.getElementById('aiApiKeyInput');
        const aiProviderSelect = document.getElementById('aiProviderSelect');
        
        if (urlInput && config.supabaseUrl) urlInput.value = config.supabaseUrl;
        if (keyInput && config.supabaseKey) keyInput.value = config.supabaseKey;
        if (aiKeyInput && config.aiApiKey) aiKeyInput.value = config.aiApiKey;
        if (aiProviderSelect && config.aiProvider) {
            aiProviderSelect.value = config.aiProvider;
            updateAIProviderLabels();
        }
        
        // Initialize Supabase if credentials are available
        if (config.supabaseUrl && config.supabaseKey && typeof initializeSupabase === 'function') {
            initializeSupabase(config.supabaseUrl, config.supabaseKey);
            showSupabaseStatus('Connected', 'success');
            const aiSection = document.getElementById('aiEvaluationSection');
            if (aiSection) aiSection.style.display = 'block';
        }
    } catch (error) {
        console.error('Error loading Supabase config:', error);
    }
}

// Save Supabase configuration to localStorage
function saveSupabaseConfig() {
    try {
        const supabaseUrl = document.getElementById('supabaseUrlInput').value.trim();
        const supabaseKey = document.getElementById('supabaseKeyInput').value.trim();
        const openaiKey = document.getElementById('openaiKeyInput').value.trim();
        
        if (!supabaseUrl || !supabaseKey) {
            showError('Please enter both Supabase URL and Key');
            return;
        }
        
        if (typeof supabase === 'undefined' || typeof initializeSupabase !== 'function') {
            showError('Supabase libraries not loaded. Please refresh the page.');
            return;
        }
        
        const success = initializeSupabase(supabaseUrl, supabaseKey);
        if (!success) {
            showError('Failed to initialize Supabase client');
            return;
        }
        
        const aiProvider = document.getElementById('aiProviderSelect')?.value || 'openai';
        const aiApiKey = document.getElementById('aiApiKeyInput')?.value.trim() || '';
        
        const config = { 
            supabaseUrl, 
            supabaseKey, 
            aiApiKey,
            aiProvider
        };
        localStorage.setItem('supabaseConfig', JSON.stringify(config));
        
        showSupabaseStatus('Configuration saved and connected!', 'success');
        const aiSection = document.getElementById('aiEvaluationSection');
        if (aiSection) aiSection.style.display = 'block';
        showMessage('Supabase configuration saved successfully!', 'success');
    } catch (error) {
        console.error('Error saving Supabase config:', error);
        showError('Error saving configuration: ' + error.message);
    }
}

// Test Supabase connection
async function testSupabaseConnection() {
    try {
        const supabaseUrl = document.getElementById('supabaseUrlInput').value.trim();
        const supabaseKey = document.getElementById('supabaseKeyInput').value.trim();
        
        if (!supabaseUrl || !supabaseKey) {
            showError('Please enter both Supabase URL and Key');
            return;
        }
        
        showLoading(true);
        
        if (typeof supabase === 'undefined') {
            showError('Supabase library not loaded. Please refresh the page.');
            showLoading(false);
            return;
        }
        
        const testClient = supabase.createClient(supabaseUrl, supabaseKey);
        const { data, error } = await testClient.from('heyreach_messages').select('id').limit(1);
        
        if (error) throw error;
        
        showSupabaseStatus('Connection successful!', 'success');
        showMessage('Supabase connection test passed!', 'success');
    } catch (error) {
        console.error('Connection test failed:', error);
        showSupabaseStatus('Connection failed: ' + error.message, 'error');
        showError('Connection test failed: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Toggle Supabase configuration section
function toggleSupabaseConfig() {
    const section = document.getElementById('supabaseConfigSection');
    const btn = document.getElementById('toggleSupabaseBtn');
    if (!section || !btn) return;
    
    if (section.style.display === 'none') {
        section.style.display = 'block';
        btn.innerHTML = '<span class="btn-icon">❌</span><span>Close</span>';
        section.scrollIntoView({ behavior: 'smooth' });
    } else {
        section.style.display = 'none';
        btn.innerHTML = '<span class="btn-icon">⚙️</span><span>Configure Supabase</span>';
    }
}

// Show Supabase status
function showSupabaseStatus(message, type) {
    const statusDiv = document.getElementById('supabaseStatus');
    if (!statusDiv) return;
    statusDiv.style.display = 'block';
    statusDiv.style.backgroundColor = type === 'success' ? '#d4edda' : '#f8d7da';
    statusDiv.style.color = type === 'success' ? '#155724' : '#721c24';
    statusDiv.style.border = `1px solid ${type === 'success' ? '#c3e6cb' : '#f5c6cb'}`;
    statusDiv.textContent = message;
}

// Toggle password visibility
function togglePasswordVisibility(inputId, buttonId) {
    const input = document.getElementById(inputId);
    const button = document.getElementById(buttonId);
    if (!input || !button) return;
    
    if (input.type === 'password') {
        input.type = 'text';
        button.textContent = 'Hide';
    } else {
        input.type = 'password';
        button.textContent = 'Show';
    }
}

// Evaluate messages with AI
async function evaluateMessages() {
    try {
        const config = JSON.parse(localStorage.getItem('supabaseConfig') || '{}');
        const aiProvider = config.aiProvider || document.getElementById('aiProviderSelect')?.value || 'openai';
        const aiApiKey = config.aiApiKey || document.getElementById('aiApiKeyInput')?.value.trim();
        
        if (!aiApiKey) {
            showError(`Please enter your ${aiProvider === 'openai' ? 'OpenAI' : aiProvider === 'claude' ? 'Anthropic' : 'Google'} API key`);
            return;
        }
        
        if (typeof supabaseClient === 'undefined' || !supabaseClient) {
            showError('Supabase not initialized. Please save your configuration first.');
            return;
        }
        
        showLoading(true);
        const progressDiv = document.getElementById('evaluationProgress');
        const statusDiv = document.getElementById('evaluationStatus');
        const progressBar = document.getElementById('evaluationProgressBar');
        
        if (progressDiv) progressDiv.style.display = 'block';
        if (statusDiv) statusDiv.textContent = 'Fetching unevaluated messages...';
        if (progressBar) progressBar.style.width = '10%';
        
        const messages = await getUnevaluatedMessages(100);
        
        if (messages.length === 0) {
            showMessage('No unevaluated messages found.', 'info');
            if (progressDiv) progressDiv.style.display = 'none';
            showLoading(false);
            return;
        }
        
        if (statusDiv) statusDiv.textContent = `Evaluating ${messages.length} messages using ${aiProvider}...`;
        if (progressBar) progressBar.style.width = '20%';
        
        let processed = 0, errors = 0;
        
        for (let i = 0; i < messages.length; i++) {
            const message = messages[i];
            try {
                if (statusDiv) statusDiv.textContent = `Evaluating message ${i + 1} of ${messages.length} using ${aiProvider}...`;
                if (progressBar) progressBar.style.width = `${20 + (i / messages.length) * 70}%`;
                await processMessageEvaluation(message, aiProvider, aiApiKey);
                processed++;
            } catch (error) {
                console.error(`Error evaluating message ${message.id}:`, error);
                errors++;
            }
        }
        
        if (progressBar) progressBar.style.width = '100%';
        if (statusDiv) statusDiv.textContent = `Completed! Processed: ${processed}, Errors: ${errors}`;
        showMessage(`Evaluation complete! Processed ${processed} messages, ${errors} errors.`, 'success');
        
        setTimeout(() => { if (progressDiv) progressDiv.style.display = 'none'; }, 3000);
    } catch (error) {
        console.error('Error evaluating messages:', error);
        showError('Error evaluating messages: ' + error.message);
    } finally {
        showLoading(false);
    }
}

// Show n8n help modal
function showN8nHelp() {
    const modal = document.getElementById('n8nHelpModal');
    if (modal) {
        modal.style.display = 'block';
    }
}

// Hide n8n help modal
function hideN8nHelp() {
    const modal = document.getElementById('n8nHelpModal');
    if (modal) {
        modal.style.display = 'none';
    }
}

// Get weekly stats from Supabase
async function getWeeklyStatsFromSupabase() {
    try {
        if (typeof supabaseClient === 'undefined' || !supabaseClient) {
            showError('Supabase not initialized. Please save your configuration first.');
            return;
        }
        
        showLoading(true);
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        
        if (!startDate || !endDate) {
            showError('Please select a date range first');
            showLoading(false);
            return;
        }
        
        const clientStats = await getStatsByClient(startDate, endDate);
        const resultsDiv = document.getElementById('weeklyStatsResults');
        const tableDiv = document.getElementById('weeklyStatsTable');
        
        if (!resultsDiv || !tableDiv) {
            showError('Results display elements not found');
            showLoading(false);
            return;
        }
        
        let html = '<table style="width: 100%; border-collapse: collapse; margin-top: 10px;"><thead><tr><th style="border: 1px solid #ddd; padding: 8px;">Client</th><th style="border: 1px solid #ddd; padding: 8px;">Week</th><th style="border: 1px solid #ddd; padding: 8px;">Open Conversations</th><th style="border: 1px solid #ddd; padding: 8px;">Interested</th></tr></thead><tbody>';
        
        for (const [clientName, weeks] of Object.entries(clientStats)) {
            for (const week of weeks) {
                html += `<tr><td style="border: 1px solid #ddd; padding: 8px;">${clientName}</td><td style="border: 1px solid #ddd; padding: 8px;">${week.week_end}</td><td style="border: 1px solid #ddd; padding: 8px;">${week.open_conversations}</td><td style="border: 1px solid #ddd; padding: 8px;">${week.interested}</td></tr>`;
            }
        }
        
        html += '</tbody></table>';
        tableDiv.innerHTML = html;
        resultsDiv.style.display = 'block';
        showMessage('Weekly stats loaded successfully!', 'success');
    } catch (error) {
        console.error('Error getting weekly stats:', error);
        showError('Error getting weekly stats: ' + error.message);
    } finally {
        showLoading(false);
    }
}

