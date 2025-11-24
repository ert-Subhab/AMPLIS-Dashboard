// Task Manager JavaScript

const API_BASE = '/api';

// State
let currentClientId = null;
let currentTasks = [];
let clients = [];
let recognition = null;
let currentView = 'tasks'; // 'tasks' or 'notes'
let currentNotes = [];
let currentNote = null;
let noteBlocks = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeVoiceRecognition();
    loadClients();
    loadTasks();
    setupEventListeners();
    setupNotesView();
});

// Voice Recognition Setup
function initializeVoiceRecognition() {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';
        
        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            handleVoiceInput(transcript);
        };
        
        recognition.onerror = (event) => {
            console.error('Speech recognition error:', event.error);
            alert('Voice recognition error: ' + event.error);
            stopRecording();
        };
        
        recognition.onend = () => {
            stopRecording();
        };
    } else {
        console.warn('Speech recognition not supported');
        document.getElementById('voiceBtn').style.display = 'none';
    }
}

// Event Listeners
function setupEventListeners() {
    // Client buttons
    document.getElementById('addClientBtn').addEventListener('click', () => openClientModal());
    document.getElementById('closeClientModal').addEventListener('click', () => closeClientModal());
    document.getElementById('cancelClientBtn').addEventListener('click', () => closeClientModal());
    document.getElementById('clientForm').addEventListener('submit', handleClientSubmit);
    
    // Task buttons
    document.getElementById('addTaskBtn').addEventListener('click', () => openTaskModal());
    document.getElementById('closeTaskModal').addEventListener('click', () => closeTaskModal());
    document.getElementById('cancelTaskBtn').addEventListener('click', () => closeTaskModal());
    document.getElementById('taskForm').addEventListener('submit', handleTaskSubmit);
    
    // AI Extract
    document.getElementById('aiExtractBtn').addEventListener('click', () => openAiExtractModal());
    document.getElementById('closeAiExtractModal').addEventListener('click', () => closeAiExtractModal());
    document.getElementById('cancelAiExtractBtn').addEventListener('click', () => closeAiExtractModal());
    document.getElementById('extractTasksBtn').addEventListener('click', handleExtractTasks);
    
    // Voice Input
    document.getElementById('voiceBtn').addEventListener('click', () => openVoiceModal());
    document.getElementById('closeVoiceModal').addEventListener('click', () => closeVoiceModal());
    document.getElementById('startRecordingBtn').addEventListener('click', toggleRecording);
    document.getElementById('createTaskFromVoiceBtn').addEventListener('click', createTaskFromVoice);
    
    // Search
    document.getElementById('searchInput').addEventListener('input', debounce(() => {
        if (currentView === 'tasks') {
            handleSearch();
        } else {
            loadNotes();
        }
    }, 300));
    
    // Update add button based on view
    document.getElementById('addTaskBtn').addEventListener('click', () => {
        if (currentView === 'tasks') {
            openTaskModal();
        } else {
            createNewNote();
        }
    });
    
    // Filters
    document.getElementById('statusFilter').addEventListener('change', loadTasks);
    document.getElementById('priorityFilter').addEventListener('change', loadTasks);
    document.getElementById('startDateFilter').addEventListener('change', loadTasks);
    document.getElementById('endDateFilter').addEventListener('change', loadTasks);
    
    // Close modals on outside click
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.remove('active');
            }
        });
    });
}

// Client Management
async function loadClients() {
    try {
        const response = await fetch(`${API_BASE}/clients`);
        const data = await response.json();
        clients = data;
        renderClients();
        updateClientSelects();
    } catch (error) {
        console.error('Error loading clients:', error);
        showError('Failed to load clients');
    }
}

