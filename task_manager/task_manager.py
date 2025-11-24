#!/usr/bin/env python3
"""
Task Management Application
Flask web application for client-based task tracking with AI integration
"""

import os
import json
import logging
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from dateutil import parser as date_parser
import requests
import re

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app
# Set template and static folders relative to this file's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
DB_PATH = os.path.join(BASE_DIR, 'task_manager.db')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', f'sqlite:///{DB_PATH}')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)

# AI configuration - using built-in logic (no OpenAI required)
openai_client = None  # Set to None to use built-in AI


# Database Models
class Client(db.Model):
    """Client model for organizing tasks"""
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    tasks = db.relationship('Task', backref='client', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'task_count': len(self.tasks)
        }


class Task(db.Model):
    """Task model"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')  # pending, in_progress, completed, cancelled
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    due_date = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = db.Column(db.Text)  # JSON array of tags
    extra_data = db.Column(db.Text)  # JSON for additional data (renamed from metadata to avoid SQLAlchemy conflict)
    
    # Foreign key
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'priority': self.priority,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tags': json.loads(self.tags) if self.tags else [],
            'metadata': json.loads(self.extra_data) if self.extra_data else {},
            'client_id': self.client_id,
            'client_name': self.client.name if self.client else None
        }


class Note(db.Model):
    """Note/Document model for free-form typing (Notion-like)"""
    __tablename__ = 'notes'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500))
    content = db.Column(db.Text)  # JSON array of content blocks
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    client = db.relationship('Client', backref='notes', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': json.loads(self.content) if self.content else [],
            'client_id': self.client_id,
            'client_name': self.client.name if self.client else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class Integration(db.Model):
    """Integration model for external tool connections"""
    __tablename__ = 'integrations'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # webhook, api, zapier, etc.
    config = db.Column(db.Text)  # JSON configuration
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'config': json.loads(self.config) if self.config else {},
            'enabled': self.enabled,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


# AI Service
class AIService:
    """Service for AI-powered task extraction and processing"""
    
    @staticmethod
    def extract_tasks_from_text(text, client_name=None):
        """Extract tasks from text using OpenAI"""
        if not openai_client:
            logger.warning("OpenAI API key not set, using basic extraction")
            return AIService._basic_extraction(text, client_name)
        
        try:
            prompt = f"""Analyze the following text and extract all actionable tasks. 
For each task, provide:
1. A clear, concise title
2. A brief description
3. Priority level (low, medium, high, urgent)
4. Any relevant due dates mentioned

Text to analyze:
{text}

{f"Note: These tasks are for client: {client_name}" if client_name else ""}

