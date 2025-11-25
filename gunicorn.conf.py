# Gunicorn configuration file for Render deployment
# This file is automatically loaded by Gunicorn

import os

# Bind to the port provided by Render
bind = f"0.0.0.0:{os.environ.get('PORT', '10000')}"

# Worker configuration
# Using gevent for async I/O - better for API-heavy applications
worker_class = "gevent"
workers = 1  # Single worker for memory efficiency on free tier
worker_connections = 100  # Max concurrent connections per worker

# Timeout configuration (in seconds)
# Critical for long-running API requests
timeout = 300  # 5 minutes - allows for ~140 API calls at 2 sec each
graceful_timeout = 30  # Time to finish ongoing requests during restart
keepalive = 5  # Keep connections alive for potential reuse

# Memory management
max_requests = 100  # Restart worker after 100 requests to prevent memory leaks
max_requests_jitter = 10  # Add randomness to prevent all workers restarting at once

# Logging
loglevel = "info"
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr

# Preload app for faster worker startup (but uses more memory initially)
preload_app = False  # Disabled for memory efficiency on free tier

# Print config on startup for debugging
print(f"Gunicorn Config: bind={bind}, workers={workers}, worker_class={worker_class}, timeout={timeout}")

