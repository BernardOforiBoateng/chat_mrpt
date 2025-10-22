#!/bin/bash

echo "=== Verifying Redis Fix on Production ==="
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Connect via staging
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

echo "Checking Production Instance 1 (172.31.44.52)..."
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'CHECK1'
echo "Instance 1 Redis Config:"
grep -E "REDIS_HOST|REDIS_URL|REDIS_ENABLED" /home/ec2-user/ChatMRPT/.env | grep -v "^#"
echo ""
echo "Service Status:"
sudo systemctl is-active chatmrpt
echo ""
echo "Recent logs mentioning Redis:"
sudo journalctl -u chatmrpt --since "5 minutes ago" | grep -i redis | tail -5
CHECK1

echo ""
echo "-----------------------------------"
echo ""

echo "Checking Production Instance 2 (172.31.43.200)..."
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 << 'CHECK2'
echo "Instance 2 Redis Config:"
grep -E "REDIS_HOST|REDIS_URL|REDIS_ENABLED" /home/ec2-user/ChatMRPT/.env | grep -v "^#"
echo ""
echo "Service Status:"
sudo systemctl is-active chatmrpt
echo ""
echo "Recent logs mentioning Redis:"
sudo journalctl -u chatmrpt --since "5 minutes ago" | grep -i redis | tail -5
CHECK2

EOF

echo ""
echo "=== Verification Complete ==="
echo ""
echo "Both instances should now have:"
echo "  - REDIS_HOST pointing to production Redis"
echo "  - REDIS_ENABLED=true"
echo "  - Services running (active)"
echo ""
echo "The session state issue with option '2' should be resolved!"