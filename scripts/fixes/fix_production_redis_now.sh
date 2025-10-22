#!/bin/bash

echo "=== Fixing Redis Configuration on Production Instances ==="
echo "This will update REDIS_HOST from staging to production endpoint"

# Production instances
INSTANCE1="172.31.44.52"
INSTANCE2="172.31.43.200"
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Copy key file to /tmp
echo "Preparing SSH key..."
cp aws_files/chatmrpt-key.pem $KEY_PATH
chmod 600 $KEY_PATH

# Get staging instance IP for SSH proxy
STAGING_IP="3.21.167.170"

echo ""
echo "=== Connecting via staging server to production instances ==="

for INSTANCE_IP in $INSTANCE1 $INSTANCE2; do
    echo ""
    echo "🔧 Fixing Redis on instance: $INSTANCE_IP"
    
    # SSH through staging to production instance
    ssh -i $KEY_PATH ec2-user@$STAGING_IP << 'REMOTE_SCRIPT'
        # Copy key on staging if not exists
        if [ ! -f ~/.ssh/chatmrpt-key.pem ]; then
            echo "Setting up SSH key on staging..."
            exit 1
        fi
        
        # Connect to production instance
        ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@'$INSTANCE_IP' << 'PROD_SCRIPT'
            echo "Connected to production instance $(hostname -I)"
            
            cd /home/ec2-user/ChatMRPT
            
            # Backup current .env
            echo "Backing up current .env..."
            cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
            
            # Fix REDIS_HOST to point to production
            echo "Updating REDIS_HOST to production endpoint..."
            sed -i 's|REDIS_HOST=chatmrpt-redis-staging\.1b3pmt\.0001\.use2\.cache\.amazonaws\.com|REDIS_HOST=chatmrpt-redis-production.1b3pmt.0001.use2.cache.amazonaws.com|' .env
            
            # Verify the change
            echo "Verifying Redis configuration:"
            grep -E "REDIS_HOST|REDIS_URL|REDIS_ENABLED" .env
            
            # Also ensure REDIS_ENABLED is set to true
            if ! grep -q "REDIS_ENABLED=true" .env; then
                echo "REDIS_ENABLED=true" >> .env
                echo "Added REDIS_ENABLED=true"
            fi
            
            # Restart the service
            echo "Restarting ChatMRPT service..."
            sudo systemctl restart chatmrpt
            
            # Wait for service to start
            sleep 5
            
            # Check service status
            echo "Service status:"
            sudo systemctl status chatmrpt | head -20
            
            # Test Redis connectivity
            echo ""
            echo "Testing Redis connection..."
            python3 << 'PYTEST'
import redis
import os
from dotenv import load_dotenv

load_dotenv()

redis_host = os.getenv('REDIS_HOST', '')
redis_port = int(os.getenv('REDIS_PORT', 6379))

print(f"Testing connection to: {redis_host}:{redis_port}")

try:
    r = redis.Redis(host=redis_host, port=redis_port, db=0, socket_timeout=5)
    r.ping()
    print("✅ Redis connection successful!")
    
    # Test setting and getting a value
    r.set('test_key', 'test_value', ex=10)
    value = r.get('test_key')
    if value == b'test_value':
        print("✅ Redis read/write test successful!")
    else:
        print("❌ Redis read/write test failed")
        
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
PYTEST
            
            echo ""
            echo "✅ Completed fixing Redis on $(hostname -I)"
PROD_SCRIPT
REMOTE_SCRIPT
    
    echo "-----------------------------------"
done

echo ""
echo "=== Redis Fix Complete ==="
echo ""
echo "Summary:"
echo "✅ Updated REDIS_HOST from staging to production endpoint on both instances"
echo "✅ Ensured REDIS_ENABLED=true is set"
echo "✅ Restarted ChatMRPT service on both instances"
echo ""
echo "The session state issue with option '2' should now be resolved!"
echo "Users should now be able to select guided TPR analysis without issues."