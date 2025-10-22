#!/bin/bash

echo "Investigating what changed with gunicorn configuration..."

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOF'
echo "=== Checking current gunicorn configuration ==="

# 1. Check how gunicorn is currently running
echo "1. Current gunicorn processes:"
ps aux | grep gunicorn | grep -v grep

# 2. Check the systemd service file I created
echo ""
echo "2. Systemd service configuration:"
cat /etc/systemd/system/chatmrpt.service | grep ExecStart

# 3. Check the gunicorn config file I created
echo ""
echo "3. Gunicorn config file:"
cd /home/ec2-user/ChatMRPT
cat gunicorn_config.py | grep bind

# 4. Stop the systemd service and run gunicorn the old way
echo ""
echo "4. Stopping systemd service and running gunicorn manually..."
sudo systemctl stop chatmrpt
sudo systemctl disable chatmrpt

# Kill any remaining gunicorn
pkill -f gunicorn

# Wait
sleep 2

# Run gunicorn the simple way it was probably running before
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo ""
echo "5. Starting gunicorn the original way:"
nohup gunicorn run:app --bind 0.0.0.0:8080 --workers 3 --timeout 300 > gunicorn.log 2>&1 &

sleep 3

# Check if it's running
echo ""
echo "6. Checking if gunicorn started:"
ps aux | grep gunicorn | grep -v grep

# Check listening ports
echo ""
echo "7. Checking listening ports:"
sudo netstat -tlnp | grep 8080

# Test it
echo ""
echo "8. Testing local access:"
curl -I http://localhost:8080/ping

# Check for ALB health checks in the next minute
echo ""
echo "9. Monitoring for ALB health checks (30 seconds):"
tail -f gunicorn.log | grep -E "ELB-HealthChecker|GET / |GET /ping" &
TAIL_PID=$!

sleep 30

kill $TAIL_PID 2>/dev/null

echo ""
echo "10. Checking recent access log:"
tail -n 20 gunicorn.log | grep -v DEBUG

EOF