function renderClients() {
    const clientList = document.getElementById('clientList');
    clientList.innerHTML = '';
    
    // Add "All Tasks" option
    const allItem = document.createElement('div');
    allItem.className = `client-item ${currentClientId === null ? 'active' : ''}`;
    allItem.innerHTML = `
        <span class="client-item-name">All Tasks</span>
        <span class="client-item-count">${currentTasks.length}</span>
    `;
    allItem.addEventListener('click', () => {
        currentClientId = null;
        loadTasks();
        renderClients();
    });
    clientList.appendChild(allItem);
    
    // Add clients
    clients.forEach(client => {
        const item = document.createElement('div');
        item.className = `client-item ${currentClientId === client.id ? 'active' : ''}`;
        item.innerHTML = `
            <span class="client-item-name">${escapeHtml(client.name)}</span>
            <span class="client-item-count">${client.task_count || 0}</span>
        `;
        item.addEventListener('click', () => {
            currentClientId = client.id;
            loadTasks();
            renderClients();
        });
        clientList.appendChild(item);
    });
}

function updateClientSelects() {
    const selects = ['taskClientId', 'aiExtractClient'];
    selects.forEach(selectId => {
        const select = document.getElementById(selectId);
        if (select) {
            select.innerHTML = '<option value="">Select Client</option>';
            clients.forEach(client => {
                const option = document.createElement('option');
                option.value = client.id;
                option.textContent = client.name;
                if (currentClientId === client.id) {
                    option.selected = true;
                }
                select.appendChild(option);
            });
        }
    });
}

function openClientModal(client = null) {
    const modal = document.getElementById('clientModal');
    const form = document.getElementById('clientForm');
    const title = document.getElementById('clientModalTitle');
    
    if (client) {
        title.textContent = 'Edit Client';
        document.getElementById('clientName').value = client.name;
        document.getElementById('clientDescription').value = client.description || '';
        form.dataset.clientId = client.id;
    } else {
        title.textContent = 'Add Client';
        form.reset();
        delete form.dataset.clientId;
    }
    
    modal.classList.add('active');
}

function closeClientModal() {
    document.getElementById('clientModal').classList.remove('active');
    document.getElementById('clientForm').reset();
}

