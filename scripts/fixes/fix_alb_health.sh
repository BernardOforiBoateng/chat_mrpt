#!/bin/bash

echo "Fixing ALB health check and ensuring stable service..."

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOF'
echo "=== Ensuring stable ChatMRPT service ==="

# 1. Kill all existing gunicorn processes
echo "1. Stopping all gunicorn processes..."
pkill -f gunicorn
sleep 3

# 2. Clean up any stale pid files
cd /home/ec2-user/ChatMRPT
rm -f gunicorn.pid

# 3. Activate virtual environment
source /home/ec2-user/chatmrpt_env/bin/activate

# 4. Create a proper gunicorn config file
echo "2. Creating gunicorn configuration..."
cat > gunicorn_config.py << 'GCONFIG'
import multiprocessing

# Server socket
bind = "0.0.0.0:8080"
backlog = 2048

# Worker processes
workers = 3
worker_class = 'sync'
worker_connections = 1000
timeout = 300
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging
accesslog = '/home/ec2-user/ChatMRPT/gunicorn-access.log'
errorlog = '/home/ec2-user/ChatMRPT/gunicorn-error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'chatmrpt'

# Server mechanics
daemon = False
pidfile = '/home/ec2-user/ChatMRPT/gunicorn.pid'
user = None
group = None
tmp_upload_dir = None

# SSL - disabled for now as ALB handles it
keyfile = None
certfile = None
GCONFIG

# 5. Create a systemd service file for auto-restart
echo "3. Creating systemd service..."
sudo tee /etc/systemd/system/chatmrpt.service > /dev/null << 'SERVICE'
[Unit]
Description=ChatMRPT Gunicorn Application
After=network.target

[Service]
Type=notify
User=ec2-user
Group=ec2-user
WorkingDirectory=/home/ec2-user/ChatMRPT
Environment="PATH=/home/ec2-user/chatmrpt_env/bin"
ExecStart=/home/ec2-user/chatmrpt_env/bin/gunicorn --config gunicorn_config.py run:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE

# 6. Reload systemd and start the service
echo "4. Starting ChatMRPT service..."
sudo systemctl daemon-reload
sudo systemctl enable chatmrpt
sudo systemctl start chatmrpt

# 7. Wait for service to start
sleep 5

# 8. Check service status
echo ""
echo "5. Service status:"
sudo systemctl status chatmrpt --no-pager

# 9. Test the endpoints
echo ""
echo "6. Testing endpoints:"
echo "- Health check:"
curl -s -o /dev/null -w "  /ping: %{http_code}\n" http://localhost:8080/ping
echo "- Root:"
curl -s -o /dev/null -w "  /: %{http_code}\n" http://localhost:8080/

# 10. Show recent logs
echo ""
echo "7. Recent logs:"
sudo journalctl -u chatmrpt -n 20 --no-pager

# 11. Ensure port is open
echo ""
echo "8. Port status:"
sudo ss -tlnp | grep 8080

echo ""
echo "✅ Service configuration complete!"
echo "The application should now be accessible through the ALB."

EOF