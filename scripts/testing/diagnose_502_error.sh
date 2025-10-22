#!/bin/bash

# Diagnose 502 Bad Gateway error

echo "Diagnosing 502 Bad Gateway error on AWS..."

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOF'
echo "=== Checking system status ==="

# Check if gunicorn is running
echo ""
echo "1. Checking gunicorn processes:"
pgrep -f gunicorn
if pgrep -f gunicorn > /dev/null; then
    echo "✅ Gunicorn processes found"
    ps aux | grep gunicorn | grep -v grep
else
    echo "❌ No gunicorn processes running!"
fi

# Check port 8080
echo ""
echo "2. Checking port 8080:"
sudo netstat -tlnp | grep 8080 || echo "Port 8080 not listening"

# Check recent logs
echo ""
echo "3. Recent gunicorn logs:"
cd /home/ec2-user/ChatMRPT
if [ -f gunicorn.log ]; then
    tail -n 50 gunicorn.log
else
    echo "No gunicorn.log file found"
fi

# Check for Python errors
echo ""
echo "4. Checking for Python errors:"
if [ -f instance/app.log ]; then
    tail -n 20 instance/app.log | grep -i error || echo "No recent errors in app.log"
fi

# Check disk space
echo ""
echo "5. Checking disk space:"
df -h

# Check memory
echo ""
echo "6. Checking memory:"
free -m

# Try to start gunicorn if not running
if ! pgrep -f gunicorn > /dev/null; then
    echo ""
    echo "7. Attempting to start gunicorn..."
    cd /home/ec2-user/ChatMRPT
    source /home/ec2-user/chatmrpt_env/bin/activate
    
    # First try to run the app directly to see any errors
    echo "Testing app startup..."
    python -c "from run import app; print('App imported successfully')" 2>&1
    
    # Try to start gunicorn
    echo ""
    echo "Starting gunicorn..."
    gunicorn 'run:app' --bind=0.0.0.0:8080 --timeout 300 --workers 3 --log-level debug 2>&1 | head -n 50
fi

EOF