async function handleClientSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const clientId = form.dataset.clientId;
    const data = {
        name: document.getElementById('clientName').value,
        description: document.getElementById('clientDescription').value
    };
    
    try {
        if (clientId) {
            // Update
            const response = await fetch(`${API_BASE}/clients/${clientId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error('Failed to update client');
        } else {
            // Create
            const response = await fetch(`${API_BASE}/clients`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error('Failed to create client');
        }
        
        closeClientModal();
        loadClients();
    } catch (error) {
        console.error('Error saving client:', error);
        showError('Failed to save client');
    }
}

// Task Management
async function loadTasks() {
    try {
        const params = new URLSearchParams();
        if (currentClientId) params.append('client_id', currentClientId);
        
        const status = document.getElementById('statusFilter').value;
        if (status) params.append('status', status);
        
        const priority = document.getElementById('priorityFilter').value;
        if (priority) params.append('priority', priority);
        
        const startDate = document.getElementById('startDateFilter').value;
        if (startDate) params.append('start_date', startDate);
        
        const endDate = document.getElementById('endDateFilter').value;
        if (endDate) params.append('end_date', endDate);
        
        const search = document.getElementById('searchInput').value;
        if (search) params.append('search', search);
        
        const response = await fetch(`${API_BASE}/tasks?${params}`);
        const data = await response.json();
        currentTasks = data;
        renderTasks();
        updateTaskCount();
        updateClientName();
    } catch (error) {
        console.error('Error loading tasks:', error);
        showError('Failed to load tasks');
    }
}

function renderTasks() {
    const taskList = document.getElementById('taskList');
    taskList.innerHTML = '';
    
    if (currentTasks.length === 0) {
        taskList.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-tasks"></i>
                <h3>No tasks found</h3>
                <p>Create a new task to get started</p>
            </div>
        `;
        return;
    }
    
    currentTasks.forEach(task => {
        const item = document.createElement('div');
        item.className = `task-item priority-${task.priority} ${task.status === 'completed' ? 'completed' : ''}`;
        item.innerHTML = `
            <div class="task-header">
                <div class="task-title">${escapeHtml(task.title)}</div>
                <div class="task-actions">
                    <button class="task-action-btn" onclick="toggleTaskStatus(${task.id}, '${task.status}')" title="Toggle Status">
                        <i class="fas fa-${task.status === 'completed' ? 'undo' : 'check'}"></i>
                    </button>
                    <button class="task-action-btn" onclick="editTask(${task.id})" title="Edit">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="task-action-btn" onclick="deleteTask(${task.id})" title="Delete">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
            ${task.description ? `<div class="task-description">${escapeHtml(task.description)}</div>` : ''}
            <div class="task-meta">
                <span class="task-meta-item">
                    <i class="fas fa-building"></i>
                    ${escapeHtml(task.client_name || 'Unknown')}
                </span>
                <span class="status-badge ${task.status}">${task.status.replace('_', ' ')}</span>
                <span class="priority-badge ${task.priority}">${task.priority}</span>
                ${task.due_date ? `<span class="task-meta-item"><i class="fas fa-calendar"></i> ${formatDate(task.due_date)}</span>` : ''}
                <span class="task-meta-item"><i class="fas fa-clock"></i> ${formatDate(task.created_at)}</span>
            </div>
        `;
        taskList.appendChild(item);
    });
}

function updateTaskCount() {
    document.getElementById('taskCount').textContent = `${currentTasks.length} task${currentTasks.length !== 1 ? 's' : ''}`;
}

function updateClientName() {
    if (currentClientId) {
        const client = clients.find(c => c.id === currentClientId);
        document.getElementById('currentClientName').textContent = client ? client.name : 'Unknown Client';
    } else {
        document.getElementById('currentClientName').textContent = 'All Tasks';
    }
}

function openTaskModal(task = null) {
    const modal = document.getElementById('taskModal');
    const form = document.getElementById('taskForm');
    const title = document.getElementById('taskModalTitle');
    
    updateClientSelects();
    
    if (task) {
        title.textContent = 'Edit Task';
        document.getElementById('taskClientId').value = task.client_id;
        document.getElementById('taskTitle').value = task.title;
        document.getElementById('taskDescription').value = task.description || '';
        document.getElementById('taskStatus').value = task.status;
        document.getElementById('taskPriority').value = task.priority;
        document.getElementById('taskDueDate').value = task.due_date ? task.due_date.split('T')[0] : '';
        form.dataset.taskId = task.id;
    } else {
        title.textContent = 'Add Task';
        form.reset();
        if (currentClientId) {
            document.getElementById('taskClientId').value = currentClientId;
        }
        delete form.dataset.taskId;
    }
    
    modal.classList.add('active');
}

function closeTaskModal() {
    document.getElementById('taskModal').classList.remove('active');
    document.getElementById('taskForm').reset();
}

async function handleTaskSubmit(e) {
    e.preventDefault();
    const form = e.target;
    const taskId = form.dataset.taskId;
    const data = {
        client_id: parseInt(document.getElementById('taskClientId').value),
        title: document.getElementById('taskTitle').value,
        description: document.getElementById('taskDescription').value,
        status: document.getElementById('taskStatus').value,
        priority: document.getElementById('taskPriority').value,
        due_date: document.getElementById('taskDueDate').value || null
    };
    
    try {
        if (taskId) {
            // Update
            const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error('Failed to update task');
        } else {
            // Create
            const response = await fetch(`${API_BASE}/tasks`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            });
            if (!response.ok) throw new Error('Failed to create task');
        }
        
        closeTaskModal();
        loadTasks();
        loadClients(); // Refresh client counts
    } catch (error) {
        console.error('Error saving task:', error);
        showError('Failed to save task');
    }
}

