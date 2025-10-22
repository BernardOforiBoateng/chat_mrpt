#!/bin/bash

echo "=== Fixing Redis on Production Instance 2 ==="
echo "Instance 2 is missing REDIS_HOST configuration"
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Connect via staging to Instance 2
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

echo "Connecting to Production Instance 2 (172.31.43.200)..."
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 << 'FIX'
echo "Connected to Instance 2"
cd /home/ec2-user/ChatMRPT

echo ""
echo "Current .env Redis config:"
grep -E "REDIS" .env | head -10

echo ""
echo "Adding missing REDIS_HOST configuration..."

# Check if REDIS_HOST exists
if ! grep -q "^REDIS_HOST=" .env; then
    echo "Adding REDIS_HOST..."
    echo "REDIS_HOST=chatmrpt-redis-production.1b3pmt.0001.use2.cache.amazonaws.com" >> .env
else
    echo "Updating existing REDIS_HOST..."
    sed -i 's|^REDIS_HOST=.*|REDIS_HOST=chatmrpt-redis-production.1b3pmt.0001.use2.cache.amazonaws.com|' .env
fi

# Also add REDIS_PORT if missing
if ! grep -q "^REDIS_PORT=" .env; then
    echo "Adding REDIS_PORT..."
    echo "REDIS_PORT=6379" >> .env
fi

echo ""
echo "Updated .env Redis config:"
grep -E "^REDIS_HOST|^REDIS_PORT|^REDIS_URL|^REDIS_ENABLED" .env

echo ""
echo "Restarting service..."
sudo systemctl restart chatmrpt
sleep 5

echo ""
echo "Checking service status..."
sudo systemctl is-active chatmrpt

echo ""
echo "Checking Redis connection in logs..."
sudo journalctl -u chatmrpt --since "1 minute ago" | grep -i redis | tail -10

echo ""
echo "✅ Instance 2 Redis configuration fixed!"
FIX

EOF

echo ""
echo "=== Fix Complete ==="
echo "Instance 2 now has proper REDIS_HOST configuration"
echo "The session state issue should be fully resolved now!"