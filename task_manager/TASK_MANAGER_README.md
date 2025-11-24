# Task Manager Application

A comprehensive client-based task management system with AI integration, voice input, and automation capabilities.

## Features

### Core Features
- **Client-Based Organization**: Organize tasks by client with dedicated folders
- **Task Management**: Create, update, delete, and track tasks with status, priority, and due dates
- **Search & Filter**: Search tasks by keywords and filter by status, priority, and date range
- **Date Tracking**: Track tasks by creation date, due date, and completion date

### AI Features
- **AI Task Extraction**: Paste Grain call logs, emails, or any text to automatically extract actionable tasks
- **Voice Input**: Use voice commands to create tasks (e.g., "create a new task for X client and the task is create a new lead list in clay")
- **Smart Parsing**: AI-powered parsing of voice commands and text to extract task details

### Integration Features
- **Webhook Support**: Easy integration with external tools via webhooks
- **API Endpoints**: RESTful API for programmatic access
- **Operational Efficiency Search**: AI-powered recommendations for best practices and tools

## Installation

### Prerequisites
- Python 3.8+
- pip

### Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (optional but recommended):
```bash
# For AI features
export OPENAI_API_KEY="your-openai-api-key"

# For database (defaults to SQLite)
export DATABASE_URL="sqlite:///task_manager.db"

# For production
export SECRET_KEY="your-secret-key"
```

3. Initialize the database:
```bash
python task_manager.py
```

The database will be automatically created on first run.

## Usage

### Starting the Application

```bash
python task_manager.py
```

The application will start on `http://localhost:5001` by default.

### Accessing the Interface

Open your browser and navigate to:
```
http://localhost:5001/tasks
```

### Creating Clients

1. Click the "+" button next to "Clients" in the sidebar
2. Enter client name and description
3. Click "Save"

### Creating Tasks

**Method 1: Manual Creation**
1. Click "Add Task" button
2. Select client, enter task details
3. Set status, priority, and due date
4. Click "Save"

**Method 2: Voice Input**
1. Click the microphone button
2. Click "Click to Start Recording"
3. Speak your command (e.g., "create a new task for Client X and the task is create a new lead list in clay")
4. Click "Create Task" after review

**Method 3: AI Extraction**
1. Click "AI Extract" button
2. Select client (optional)
3. Paste your Grain call log, email, or any text
4. Click "Extract Tasks"
5. Review extracted tasks and click "Create Task" for each

### Searching and Filtering

- **Search**: Use the search box to find tasks by keywords
- **Status Filter**: Filter by pending, in progress, completed, or cancelled
- **Priority Filter**: Filter by low, medium, high, or urgent
- **Date Range**: Set start and end dates to filter by creation date

### Managing Tasks

- **Toggle Status**: Click the checkmark icon to mark tasks as completed
- **Edit**: Click the edit icon to modify task details
- **Delete**: Click the trash icon to delete tasks

## API Endpoints

### Clients
- `GET /api/clients` - Get all clients
- `POST /api/clients` - Create a new client
- `PUT /api/clients/<id>` - Update a client
- `DELETE /api/clients/<id>` - Delete a client

### Tasks
- `GET /api/tasks` - Get tasks (supports query parameters: client_id, status, priority, search, start_date, end_date)
- `POST /api/tasks` - Create a new task
- `PUT /api/tasks/<id>` - Update a task
- `DELETE /api/tasks/<id>` - Delete a task

### AI Features
- `POST /api/ai/extract-tasks` - Extract tasks from text
  ```json
  {
    "text": "Your text here",
    "client_name": "Optional client name"
  }
  ```

- `POST /api/ai/parse-voice` - Parse voice command
  ```json
  {
    "text": "Voice command text"
  }
  ```

### Integrations
- `GET /api/integrations` - Get all integrations
- `POST /api/integrations` - Create a new integration
  ```json
  {
    "name": "Webhook Name",
    "type": "webhook",
    "config": {
      "url": "https://your-webhook-url.com"
    },
    "enabled": true
  }
  ```

### Web Search
- `POST /api/web-search` - Get operational efficiency recommendations
  ```json
  {
    "query": "Your search query"
  }
  ```

## Integration Examples

### Webhook Integration

When tasks are created or updated, webhooks are automatically triggered:

```json
{
  "event": "task_created",
  "data": {
    "id": 1,
    "title": "Task title",
    "client_id": 1,
    "status": "pending",
    ...
  }
}
```

### Zapier Integration

1. Create a webhook integration in the app
2. Use the webhook URL in Zapier
3. Tasks will automatically sync to Zapier

### Custom Automation

Use the API to build custom integrations:

```python
import requests

# Create a task
response = requests.post('http://localhost:5001/api/tasks', json={
    'client_id': 1,
    'title': 'New task',
    'description': 'Task description',
    'priority': 'high',
    'status': 'pending'
})
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key for AI features
- `DATABASE_URL`: Database connection string (default: SQLite)
- `SECRET_KEY`: Flask secret key for sessions
- `PORT`: Port to run the application (default: 5001)

### Database

The application uses SQLAlchemy and supports:
- SQLite (default, for development)
- PostgreSQL (for production)
- MySQL (for production)

To use PostgreSQL:
```bash
export DATABASE_URL="postgresql://user:password@localhost/taskmanager"
```

## Troubleshooting

### Voice Recognition Not Working
- Ensure you're using a browser that supports Web Speech API (Chrome, Edge)
- Check microphone permissions in your browser
- Voice recognition requires HTTPS in production

### AI Features Not Working
- Verify your OpenAI API key is set correctly
- Check that you have API credits available
- The app will fall back to basic extraction if AI is unavailable

### Database Issues
- Ensure the database file/directory is writable
- For SQLite, check file permissions
- For PostgreSQL/MySQL, verify connection credentials

## Development

### Project Structure
```
.
├── task_manager.py          # Main application file
├── templates/
│   └── task_manager.html    # Frontend HTML
├── static/
│   ├── css/
│   │   └── task_manager.css # Styles
│   └── js/
│       └── task_manager.js  # Frontend JavaScript
├── requirements.txt         # Python dependencies
└── TASK_MANAGER_README.md    # This file
```

### Running in Development

```bash
python task_manager.py
```

### Running in Production

Use a production WSGI server like Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:5001 task_manager:app
```

## License

This project is part of the outreach reporting automation system.

## Support

For issues or questions, please check the codebase or create an issue in the repository.