async function toggleTaskStatus(taskId, currentStatus) {
    const newStatus = currentStatus === 'completed' ? 'pending' : 'completed';
    try {
        const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status: newStatus })
        });
        if (!response.ok) throw new Error('Failed to update task');
        loadTasks();
    } catch (error) {
        console.error('Error updating task:', error);
        showError('Failed to update task');
    }
}

async function editTask(taskId) {
    const task = currentTasks.find(t => t.id === taskId);
    if (task) {
        openTaskModal(task);
    }
}

async function deleteTask(taskId) {
    if (!confirm('Are you sure you want to delete this task?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/tasks/${taskId}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete task');
        loadTasks();
        loadClients(); // Refresh client counts
    } catch (error) {
        console.error('Error deleting task:', error);
        showError('Failed to delete task');
    }
}

// AI Extract
function openAiExtractModal() {
    const modal = document.getElementById('aiExtractModal');
    updateClientSelects();
    document.getElementById('aiExtractText').value = '';
    document.getElementById('extractedTasksContainer').style.display = 'none';
    modal.classList.add('active');
}

function closeAiExtractModal() {
    document.getElementById('aiExtractModal').classList.remove('active');
}

async function handleExtractTasks() {
    const text = document.getElementById('aiExtractText').value;
    const clientId = document.getElementById('aiExtractClient').value;
    
    if (!text.trim()) {
        alert('Please enter some text to extract tasks from');
        return;
    }
    
    const client = clientId ? clients.find(c => c.id === parseInt(clientId)) : null;
    
    try {
        const response = await fetch(`${API_BASE}/ai/extract-tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                text: text,
                client_name: client ? client.name : null
            })
        });
        
        if (!response.ok) throw new Error('Failed to extract tasks');
        
        const data = await response.json();
        displayExtractedTasks(data.tasks, clientId);
    } catch (error) {
        console.error('Error extracting tasks:', error);
        showError('Failed to extract tasks');
    }
}

function displayExtractedTasks(tasks, defaultClientId) {
    const container = document.getElementById('extractedTasksContainer');
    const list = document.getElementById('extractedTasksList');
    
    list.innerHTML = '';
    
    tasks.forEach((task, index) => {
        const item = document.createElement('div');
        item.className = 'extracted-task-item';
        item.innerHTML = `
            <h5>${escapeHtml(task.title)}</h5>
            <p>${escapeHtml(task.description || '')}</p>
            <div class="form-row">
                <div class="form-group">
                    <label>Client</label>
                    <select class="extracted-task-client" data-index="${index}">
                        <option value="">Select Client</option>
                        ${clients.map(c => `<option value="${c.id}" ${c.id === parseInt(defaultClientId) ? 'selected' : ''}>${escapeHtml(c.name)}</option>`).join('')}
                    </select>
                </div>
                <div class="form-group">
                    <label>Priority</label>
                    <select class="extracted-task-priority" data-index="${index}">
                        <option value="low" ${task.priority === 'low' ? 'selected' : ''}>Low</option>
                        <option value="medium" ${task.priority === 'medium' ? 'selected' : ''}>Medium</option>
                        <option value="high" ${task.priority === 'high' ? 'selected' : ''}>High</option>
                        <option value="urgent" ${task.priority === 'urgent' ? 'selected' : ''}>Urgent</option>
                    </select>
                </div>
            </div>
            <button class="btn-primary" onclick="createExtractedTask(${index})" style="margin-top: 10px;">
                Create Task
            </button>
        `;
        list.appendChild(item);
    });
    
    container.style.display = 'block';
}

async function createExtractedTask(index) {
    const item = document.querySelectorAll('.extracted-task-item')[index];
    const clientId = item.querySelector('.extracted-task-client').value;
    const priority = item.querySelector('.extracted-task-priority').value;
    const title = item.querySelector('h5').textContent;
    const description = item.querySelector('p').textContent;
    
    if (!clientId) {
        alert('Please select a client');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                client_id: parseInt(clientId),
                title: title,
                description: description,
                priority: priority,
                status: 'pending'
            })
        });
        
        if (!response.ok) throw new Error('Failed to create task');
        
        item.style.opacity = '0.5';
        item.querySelector('button').textContent = 'Created ✓';
        item.querySelector('button').disabled = true;
        
        loadTasks();
        loadClients();
    } catch (error) {
        console.error('Error creating task:', error);
        showError('Failed to create task');
    }
}

// Voice Input
function openVoiceModal() {
    const modal = document.getElementById('voiceModal');
    document.getElementById('recordingStatus').style.display = 'none';
    document.getElementById('voiceTextResult').style.display = 'none';
    document.getElementById('voiceText').textContent = '';
    modal.classList.add('active');
}

function closeVoiceModal() {
    document.getElementById('voiceModal').classList.remove('active');
    stopRecording();
}

function toggleRecording() {
    if (recognition && recognition.state === 'recording') {
        stopRecording();
    } else {
        startRecording();
    }
}

function startRecording() {
    if (!recognition) {
        alert('Voice recognition is not available in your browser');
        return;
    }
    
    try {
        recognition.start();
        document.getElementById('startRecordingBtn').classList.add('recording');
        document.getElementById('startRecordingBtn').innerHTML = '<i class="fas fa-stop"></i><span>Click to Stop</span>';
        document.getElementById('recordingStatus').style.display = 'block';
    } catch (error) {
        console.error('Error starting recognition:', error);
    }
}

function stopRecording() {
    if (recognition && recognition.state === 'recording') {
        recognition.stop();
    }
    document.getElementById('startRecordingBtn').classList.remove('recording');
    document.getElementById('startRecordingBtn').innerHTML = '<i class="fas fa-microphone"></i><span>Click to Start Recording</span>';
    document.getElementById('recordingStatus').style.display = 'none';
}

async function handleVoiceInput(transcript) {
    document.getElementById('voiceText').textContent = transcript;
    document.getElementById('voiceTextResult').style.display = 'block';
    
    // Parse voice command
    try {
        const response = await fetch(`${API_BASE}/ai/parse-voice`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: transcript })
        });
        
        if (!response.ok) throw new Error('Failed to parse voice');
        
        const parsed = await response.json();
        window.parsedVoiceCommand = parsed;
    } catch (error) {
        console.error('Error parsing voice:', error);
        // Use basic parsing
        window.parsedVoiceCommand = {
            client_name: null,
            title: transcript,
            description: transcript,
            priority: 'medium',
            due_date: null
        };
    }
}

async function createTaskFromVoice() {
    const parsed = window.parsedVoiceCommand;
    if (!parsed) {
        alert('No voice command parsed');
        return;
    }
    
    // Find client by name if specified
    let clientId = currentClientId;
    if (parsed.client_name) {
        const client = clients.find(c => 
            c.name.toLowerCase().includes(parsed.client_name.toLowerCase())
        );
        if (client) {
            clientId = client.id;
        } else {
            alert(`Client "${parsed.client_name}" not found. Please select a client.`);
            // Open task modal with parsed data
            openTaskModal({
                client_id: null,
                title: parsed.title,
                description: parsed.description,
                priority: parsed.priority,
                due_date: parsed.due_date
            });
            closeVoiceModal();
            return;
        }
    }
    
    if (!clientId) {
        alert('Please select a client first or specify client name in voice command');
        return;
    }
    
    try {
        const response = await fetch(`${API_BASE}/tasks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                client_id: clientId,
                title: parsed.title,
                description: parsed.description,
                priority: parsed.priority,
                due_date: parsed.due_date,
                status: 'pending'
            })
        });
        
        if (!response.ok) throw new Error('Failed to create task');
        
        closeVoiceModal();
        loadTasks();
        loadClients();
    } catch (error) {
        console.error('Error creating task from voice:', error);
        showError('Failed to create task');
    }
}

