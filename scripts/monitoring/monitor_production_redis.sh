#!/bin/bash
# Monitor Production Redis and Application Health

SSH_KEY="/tmp/chatmrpt-key2.pem"
STAGING_HOST="ec2-user@18.117.115.217"
PROD_IP="172.31.44.52"

if [ ! -f "$SSH_KEY" ]; then
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
    chmod 600 /tmp/chatmrpt-key2.pem
fi

echo "=== Production Redis Monitoring ==="
echo "Date: $(date)"
echo ""

# Check Redis configuration
echo "📋 Current Redis Configuration:"
ssh -i "$SSH_KEY" "$STAGING_HOST" << 'CHECK_CONFIG'
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 'grep -E "REDIS_URL|ENABLE_REDIS" /home/ec2-user/ChatMRPT/.env'
CHECK_CONFIG

echo ""
echo "📋 Service Status:"
ssh -i "$SSH_KEY" "$STAGING_HOST" << 'CHECK_SERVICE'
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'PROD_CHECK'
        sudo systemctl status chatmrpt | head -10
        echo ""
        echo "Worker count: $(ps aux | grep gunicorn | grep -v grep | wc -l)"
PROD_CHECK
CHECK_SERVICE

echo ""
echo "📋 Redis Connection Test:"
ssh -i "$SSH_KEY" "$STAGING_HOST" << 'TEST_REDIS'
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'PROD_TEST'
        cd /home/ec2-user/ChatMRPT
        /home/ec2-user/chatmrpt_env/bin/python << 'PYTEST'
import redis
import os
from dotenv import load_dotenv

load_dotenv()
redis_url = os.getenv('REDIS_URL')

try:
    r = redis.from_url(redis_url)
    r.ping()
    print(f"✅ Redis connection OK: {redis_url}")
    
    # Check for any existing sessions
    session_keys = list(r.scan_iter("session:*"))
    print(f"Active sessions: {len(session_keys)}")
    
    # Check Redis info
    info = r.info()
    print(f"Redis uptime: {info['uptime_in_seconds']} seconds")
    print(f"Connected clients: {info['connected_clients']}")
    print(f"Used memory: {info['used_memory_human']}")
except Exception as e:
    print(f"❌ Redis error: {e}")
PYTEST
PROD_TEST
TEST_REDIS

echo ""
echo "📋 Recent Application Logs (last 20 lines):"
ssh -i "$SSH_KEY" "$STAGING_HOST" << 'CHECK_LOGS'
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 'sudo journalctl -u chatmrpt -n 20 --no-pager'
CHECK_LOGS

echo ""
echo "=== Monitoring Complete ==="
echo ""
echo "To view real-time logs:"
echo "ssh -i aws_files/chatmrpt-key.pem ec2-user@172.31.44.52 'sudo journalctl -u chatmrpt -f'"