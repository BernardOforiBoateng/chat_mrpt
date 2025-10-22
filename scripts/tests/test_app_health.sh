#!/bin/bash

# Test application health

echo "Testing application health on AWS..."

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOF'
echo "=== Testing local application response ==="

# Test health endpoint
echo "1. Testing /ping endpoint:"
curl -v http://localhost:8080/ping 2>&1 | head -n 20

echo ""
echo "2. Testing root endpoint:"
curl -v http://localhost:8080/ 2>&1 | head -n 20

# Check for any recent errors
echo ""
echo "3. Checking for recent access logs:"
cd /home/ec2-user/ChatMRPT
tail -n 10 gunicorn.log

# Check security group and ALB target health
echo ""
echo "4. Checking network interfaces:"
ip addr show | grep inet

# Try restarting with explicit error logging
echo ""
echo "5. Restarting gunicorn with verbose logging..."
pkill -f gunicorn
sleep 2

cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

# Start with error logging to see any issues
nohup gunicorn 'run:app' --bind=0.0.0.0:8080 --timeout 300 --workers 3 --log-level debug --error-logfile gunicorn-error.log --access-logfile gunicorn-access.log > gunicorn.log 2>&1 &

sleep 5

# Check if it started
if pgrep -f gunicorn > /dev/null; then
    echo "✅ Gunicorn restarted successfully"
    
    # Test again
    echo ""
    echo "6. Testing application after restart:"
    curl -I http://localhost:8080/ping
else
    echo "❌ Failed to restart gunicorn"
    cat gunicorn-error.log 2>/dev/null || cat gunicorn.log
fi

EOF