// Search
function handleSearch() {
    loadTasks();
}

// Utility Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
        year: 'numeric', 
        month: 'short', 
        day: 'numeric' 
    });
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function showError(message) {
    alert(message); // Can be replaced with a toast notification
}

// Notes/Documents View (Notion-like)
function setupNotesView() {
    // View toggle
    document.getElementById('tasksViewBtn').addEventListener('click', () => switchView('tasks'));
    document.getElementById('notesViewBtn').addEventListener('click', () => switchView('notes'));
    
    // Notes buttons
    document.getElementById('addNoteBtn').addEventListener('click', createNewNote);
    document.getElementById('saveNoteBtn').addEventListener('click', saveCurrentNote);
    document.getElementById('deleteNoteBtn').addEventListener('click', deleteCurrentNote);
    document.getElementById('noteTitleInput').addEventListener('input', debounce(saveCurrentNote, 1000));
}

function switchView(view) {
    currentView = view;
    
    // Update buttons
    document.getElementById('tasksViewBtn').classList.toggle('active', view === 'tasks');
    document.getElementById('notesViewBtn').classList.toggle('active', view === 'notes');
    
    // Show/hide views
    document.getElementById('tasksView').style.display = view === 'tasks' ? 'flex' : 'none';
    document.getElementById('notesView').style.display = view === 'notes' ? 'flex' : 'none';
    
    // Update add button text
    document.getElementById('addButtonText').textContent = view === 'tasks' ? 'Add Task' : 'New Document';
    
    // Update search placeholder
    document.getElementById('searchInput').placeholder = view === 'tasks' ? 'Search tasks...' : 'Search documents...';
    
    if (view === 'notes') {
        loadNotes();
    } else {
        loadTasks();
    }
}

