"""
Optimized Gunicorn Configuration for Production
Phase 2: Application Optimization
Date: August 27, 2025
"""

import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8080"
backlog = 2048

# Worker processes
# Formula: 2-4 x CPU cores
# t3.large has 2 vCPUs, so 4-8 workers optimal
workers = int(os.environ.get('GUNICORN_WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = 'sync'  # Will change to 'gevent' for async if needed
worker_connections = 1000
max_requests = 1000  # Restart workers after this many requests to prevent memory leaks
max_requests_jitter = 50  # Randomize restart to prevent all workers restarting at once
timeout = 120  # Increased for complex analysis operations
graceful_timeout = 30
keepalive = 5

# Restart workers when code changes (development only)
reload = False

# Logging
accesslog = '/home/ec2-user/ChatMRPT/instance/logs/gunicorn-access.log'
errorlog = '/home/ec2-user/ChatMRPT/instance/logs/gunicorn-error.log'
loglevel = 'info'
access_log_format = '%(t)s %(h)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'chatmrpt-gunicorn'

# Server mechanics
daemon = False
pidfile = '/tmp/chatmrpt-gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# SSL (for future HTTPS)
# keyfile = '/path/to/keyfile'
# certfile = '/path/to/certfile'

# Worker lifecycle hooks
def when_ready(server):
    server.log.info("Server is ready. Spawning workers")

def worker_int(worker):
    worker.log.info("Worker received INT or QUIT signal")

def pre_fork(server, worker):
    server.log.info("Worker spawned (pid: %s)", worker.pid)

def pre_exec(server):
    server.log.info("Forked child, re-executing.")

def on_starting(server):
    server.log.info("ChatMRPT Gunicorn server is starting.")

def on_reload(server):
    server.log.info("ChatMRPT Gunicorn server is reloading.")

# Performance optimizations
def post_fork(server, worker):
    """
    Called just after a worker has been forked.
    """
    server.log.info("Worker spawned (pid: %s)", worker.pid)
    
    # Disconnect database connections to force reconnection in worker
    from app import create_app
    app = create_app()
    with app.app_context():
        from app.models import db
        db.session.remove()
        db.engine.dispose()

# StatsD integration (optional, for monitoring)
# statsd_host = 'localhost:8125'
# statsd_prefix = 'chatmrpt'