Return a JSON array of tasks in this format:
[
  {{
    "title": "Task title",
    "description": "Task description",
    "priority": "medium",
    "due_date": "YYYY-MM-DD or null"
  }}
]"""

            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a task extraction assistant. Extract actionable tasks from text and return them as JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            # Extract JSON from response
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            tasks = json.loads(content)
            return tasks if isinstance(tasks, list) else [tasks]
            
        except Exception as e:
            logger.error(f"Error in AI extraction: {e}")
            return AIService._basic_extraction(text, client_name)
    
    @staticmethod
    def _basic_extraction(text, client_name=None):
        """Enhanced task extraction without external AI"""
        tasks = []
        lines = text.split('\n')
        current_task = None
        
        # Task indicators
        task_indicators = [
            'todo', 'task', 'need to', 'should', 'must', 'action', 'action item',
            'follow up', 'follow-up', 'next steps', 'actionable', 'do this',
            'create', 'build', 'implement', 'set up', 'setup', 'prepare',
            'send', 'email', 'call', 'meeting', 'schedule', 'review', 'update'
        ]
        
        # Priority indicators
        priority_keywords = {
            'urgent': ['urgent', 'asap', 'immediately', 'critical', 'emergency'],
            'high': ['important', 'high priority', 'priority', 'soon', 'quickly'],
            'low': ['low priority', 'when possible', 'eventually', 'nice to have']
        }
        
        # Date patterns
        date_pattern = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{4})\b'
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line or len(line) < 3:
                if current_task:
                    tasks.append(current_task)
                    current_task = None
                continue
            
            line_lower = line.lower()
            
            # Check if this line starts a new task
            is_task_start = any(indicator in line_lower for indicator in task_indicators)
            is_bullet_point = line.startswith(('-', '*', '•', '1.', '2.', '3.', '4.', '5.'))
            is_numbered = re.match(r'^\d+[\.\)]\s+', line)
            
            if (is_task_start or is_bullet_point or is_numbered) and not current_task:
                # Start new task
                # Extract priority
                priority = 'medium'
                for prio, keywords in priority_keywords.items():
                    if any(kw in line_lower for kw in keywords):
                        priority = prio
                        break
                
                # Extract date
                due_date = None
                date_match = re.search(date_pattern, line, re.IGNORECASE)
                if date_match:
                    try:
                        due_date = date_parser.parse(date_match.group(1)).strftime('%Y-%m-%d')
                    except:
                        pass
                
                # Clean title (remove bullet points, numbers)
                title = re.sub(r'^[-*•]\s+', '', line)
                title = re.sub(r'^\d+[\.\)]\s+', '', title)
                title = title.strip()
                
                current_task = {
                    'title': title[:200] if len(title) > 200 else title,
                    'description': title,
                    'priority': priority,
                    'due_date': due_date
                }
            elif current_task:
                # Continue current task
                # Check for date in continuation
                if not current_task.get('due_date'):
                    date_match = re.search(date_pattern, line, re.IGNORECASE)
                    if date_match:
                        try:
                            current_task['due_date'] = date_parser.parse(date_match.group(1)).strftime('%Y-%m-%d')
                        except:
                            pass
                
                current_task['description'] += '\n' + line
                
                # If line is too long or seems like a new section, finalize task
                if len(line) > 100 or (i < len(lines) - 1 and lines[i+1].strip() and 
                                      any(ind in lines[i+1].strip().lower() for ind in task_indicators)):
                    tasks.append(current_task)
                    current_task = None
        
        if current_task:
            tasks.append(current_task)
        
        # If no tasks found, try to split by sentences or create one task
        if not tasks:
            # Try to find action items in sentences
            sentences = re.split(r'[.!?]\s+', text)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 10 and any(ind in sentence.lower() for ind in task_indicators):
                    priority = 'medium'
                    for prio, keywords in priority_keywords.items():
                        if any(kw in sentence.lower() for kw in keywords):
                            priority = prio
                            break
                    
                    tasks.append({
                        'title': sentence[:200] if len(sentence) > 200 else sentence,
                        'description': sentence,
                        'priority': priority,
                        'due_date': None
                    })
            
            # If still no tasks, create one from the whole text
            if not tasks:
                tasks.append({
                    'title': text[:200] if len(text) > 200 else text,
                    'description': text,
                    'priority': 'medium',
                    'due_date': None
                })
        
        return tasks
    
    @staticmethod
    def parse_voice_command(voice_text):
        """Parse voice command to extract task information"""
        if not openai_client:
            return AIService._basic_voice_parse(voice_text)
        
        try:
            prompt = f"""Parse the following voice command and extract task information:
"{voice_text}"

Extract:
1. Client name (if mentioned)
2. Task title
3. Task description
4. Priority (if mentioned)
5. Due date (if mentioned)