async function loadNotes() {
    try {
        const params = new URLSearchParams();
        if (currentClientId) params.append('client_id', currentClientId);
        
        const search = document.getElementById('searchInput').value;
        if (search) params.append('search', search);
        
        const response = await fetch(`${API_BASE}/notes?${params}`);
        const data = await response.json();
        currentNotes = data;
        renderNotesList();
    } catch (error) {
        console.error('Error loading notes:', error);
        showError('Failed to load documents');
    }
}

function renderNotesList() {
    const notesList = document.getElementById('notesList');
    notesList.innerHTML = '';
    
    if (currentNotes.length === 0) {
        notesList.innerHTML = '<div class="empty-state"><p>No documents yet</p></div>';
        return;
    }
    
    currentNotes.forEach(note => {
        const item = document.createElement('div');
        item.className = `note-item ${currentNote && currentNote.id === note.id ? 'active' : ''}`;
        
        const preview = note.content && note.content.length > 0 
            ? note.content[0].text || '' 
            : 'Empty document';
        
        item.innerHTML = `
            <div class="note-item-title">${escapeHtml(note.title || 'Untitled')}</div>
            <div class="note-item-preview">${escapeHtml(preview.substring(0, 50))}</div>
            <div class="note-item-date">${formatDate(note.updated_at)}</div>
        `;
        
        item.addEventListener('click', () => openNote(note));
        notesList.appendChild(item);
    });
}

function createNewNote() {
    const note = {
        id: null,
        title: 'Untitled',
        content: [],
        client_id: currentClientId
    };
    
    openNote(note);
    
    // Create in backend
    fetch(`${API_BASE}/notes`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            title: 'Untitled',
            content: [],
            client_id: currentClientId
        })
    })
    .then(res => res.json())
    .then(data => {
        currentNote = data;
        loadNotes();
    })
    .catch(err => {
        console.error('Error creating note:', err);
    });
}

function openNote(note) {
    currentNote = note;
    noteBlocks = note.content || [];
    
    // Show editor
    document.getElementById('editorHeader').style.display = 'flex';
    document.getElementById('noteTitleInput').value = note.title || 'Untitled';
    
    // Render blocks
    renderEditor();
    
    // Update active note in list
    renderNotesList();
}

