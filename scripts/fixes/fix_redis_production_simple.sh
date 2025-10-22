#!/bin/bash

echo "=== Fixing Redis Configuration on Production ==="
echo "This will update REDIS_HOST from staging to production endpoint"
echo ""

# First, we need to copy our key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Connect to staging first
echo "Step 1: Connecting to staging server..."
echo ""

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'
echo "Connected to staging server"
echo ""

# Ensure we have the key on staging
if [ ! -f ~/.ssh/chatmrpt-key.pem ]; then
    echo "Error: SSH key not found on staging. Please copy it first."
    exit 1
fi

echo "Step 2: Fixing Redis on Production Instance 1 (172.31.44.52)..."
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'INSTANCE1'
echo "Connected to Production Instance 1"
cd /home/ec2-user/ChatMRPT

# Backup .env
cp .env .env.backup.redis.$(date +%Y%m%d_%H%M%S)

# Fix REDIS_HOST
echo "Updating REDIS_HOST..."
sed -i 's|REDIS_HOST=chatmrpt-redis-staging\.1b3pmt\.0001\.use2\.cache\.amazonaws\.com|REDIS_HOST=chatmrpt-redis-production.1b3pmt.0001.use2.cache.amazonaws.com|' .env

# Ensure REDIS_ENABLED is true
if ! grep -q "REDIS_ENABLED=true" .env; then
    echo "REDIS_ENABLED=true" >> .env
fi

echo "Current Redis configuration:"
grep -E "REDIS_HOST|REDIS_URL|REDIS_ENABLED" .env

# Restart service
echo "Restarting service..."
sudo systemctl restart chatmrpt
sleep 3

echo "Service status:"
sudo systemctl is-active chatmrpt

echo "✅ Instance 1 complete"
INSTANCE1

echo ""
echo "Step 3: Fixing Redis on Production Instance 2 (172.31.43.200)..."
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.43.200 << 'INSTANCE2'
echo "Connected to Production Instance 2"
cd /home/ec2-user/ChatMRPT

# Backup .env
cp .env .env.backup.redis.$(date +%Y%m%d_%H%M%S)

# Fix REDIS_HOST
echo "Updating REDIS_HOST..."
sed -i 's|REDIS_HOST=chatmrpt-redis-staging\.1b3pmt\.0001\.use2\.cache\.amazonaws\.com|REDIS_HOST=chatmrpt-redis-production.1b3pmt.0001.use2.cache.amazonaws.com|' .env

# Ensure REDIS_ENABLED is true
if ! grep -q "REDIS_ENABLED=true" .env; then
    echo "REDIS_ENABLED=true" >> .env
fi

echo "Current Redis configuration:"
grep -E "REDIS_HOST|REDIS_URL|REDIS_ENABLED" .env

# Restart service
echo "Restarting service..."
sudo systemctl restart chatmrpt
sleep 3

echo "Service status:"
sudo systemctl is-active chatmrpt

echo "✅ Instance 2 complete"
INSTANCE2

echo ""
echo "Step 4: Testing Redis connectivity from Instance 1..."
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'TEST'
cd /home/ec2-user/ChatMRPT
python3 -c "
import redis
import os
from dotenv import load_dotenv

load_dotenv()

redis_host = os.getenv('REDIS_HOST', '')
print(f'Testing Redis at: {redis_host}')

try:
    r = redis.Redis(host=redis_host, port=6379, db=0, socket_timeout=5)
    r.ping()
    print('✅ Redis connection successful!')
    
    # Test write/read
    r.set('test_prod_fix', 'working', ex=60)
    val = r.get('test_prod_fix')
    if val == b'working':
        print('✅ Redis read/write working!')
except Exception as e:
    print(f'❌ Redis error: {e}')
"
TEST

echo ""
echo "==================================="
echo "✅ Redis Fix Complete!"
echo "==================================="
echo ""
echo "Both production instances now use:"
echo "  REDIS_HOST=chatmrpt-redis-production.1b3pmt.0001.use2.cache.amazonaws.com"
echo ""
echo "Services have been restarted."
echo "The option '2' selection issue should now be resolved!"

EOF