#!/bin/bash
# Update Production Redis Configuration Properly
# This script properly tests and updates the Redis configuration

set -e

echo "=== Production Redis Configuration Update ==="
echo "Date: $(date)"
echo ""

SSH_KEY="/tmp/chatmrpt-key2.pem"
STAGING_HOST="ec2-user@18.117.115.217"
PROD_IP="172.31.44.52"
REDIS_ENDPOINT="chatmrpt-redis-production.1b3pmt.0001.use2.cache.amazonaws.com:6379"

# Ensure we have the SSH key
if [ ! -f "$SSH_KEY" ]; then
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
    chmod 600 /tmp/chatmrpt-key2.pem
fi

echo "📋 Step 1: Testing Redis connection from production server..."
echo ""

# Test Redis connection using the virtual environment
ssh -i "$SSH_KEY" "$STAGING_HOST" << 'TEST_REDIS'
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'PROD_TEST'
        cd /home/ec2-user/ChatMRPT
        
        # Activate virtual environment and test Redis
        source chatmrpt_venv_new/bin/activate
        
        python << PYTEST
import redis
import sys

redis_endpoint = "chatmrpt-redis-production.1b3pmt.0001.use2.cache.amazonaws.com:6379"
redis_url = f"redis://{redis_endpoint}/0"
print(f"Testing connection to: {redis_url}")

try:
    r = redis.from_url(redis_url, socket_connect_timeout=5)
    r.ping()
    print("✅ Redis connection successful!")
    # Test setting and getting a value
    r.set('test_key', 'production_test', ex=60)
    value = r.get('test_key')
    if value == b'production_test':
        print("✅ Redis read/write test successful!")
    else:
        print("❌ Redis read/write test failed!")
        sys.exit(1)
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    sys.exit(1)
PYTEST
PROD_TEST
TEST_REDIS

if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Redis connection test failed. Please check:"
    echo "  1. Redis cluster is in 'available' status"
    echo "  2. Security group allows connection from production EC2"
    echo "  3. Endpoint is correct"
    exit 1
fi

echo ""
echo "📋 Step 2: Backing up current configuration..."

ssh -i "$SSH_KEY" "$STAGING_HOST" << 'BACKUP'
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'PROD_BACKUP'
        cd /home/ec2-user/ChatMRPT
        
        # Create timestamped backup
        BACKUP_FILE=".env.backup_$(date +%Y%m%d_%H%M%S)_redis_update"
        sudo cp .env "$BACKUP_FILE"
        echo "✅ Backup created: $BACKUP_FILE"
        
        # Show current configuration
        echo ""
        echo "Current Redis configuration:"
        grep -E "REDIS_URL|ENABLE_REDIS" .env
PROD_BACKUP
BACKUP

echo ""
echo "📋 Step 3: Updating production configuration..."

ssh -i "$SSH_KEY" "$STAGING_HOST" << UPDATE_PROD
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'PROD_UPDATE'
        cd /home/ec2-user/ChatMRPT
        
        # Update Redis URL
        echo "Updating Redis URL..."
        sudo sed -i "s|REDIS_URL=redis://[^/]*/0|REDIS_URL=redis://chatmrpt-redis-production.1b3pmt.0001.use2.cache.amazonaws.com:6379/0|" .env
        
        # Verify the change
        echo ""
        echo "New Redis configuration:"
        grep -E "REDIS_URL|ENABLE_REDIS" .env
        
        # Ensure Redis is enabled
        if ! grep -q "ENABLE_REDIS_SESSIONS=true" .env; then
            echo "ENABLE_REDIS_SESSIONS=true" | sudo tee -a .env
        fi
PROD_UPDATE
UPDATE_PROD

echo ""
echo "📋 Step 4: Restarting ChatMRPT service..."

ssh -i "$SSH_KEY" "$STAGING_HOST" << 'RESTART'
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'PROD_RESTART'
        # Stop the service
        echo "Stopping ChatMRPT service..."
        sudo systemctl stop chatmrpt
        
        # Wait a moment
        sleep 3
        
        # Start the service
        echo "Starting ChatMRPT service..."
        sudo systemctl start chatmrpt
        
        # Wait for service to fully start
        echo "Waiting for service to start..."
        sleep 10
        
        # Check status
        echo ""
        echo "Service status:"
        sudo systemctl status chatmrpt | head -15
        
        # Check worker count
        echo ""
        echo "Worker processes:"
        ps aux | grep gunicorn | grep -v grep | wc -l
        
        # Check for any startup errors
        echo ""
        echo "Checking for startup errors..."
        sudo journalctl -u chatmrpt -n 50 | grep -i error | tail -10 || echo "No errors found in recent logs"
PROD_RESTART
RESTART

echo ""
echo "📋 Step 5: Verifying Redis connection from application..."

ssh -i "$SSH_KEY" "$STAGING_HOST" << 'VERIFY'
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'PROD_VERIFY'
        cd /home/ec2-user/ChatMRPT
        
        # Test Redis from within the application context
        source chatmrpt_venv_new/bin/activate
        
        python << VERIFY_PY
import os
import sys
import redis
from dotenv import load_dotenv

# Load the environment variables
load_dotenv()

redis_url = os.getenv('REDIS_URL')
redis_enabled = os.getenv('ENABLE_REDIS_SESSIONS')

print(f"REDIS_URL from .env: {redis_url}")
print(f"ENABLE_REDIS_SESSIONS: {redis_enabled}")

if redis_url and redis_enabled == 'true':
    try:
        r = redis.from_url(redis_url)
        r.ping()
        print("✅ Application can connect to Redis!")
        
        # Test session-like operation
        test_key = "session:test:production"
        r.setex(test_key, 300, "production_verification")
        value = r.get(test_key)
        if value:
            print("✅ Session storage test successful!")
            r.delete(test_key)
        else:
            print("❌ Session storage test failed!")
    except Exception as e:
        print(f"❌ Redis connection error: {e}")
        sys.exit(1)
else:
    print("❌ Redis not properly configured in .env")
    sys.exit(1)
VERIFY_PY
PROD_VERIFY
VERIFY

echo ""
echo "✅ === Production Redis Update Complete ==="
echo ""
echo "Summary:"
echo "- Production now uses: chatmrpt-redis-production.1b3pmt.0001.use2.cache.amazonaws.com:6379"
echo "- Service has been restarted with new configuration"
echo "- Redis connection verified from application"
echo ""
echo "PLEASE TEST:"
echo "1. Go to: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/"
echo "2. Clear browser cache (Ctrl+Shift+R) or use incognito mode"
echo "3. Test TPR workflow:"
echo "   - Upload a TPR file"
echo "   - Complete the analysis"
echo "   - Click 'Download Processed Data' tab"
echo "   - Verify download links appear"
echo "4. Test ITN export:"
echo "   - Run ITN distribution planning"
echo "   - Export the package"
echo "   - Verify dashboard HTML is included"
echo ""
echo "To monitor logs in real-time:"
echo "ssh -i $SSH_KEY $STAGING_HOST 'ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 \"sudo journalctl -u chatmrpt -f\"'"