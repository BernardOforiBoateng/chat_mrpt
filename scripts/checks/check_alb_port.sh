#!/bin/bash

echo "Checking which port the ALB expects..."

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOF'
echo "=== Checking ALB expectations ==="

# 1. Check if anything is listening on port 80
echo "1. Checking port 80:"
sudo netstat -tlnp | grep -E ":80\s"

# 2. Try starting gunicorn on port 80 (requires sudo)
echo ""
echo "2. Testing if ALB might be expecting port 80..."
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

# Stop current gunicorn
pkill -f gunicorn
sleep 2

# Try port 80 (common ALB default)
echo "Starting gunicorn on port 80..."
sudo /home/ec2-user/chatmrpt_env/bin/gunicorn run:app --bind 0.0.0.0:80 --workers 3 --timeout 300 &

sleep 5

# Check if it started
echo ""
echo "3. Checking if gunicorn is running on port 80:"
sudo netstat -tlnp | grep -E ":80\s"

# Monitor for ALB health checks
echo ""
echo "4. Monitoring for ALB health checks on port 80 (waiting 30 seconds):"
sudo tail -f /var/log/messages | grep -E "GET|POST|HEAD" &
TAIL_PID=$!

sleep 30

sudo kill $TAIL_PID 2>/dev/null

# If no luck, try the original port but with different health check path
echo ""
echo "5. Stopping port 80 and trying port 8080 again..."
sudo pkill -f gunicorn
sleep 2

# Start on 8080 with access logging to stdout
nohup gunicorn run:app --bind 0.0.0.0:8080 --workers 3 --timeout 300 --access-logfile - --error-logfile - 2>&1 | tee gunicorn-live.log &

echo ""
echo "6. Waiting for any incoming requests (30 seconds):"
sleep 30

# Check what we got
echo ""
echo "7. Checking for any requests:"
grep -E "GET|POST|HEAD" gunicorn-live.log | tail -20

# Also check system logs for any clues
echo ""
echo "8. Checking system logs for network issues:"
sudo journalctl -u amazon-ssm-agent -n 20 --no-pager 2>/dev/null || echo "No SSM agent logs"

EOF