# Gunicorn configuration file for Render deployment
# This file is automatically loaded by Gunicorn

import os

# Bind to the port provided by Render
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Worker configuration - using sync workers (simplest, most compatible)
worker_class = "sync"
workers = 1  # Single worker for memory efficiency on free tier
threads = 2  # Allow 2 threads per worker for concurrent requests

# CRITICAL: Timeout configuration (in seconds)
# This MUST be high enough for all 140 API calls to complete
timeout = 300  # 5 minutes
graceful_timeout = 60  # Time to finish ongoing requests during restart
keepalive = 5  # Keep connections alive for potential reuse

# Memory management
max_requests = 50  # Restart worker after 50 requests to prevent memory leaks
max_requests_jitter = 10  # Add randomness to prevent all workers restarting at once

# Logging
loglevel = "info"
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr

# Preload app for faster worker startup
preload_app = False  # Disabled for memory efficiency on free tier

# Print config on startup for debugging
print(f"=== GUNICORN CONFIG ===")
print(f"bind={bind}")
print(f"workers={workers}")
print(f"threads={threads}")
print(f"worker_class={worker_class}")
print(f"timeout={timeout}")
print(f"=======================")

