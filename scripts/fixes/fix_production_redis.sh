#!/bin/bash
# Fix Production Redis Configuration
# This script provides options to fix the Redis issue on production

set -e

echo "=== Production Redis Fix ==="
echo "Date: $(date)"
echo ""

SSH_KEY="/tmp/chatmrpt-key2.pem"
STAGING_HOST="ec2-user@18.117.115.217"
PROD_IP="172.31.44.52"

# Check key
if [ ! -f "$SSH_KEY" ]; then
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
    chmod 600 /tmp/chatmrpt-key2.pem
fi

echo "Current Redis configuration on production:"
ssh -i "$SSH_KEY" "$STAGING_HOST" << 'CHECK'
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 'grep -E "REDIS_URL|ENABLE_REDIS" /home/ec2-user/ChatMRPT/.env'
CHECK

echo ""
echo "Choose an option:"
echo "1. Create new production Redis and update configuration (recommended)"
echo "2. Temporarily disable Redis (quick fix but may cause multi-worker issues)"
echo "3. Exit"
echo ""
read -p "Enter your choice (1-3): " choice

case $choice in
    1)
        echo ""
        echo "=== Option 1: Create Production Redis ==="
        echo ""
        echo "To create a production Redis instance:"
        echo "1. Go to AWS Console > ElastiCache"
        echo "2. Create Redis cluster with:"
        echo "   - Name: chatmrpt-redis-production"
        echo "   - Node type: cache.t3.micro (or larger)"
        echo "   - Number of replicas: 0 (for cost savings)"
        echo "   - Subnet group: Same as production EC2"
        echo "   - Security group: Allow port 6379 from production EC2"
        echo ""
        echo "3. Once created, get the endpoint (e.g., chatmrpt-redis-production.xxxxx.use2.cache.amazonaws.com:6379)"
        echo ""
        read -p "Enter the new production Redis endpoint (or 'skip' to exit): " redis_endpoint
        
        if [ "$redis_endpoint" != "skip" ]; then
            echo ""
            echo "Updating production configuration..."
            ssh -i "$SSH_KEY" "$STAGING_HOST" << UPDATEREDIS
                ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP << 'PRODUPDATE'
                    cd /home/ec2-user/ChatMRPT
                    
                    # Backup current .env
                    sudo cp .env .env.backup_$(date +%Y%m%d_%H%M%S)
                    
                    # Update Redis URL
                    sudo sed -i "s|REDIS_URL=.*|REDIS_URL=redis://$redis_endpoint/0|" .env
                    
                    echo "Updated Redis configuration:"
                    grep REDIS .env
                    
                    # Test Redis connection
                    echo ""
                    echo "Testing Redis connection..."
                    python3 << 'PYTEST'
import os
import redis
from dotenv import load_dotenv

load_dotenv()
redis_url = os.getenv('REDIS_URL')
print(f"Connecting to: {redis_url}")

try:
    r = redis.from_url(redis_url)
    r.ping()
    print("✅ Redis connection successful!")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
PYTEST
                    
                    # Restart service
                    echo ""
                    echo "Restarting ChatMRPT service..."
                    sudo systemctl restart chatmrpt
                    
                    sleep 5
                    echo "✅ Service restarted"
                    echo "Workers running: $(ps aux | grep gunicorn | grep -v grep | wc -l)"
PRODUPDATE
UPDATEREDIS
        fi
        ;;
        
    2)
        echo ""
        echo "=== Option 2: Temporarily Disable Redis ==="
        echo ""
        read -p "This may cause session issues with multiple workers. Continue? (y/n): " confirm
        
        if [ "$confirm" = "y" ]; then
            ssh -i "$SSH_KEY" "$STAGING_HOST" << 'DISABLE'
                ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'PRODDISABLE'
                    cd /home/ec2-user/ChatMRPT
                    
                    # Backup current .env
                    sudo cp .env .env.backup_$(date +%Y%m%d_%H%M%S)
                    
                    # Disable Redis
                    sudo sed -i 's/ENABLE_REDIS_SESSIONS=true/ENABLE_REDIS_SESSIONS=false/' .env
                    
                    echo "Redis sessions disabled"
                    grep ENABLE_REDIS .env
                    
                    # Restart service
                    echo ""
                    echo "Restarting ChatMRPT service..."
                    sudo systemctl restart chatmrpt
                    
                    sleep 5
                    echo "✅ Service restarted"
                    echo "Workers running: $(ps aux | grep gunicorn | grep -v grep | wc -l)"
                    
                    echo ""
                    echo "⚠️  WARNING: Redis is disabled. This may cause issues with:"
                    echo "   - Session persistence across workers"
                    echo "   - TPR download links may not persist"
                    echo "   - ITN export may have issues"
                    echo ""
                    echo "Please create a production Redis instance as soon as possible!"
PRODDISABLE
DISABLE
        fi
        ;;
        
    3)
        echo "Exiting..."
        exit 0
        ;;
        
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "=== Fix Complete ==="
echo ""
echo "Next steps:"
echo "1. Clear browser cache or use incognito mode"
echo "2. Test TPR workflow - upload, analyze, check download links"
echo "3. Test ITN export - verify dashboard HTML is included"
echo ""
echo "Production URL: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/"