function renderEditor() {
    const editorContent = document.getElementById('editorContent');
    
    if (noteBlocks.length === 0) {
        // Add initial empty block
        noteBlocks = [{ id: generateBlockId(), type: 'paragraph', text: '' }];
    }
    
    editorContent.innerHTML = '';
    
    noteBlocks.forEach((block, index) => {
        const blockElement = createBlockElement(block, index);
        editorContent.appendChild(blockElement);
    });
    
    // Focus first block if empty
    if (noteBlocks.length === 1 && !noteBlocks[0].text) {
        const firstInput = editorContent.querySelector('.block-input');
        if (firstInput) firstInput.focus();
    }
}

function createBlockElement(block, index) {
    const blockDiv = document.createElement('div');
    blockDiv.className = 'content-block';
    blockDiv.setAttribute('data-type', block.type);
    blockDiv.setAttribute('data-index', index);
    blockDiv.setAttribute('data-block-id', block.id);
    
    if (block.type === 'todo') {
        blockDiv.setAttribute('data-checked', block.checked || false);
    }
    if (block.type === 'number') {
        blockDiv.setAttribute('data-number', index + 1);
    }
    
    const input = document.createElement('textarea');
    input.className = 'block-input';
    input.value = block.text || '';
    input.placeholder = getPlaceholderForType(block.type);
    
    // Auto-resize
    input.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
        block.text = this.value;
        saveCurrentNote();
    });
    
    // Handle Enter key
    input.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            createBlockAfter(index, block.type);
        } else if (e.key === 'Backspace' && this.value === '' && noteBlocks.length > 1) {
            e.preventDefault();
            deleteBlock(index);
        } else if (e.key === '/' && this.value === '') {
            e.preventDefault();
            showBlockMenu(blockDiv);
        }
    });
    
    // Handle slash command
    input.addEventListener('input', function() {
        if (this.value === '/') {
            showBlockMenu(blockDiv);
        }
    });
    
    // Toggle todo checkbox
    if (block.type === 'todo') {
        blockDiv.addEventListener('click', function(e) {
            if (e.target === blockDiv || e.target === input) return;
            toggleTodo(index);
        });
    }
    
    blockDiv.appendChild(input);
    
    // Auto-resize on load
    setTimeout(() => {
        input.style.height = 'auto';
        input.style.height = input.scrollHeight + 'px';
    }, 0);
    
    return blockDiv;
}

function getPlaceholderForType(type) {
    const placeholders = {
        'paragraph': 'Type "/" for commands',
        'h1': 'Heading 1',
        'h2': 'Heading 2',
        'h3': 'Heading 3',
        'bullet': 'List item',
        'number': 'Numbered item',
        'todo': 'Todo item',
        'quote': 'Quote'
    };
    return placeholders[type] || 'Type something...';
}

function createBlockAfter(index, type = 'paragraph') {
    const newBlock = {
        id: generateBlockId(),
        type: type,
        text: ''
    };
    
    noteBlocks.splice(index + 1, 0, newBlock);
    renderEditor();
    
    // Focus new block
    const newInput = document.querySelector(`[data-block-id="${newBlock.id}"] .block-input`);
    if (newInput) {
        newInput.focus();
    }
    
    saveCurrentNote();
}

function deleteBlock(index) {
    if (noteBlocks.length <= 1) return;
    
    noteBlocks.splice(index, 1);
    renderEditor();
    saveCurrentNote();
}

function toggleTodo(index) {
    if (noteBlocks[index].type === 'todo') {
        noteBlocks[index].checked = !noteBlocks[index].checked;
        renderEditor();
        saveCurrentNote();
    }
}

