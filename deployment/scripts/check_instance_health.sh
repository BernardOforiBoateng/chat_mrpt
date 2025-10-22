#!/bin/bash
# Check health of a specific instance

INSTANCE_IP=$1

if [ -z "$INSTANCE_IP" ]; then
    echo "Usage: $0 <instance_ip>"
    exit 1
fi

echo "Checking health of $INSTANCE_IP..."

# Check if we can SSH
if ssh -i ~/.ssh/chatmrpt-key.pem -o ConnectTimeout=5 -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP "echo 'SSH OK'" > /dev/null 2>&1; then
    echo "✅ SSH connection successful"
else
    echo "❌ SSH connection failed"
    return 1
fi

# Check service status
SERVICE_STATUS=$(ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP "sudo systemctl is-active chatmrpt" 2>/dev/null)

if [ "$SERVICE_STATUS" = "active" ]; then
    echo "✅ ChatMRPT service is active"
else
    echo "❌ ChatMRPT service is not active: $SERVICE_STATUS"
    return 1
fi

# Check worker count
WORKER_COUNT=$(ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP "ps aux | grep gunicorn | grep -v grep | wc -l" 2>/dev/null)

echo "✅ Worker count: $WORKER_COUNT"

# Check Redis connectivity
REDIS_CHECK=$(ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    ec2-user@$INSTANCE_IP << 'CHECK_REDIS'
cd /home/ec2-user/ChatMRPT
source chatmrpt_env/bin/activate 2>/dev/null || source venv/bin/activate 2>/dev/null
python3 << 'PY'
import os
import redis
from dotenv import load_dotenv

load_dotenv()
redis_url = os.getenv('REDIS_URL')
if redis_url:
    try:
        r = redis.from_url(redis_url)
        r.ping()
        print("REDIS_OK")
    except:
        print("REDIS_FAIL")
else:
    print("REDIS_NOT_CONFIGURED")
PY
CHECK_REDIS
)

if [[ "$REDIS_CHECK" == *"REDIS_OK"* ]]; then
    echo "✅ Redis connection successful"
elif [[ "$REDIS_CHECK" == *"REDIS_NOT_CONFIGURED"* ]]; then
    echo "⚠️  Redis not configured"
else
    echo "❌ Redis connection failed"
fi

echo ""
