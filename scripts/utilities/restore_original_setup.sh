#!/bin/bash

echo "Restoring original gunicorn setup..."

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOF'
echo "=== Restoring to original configuration ==="

# 1. Kill all gunicorn processes
echo "1. Stopping all gunicorn processes..."
pkill -f gunicorn
sleep 2

# 2. Remove the systemd service I created
echo "2. Removing systemd service..."
sudo rm -f /etc/systemd/system/chatmrpt.service
sudo systemctl daemon-reload

# 3. Remove the gunicorn config file I created
echo "3. Removing custom gunicorn config..."
cd /home/ec2-user/ChatMRPT
rm -f gunicorn_config.py

# 4. Start gunicorn the simple way
echo "4. Starting gunicorn with basic configuration..."
source /home/ec2-user/chatmrpt_env/bin/activate

# Use the most basic command
nohup gunicorn run:app --bind 0.0.0.0:8080 --workers 3 > gunicorn.log 2>&1 &

sleep 5

# 5. Verify it's running
echo ""
echo "5. Checking if gunicorn is running:"
ps aux | grep gunicorn | grep -v grep

# 6. Check listening port
echo ""
echo "6. Checking listening ports:"
sudo netstat -tlnp | grep 8080

# 7. Test local access
echo ""
echo "7. Testing local access:"
curl -I http://localhost:8080/

# 8. Check what was working before
echo ""
echo "8. Checking previous working configuration from logs:"
cd /home/ec2-user/ChatMRPT
echo "Looking for previous successful startup patterns..."
grep -B5 -A5 "Listening at" instance/app.log 2>/dev/null | tail -20 || echo "No app.log found"

# 9. Alternative: Try the deploy script that was probably used originally
echo ""
echo "9. Checking for original deployment scripts..."
ls -la | grep -E "deploy|start|run" | grep -v ".pyc"

EOF