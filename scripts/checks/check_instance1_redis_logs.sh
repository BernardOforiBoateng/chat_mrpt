#!/bin/bash

echo "=== Checking Instance 1 Redis Logs ==="
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Connect via staging
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

echo "Checking Instance 1 (172.31.44.52) Redis logs..."
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'LOGS'
echo "Last restart time:"
sudo systemctl status chatmrpt | grep "Active:" | head -1

echo ""
echo "Redis configuration in .env:"
grep -E "^REDIS" /home/ec2-user/ChatMRPT/.env

echo ""
echo "Last 20 lines mentioning Redis in logs:"
sudo journalctl -u chatmrpt | grep -i redis | tail -20

echo ""
echo "Any Redis errors in last 10 minutes:"
sudo journalctl -u chatmrpt --since "10 minutes ago" | grep -iE "redis|session" | grep -i error
LOGS

EOF