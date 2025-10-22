#!/bin/bash

# SSH into AWS and restart the service

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOF'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

# Kill existing gunicorn processes
echo "Stopping gunicorn..."
pkill -f gunicorn

# Wait a moment
sleep 2

# Start gunicorn
echo "Starting gunicorn..."
nohup gunicorn 'run:app' --bind=0.0.0.0:8080 --timeout 300 --workers 3 > gunicorn.log 2>&1 &

# Wait for startup
sleep 3

# Check if running
if pgrep -f gunicorn > /dev/null; then
    echo "✅ Gunicorn restarted successfully"
    
    # Show recent logs
    echo ""
    echo "Recent logs:"
    tail -n 20 gunicorn.log
else
    echo "❌ Failed to start gunicorn"
    echo "Error logs:"
    tail -n 50 gunicorn.log
fi
EOF