Return JSON in this format:
{{
  "client_name": "Client name or null",
  "title": "Task title",
  "description": "Task description",
  "priority": "medium",
  "due_date": "YYYY-MM-DD or null"
}}"""

            response = openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a voice command parser. Extract task information from natural language commands."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()
            
            return json.loads(content)
            
        except Exception as e:
            logger.error(f"Error in voice parsing: {e}")
            return AIService._basic_voice_parse(voice_text)
    
    @staticmethod
    def _basic_voice_parse(voice_text):
        """Enhanced voice parsing without external AI"""
        text_lower = voice_text.lower()
        client_name = None
        title = voice_text
        priority = 'medium'
        due_date = None
        
        # Extract client name patterns - more flexible
        # Pattern: "for X client" or "for client X" or "under X"
        client_patterns = [
            r'for\s+([A-Z][a-zA-Z0-9\s]+?)(?:\s+client|\s+and|\s+the\s+task)',  # "for Client X and the task"
            r'for\s+client\s+([A-Z][a-zA-Z0-9\s]+?)(?:\s+and|\s+the\s+task)',  # "for client X and"
            r'under\s+([A-Z][a-zA-Z0-9\s]+?)(?:\s+client|\s+and|\s+the\s+task)',  # "under X"
        ]
        
        for pattern in client_patterns:
            match = re.search(pattern, voice_text, re.IGNORECASE)
            if match:
                client_name = match.group(1).strip()
                # Remove client name from title
                title = re.sub(pattern, '', voice_text, flags=re.IGNORECASE).strip()
                break
        
        # Fallback: look for "for X" pattern
        if not client_name:
            match = re.search(r'for\s+([A-Z][a-zA-Z0-9\s]{2,20}?)(?:\s+and)', voice_text, re.IGNORECASE)
            if match:
                client_name = match.group(1).strip()
                title = re.sub(r'for\s+' + re.escape(client_name) + r'\s+and', '', voice_text, flags=re.IGNORECASE).strip()
        
        # Extract priority
        if any(word in text_lower for word in ['urgent', 'asap', 'immediately', 'critical']):
            priority = 'urgent'
        elif any(word in text_lower for word in ['important', 'high priority', 'priority']):
            priority = 'high'
        elif any(word in text_lower for word in ['low priority', 'when possible']):
            priority = 'low'
        
        # Extract date
        date_pattern = r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{4}|today|tomorrow|next week|next month)\b'
        date_match = re.search(date_pattern, text_lower)
        if date_match:
            date_str = date_match.group(1)
            if date_str == 'today':
                due_date = datetime.now().strftime('%Y-%m-%d')
            elif date_str == 'tomorrow':
                due_date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            elif date_str == 'next week':
                due_date = (datetime.now() + timedelta(weeks=1)).strftime('%Y-%m-%d')
            elif date_str == 'next month':
                due_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
            else:
                try:
                    due_date = date_parser.parse(date_str).strftime('%Y-%m-%d')
                except:
                    pass
        
        # Clean up title - remove common voice command phrases
        title = re.sub(r'^(create|add|make|new)\s+(a\s+)?(task|todo)\s+', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s+and\s+the\s+task\s+is\s+', ' ', title, flags=re.IGNORECASE)
        title = title.strip()
        
        if not title:
            title = voice_text
        
        return {
            'client_name': client_name,
            'title': title,
            'description': voice_text,
            'priority': priority,
            'due_date': due_date
        }


# API Routes
@app.route('/tasks')
def tasks_index():
    """Render task management interface"""
    return render_template('task_manager.html')


@app.route('/api/clients', methods=['GET'])
def get_clients():
    """Get all clients"""
    try:
        clients = Client.query.order_by(Client.name).all()
        return jsonify([client.to_dict() for client in clients])
    except Exception as e:
        logger.error(f"Error fetching clients: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/clients', methods=['POST'])
def create_client():
    """Create a new client"""
    try:
        data = request.get_json()
        name = data.get('name')
        if not name:
            return jsonify({'error': 'Client name is required'}), 400
        
        # Check if client already exists
        existing = Client.query.filter_by(name=name).first()
        if existing:
            return jsonify({'error': 'Client with this name already exists'}), 400
        
        client = Client(
            name=name,
            description=data.get('description', '')
        )
        db.session.add(client)
        db.session.commit()
        
        return jsonify(client.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating client: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/clients/<int:client_id>', methods=['PUT'])
def update_client(client_id):
    """Update a client"""
    try:
        client = Client.query.get_or_404(client_id)
        data = request.get_json()
        
        if 'name' in data:
            client.name = data['name']
        if 'description' in data:
            client.description = data['description']
        
        client.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(client.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating client: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
def delete_client(client_id):
    """Delete a client"""
    try:
        client = Client.query.get_or_404(client_id)
        db.session.delete(client)
        db.session.commit()
        return jsonify({'message': 'Client deleted successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting client: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    """Get tasks with filtering and search"""
    try:
        query = Task.query
        
        # Filter by client
        client_id = request.args.get('client_id')
        if client_id:
            query = query.filter_by(client_id=client_id)
        
        # Filter by status
        status = request.args.get('status')
        if status:
            query = query.filter_by(status=status)
        
        # Filter by priority
        priority = request.args.get('priority')
        if priority:
            query = query.filter_by(priority=priority)
        
        # Search by keyword
        search = request.args.get('search')
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                db.or_(
                    Task.title.like(search_term),
                    Task.description.like(search_term)
                )
            )
        
        # Filter by date range
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if start_date:
            try:
                start_dt = date_parser.parse(start_date)
                query = query.filter(Task.created_at >= start_dt)
            except:
                pass
        if end_date:
            try:
                end_dt = date_parser.parse(end_date)
                query = query.filter(Task.created_at <= end_dt)
            except:
                pass
        
        # Sort
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        if hasattr(Task, sort_by):
            if sort_order == 'desc':
                query = query.order_by(getattr(Task, sort_by).desc())
            else:
                query = query.order_by(getattr(Task, sort_by).asc())
        
        tasks = query.all()
        return jsonify([task.to_dict() for task in tasks])
    except Exception as e:
        logger.error(f"Error fetching tasks: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tasks', methods=['POST'])
def create_task():
    """Create a new task"""
    try:
        data = request.get_json()
        
        if not data.get('title'):
            return jsonify({'error': 'Task title is required'}), 400
        
        client_id = data.get('client_id')
        if not client_id:
            return jsonify({'error': 'Client ID is required'}), 400
        
        # Verify client exists
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        # Parse due date if provided
        due_date = None
        if data.get('due_date'):
            try:
                due_date = date_parser.parse(data.get('due_date'))
            except:
                pass
        
        task = Task(
            title=data['title'],
            description=data.get('description', ''),
            status=data.get('status', 'pending'),
            priority=data.get('priority', 'medium'),
            due_date=due_date,
            client_id=client_id,
            tags=json.dumps(data.get('tags', [])),
            extra_data=json.dumps(data.get('metadata', {}))
        )
        
        db.session.add(task)
        db.session.commit()
        
        # Trigger integrations
        _trigger_integrations('task_created', task.to_dict())
        
        return jsonify(task.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating task: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Update a task"""
    try:
        task = Task.query.get_or_404(task_id)
        data = request.get_json()
        
        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = data['status']
            if data['status'] == 'completed' and not task.completed_at:
                task.completed_at = datetime.utcnow()
            elif data['status'] != 'completed':
                task.completed_at = None
        if 'priority' in data:
            task.priority = data['priority']
        if 'due_date' in data:
            if data['due_date']:
                try:
                    task.due_date = date_parser.parse(data['due_date'])
                except:
                    pass
            else:
                task.due_date = None
        if 'tags' in data:
            task.tags = json.dumps(data['tags'])
        if 'metadata' in data:
            task.extra_data = json.dumps(data['metadata'])
        
        task.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Trigger integrations
        _trigger_integrations('task_updated', task.to_dict())
        
        return jsonify(task.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating task: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Delete a task"""
    try:
        task = Task.query.get_or_404(task_id)
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': 'Task deleted successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting task: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/extract-tasks', methods=['POST'])
def extract_tasks():
    """Extract tasks from text (email, call log, etc.)"""
    try:
        data = request.get_json()
        text = data.get('text')
        client_name = data.get('client_name')
        
        if not text:
            return jsonify({'error': 'Text is required'}), 400
        
        # Extract tasks using AI
        extracted_tasks = AIService.extract_tasks_from_text(text, client_name)
        
        return jsonify({'tasks': extracted_tasks})
    except Exception as e:
        logger.error(f"Error extracting tasks: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/ai/parse-voice', methods=['POST'])
def parse_voice():
    """Parse voice command to create task"""
    try:
        data = request.get_json()
        voice_text = data.get('text')
        
        if not voice_text:
            return jsonify({'error': 'Voice text is required'}), 400
        
        # Parse voice command
        parsed = AIService.parse_voice_command(voice_text)
        
        return jsonify(parsed)
    except Exception as e:
        logger.error(f"Error parsing voice: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations', methods=['GET'])
def get_integrations():
    """Get all integrations"""
    try:
        integrations = Integration.query.all()
        return jsonify([integration.to_dict() for integration in integrations])
    except Exception as e:
        logger.error(f"Error fetching integrations: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/integrations', methods=['POST'])
def create_integration():
    """Create a new integration"""
    try:
        data = request.get_json()
        
        integration = Integration(
            name=data.get('name'),
            type=data.get('type'),
            config=json.dumps(data.get('config', {})),
            enabled=data.get('enabled', True)
        )
        
        db.session.add(integration)
        db.session.commit()
        
        return jsonify(integration.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating integration: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes', methods=['GET'])
def get_notes():
    """Get notes/documents with filtering"""
    try:
        query = Note.query
        
        # Filter by client
        client_id = request.args.get('client_id')
        if client_id:
            query = query.filter_by(client_id=client_id)
        
        # Search by keyword
        search = request.args.get('search')
        if search:
            search_term = f'%{search}%'
            query = query.filter(
                db.or_(
                    Note.title.like(search_term),
                    Note.content.like(search_term)
                )
            )
        
        # Sort by updated date
        query = query.order_by(Note.updated_at.desc())
        
        notes = query.all()
        return jsonify([note.to_dict() for note in notes])
    except Exception as e:
        logger.error(f"Error fetching notes: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes', methods=['POST'])
def create_note():
    """Create a new note/document"""
    try:
        data = request.get_json()
        
        note = Note(
            title=data.get('title', 'Untitled'),
            content=json.dumps(data.get('content', [])),
            client_id=data.get('client_id')
        )
        
        db.session.add(note)
        db.session.commit()
        
        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating note: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a note/document"""
    try:
        note = Note.query.get_or_404(note_id)
        data = request.get_json()
        
        if 'title' in data:
            note.title = data['title']
        if 'content' in data:
            note.content = json.dumps(data['content'])
        if 'client_id' in data:
            note.client_id = data['client_id']
        
        note.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify(note.to_dict())
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating note: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a note/document"""
    try:
        note = Note.query.get_or_404(note_id)
        db.session.delete(note)
        db.session.commit()
        return jsonify({'message': 'Note deleted successfully'})
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting note: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/web-search', methods=['POST'])
def web_search():
    """Search the web for operational efficiency features and best practices"""
    try:
        data = request.get_json()
        query = data.get('query')
        
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        # Use enhanced built-in logic for recommendations
        # (OpenAI can be added later if needed)
        if False:  # Disabled OpenAI, using built-in logic
            try:
                prompt = f"""Based on the following task management query, provide best practices and operational efficiency recommendations:
Query: {query}

Provide:
1. Best practices for this type of task
2. Tools or integrations that could help
3. Automation opportunities
4. Time-saving tips

Format as JSON with keys: best_practices, recommended_tools, automation_ideas, tips"""

                response = openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are an operational efficiency consultant. Provide actionable recommendations."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5
                )
                
                content = response.choices[0].message.content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                recommendations = json.loads(content)
                
                return jsonify({
                    'query': query,
                    'recommendations': recommendations,
                    'source': 'ai_enhanced'
                })
            except Exception as e:
                logger.error(f"Error in AI web search: {e}")
        
        # Enhanced built-in recommendations based on query
        query_lower = query.lower()
        recommendations = {
            'best_practices': [
                'Break down large tasks into smaller, actionable items',
                'Set clear priorities and deadlines',
                'Use automation tools where possible',
                'Regularly review and update task status'
            ],
            'recommended_tools': [
                'Zapier for automation',
                'Slack for team communication',
                'Google Calendar for scheduling',
                'Trello/Asana for project management'
            ],
            'automation_ideas': [
                'Automate task creation from emails',
                'Set up recurring task templates',
                'Integrate with calendar for deadline reminders'
            ],
            'tips': [
                'Use voice input for quick task capture',
                'Batch similar tasks together',
                'Review tasks daily for prioritization'
            ]
        }
        
        # Context-aware recommendations
        if 'email' in query_lower or 'outreach' in query_lower:
            recommendations['recommended_tools'].extend(['Mailchimp', 'SendGrid', 'HubSpot'])
            recommendations['automation_ideas'].append('Set up email templates for common tasks')
        
        if 'lead' in query_lower or 'prospect' in query_lower:
            recommendations['recommended_tools'].extend(['Clay', 'Apollo', 'LinkedIn Sales Navigator'])
            recommendations['tips'].append('Use lead enrichment tools to gather more information')
        
        if 'calendar' in query_lower or 'meeting' in query_lower:
            recommendations['recommended_tools'].extend(['Calendly', 'Google Calendar', 'Outlook'])
            recommendations['automation_ideas'].append('Auto-schedule follow-up tasks after meetings')
        
        if 'client' in query_lower or 'customer' in query_lower:
            recommendations['best_practices'].append('Maintain separate task lists per client')
            recommendations['tips'].append('Use client folders to organize related tasks')
        
        return jsonify({
            'query': query,
            'recommendations': recommendations,
            'source': 'built_in_ai'
        })
    except Exception as e:
        logger.error(f"Error in web search: {e}")
        return jsonify({'error': str(e)}), 500


def _trigger_integrations(event_type, data):
    """Trigger webhooks and integrations"""
    try:
        integrations = Integration.query.filter_by(enabled=True).all()
        for integration in integrations:
            config = json.loads(integration.config) if integration.config else {}
            if integration.type == 'webhook' and config.get('url'):
                try:
                    import requests
                    requests.post(
                        config['url'],
                        json={'event': event_type, 'data': data},
                        timeout=5
                    )
                except Exception as e:
                    logger.error(f"Error triggering webhook {integration.name}: {e}")
    except Exception as e:
        logger.error(f"Error triggering integrations: {e}")


# Initialize database
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    # Create database tables
    with app.app_context():
        db.create_all()
    
    port = int(os.environ.get('PORT', 5001))
    app.run(debug=True, host='0.0.0.0', port=port)