function showBlockMenu(blockElement) {
    // Remove existing menu
    const existingMenu = document.querySelector('.block-menu');
    if (existingMenu) existingMenu.remove();
    
    const menu = document.createElement('div');
    menu.className = 'block-menu active';
    
    const blockTypes = [
        { type: 'paragraph', icon: 'fa-align-left', title: 'Text', desc: 'Just start typing' },
        { type: 'h1', icon: 'fa-heading', title: 'Heading 1', desc: 'Big section heading' },
        { type: 'h2', icon: 'fa-heading', title: 'Heading 2', desc: 'Medium section heading' },
        { type: 'h3', icon: 'fa-heading', title: 'Heading 3', desc: 'Small section heading' },
        { type: 'bullet', icon: 'fa-list-ul', title: 'Bullet List', desc: 'Create a bullet list' },
        { type: 'number', icon: 'fa-list-ol', title: 'Numbered List', desc: 'Create a numbered list' },
        { type: 'todo', icon: 'fa-check-square', title: 'Todo', desc: 'Track a task' },
        { type: 'quote', icon: 'fa-quote-right', title: 'Quote', desc: 'Capture a quote' },
        { type: 'divider', icon: 'fa-minus', title: 'Divider', desc: 'Visual divider' }
    ];
    
    blockTypes.forEach(bt => {
        const item = document.createElement('div');
        item.className = 'block-menu-item';
        item.innerHTML = `
            <i class="fas ${bt.icon}"></i>
            <div>
                <div class="block-menu-item-title">${bt.title}</div>
            </div>
            <div class="block-menu-item-desc">${bt.desc}</div>
        `;
        item.addEventListener('click', () => {
            const index = parseInt(blockElement.getAttribute('data-index'));
            noteBlocks[index].type = bt.type;
            if (bt.type === 'divider') {
                noteBlocks[index].text = '';
            }
            renderEditor();
            saveCurrentNote();
            menu.remove();
        });
        menu.appendChild(item);
    });
    
    blockElement.appendChild(menu);
    
    // Close menu on outside click
    setTimeout(() => {
        document.addEventListener('click', function closeMenu(e) {
            if (!menu.contains(e.target) && e.target !== blockElement) {
                menu.remove();
                document.removeEventListener('click', closeMenu);
            }
        });
    }, 0);
}

function generateBlockId() {
    return 'block_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

async function saveCurrentNote() {
    if (!currentNote || !currentNote.id) return;
    
    try {
        const title = document.getElementById('noteTitleInput').value || 'Untitled';
        
        const response = await fetch(`${API_BASE}/notes/${currentNote.id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title,
                content: noteBlocks,
                client_id: currentClientId
            })
        });
        
        if (!response.ok) throw new Error('Failed to save note');
        
        const updated = await response.json();
        currentNote = updated;
        loadNotes();
    } catch (error) {
        console.error('Error saving note:', error);
    }
}

async function deleteCurrentNote() {
    if (!currentNote || !currentNote.id) {
        if (!confirm('Discard unsaved changes?')) return;
        closeEditor();
        return;
    }
    
    if (!confirm('Are you sure you want to delete this document?')) return;
    
    try {
        const response = await fetch(`${API_BASE}/notes/${currentNote.id}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete note');
        
        closeEditor();
        loadNotes();
    } catch (error) {
        console.error('Error deleting note:', error);
        showError('Failed to delete document');
    }
}

function closeEditor() {
    currentNote = null;
    noteBlocks = [];
    document.getElementById('editorHeader').style.display = 'none';
    document.getElementById('editorContent').innerHTML = `
        <div class="empty-editor">
            <i class="fas fa-file-alt"></i>
            <h3>Select a document or create a new one</h3>
            <p>Start typing to create content blocks</p>
        </div>
    `;
    renderNotesList();
}

// Update search to work with both views
const originalHandleSearch = handleSearch;
handleSearch = function() {
    if (currentView === 'tasks') {
        originalHandleSearch();
    } else {
        loadNotes();
    }
};

