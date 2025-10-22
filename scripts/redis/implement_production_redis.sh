#!/bin/bash
# Production Redis Implementation Script
# Follow the plan in redis_production_implementation_plan.md

set -e

echo "=== Production Redis Implementation ==="
echo "Date: $(date)"
echo ""

SSH_KEY="/tmp/chatmrpt-key2.pem"
STAGING_HOST="ec2-user@18.117.115.217"
PROD_IP="172.31.44.52"

# Ensure we have the SSH key
if [ ! -f "$SSH_KEY" ]; then
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
    chmod 600 /tmp/chatmrpt-key2.pem
fi

# Step 1: Document current state
echo "📋 Step 1: Documenting current state..."
echo ""

ssh -i "$SSH_KEY" "$STAGING_HOST" << 'DOCUMENT'
    echo "=== Production Current State ==="
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@172.31.44.52 << 'PROD_STATE'
        echo "Current Redis Configuration:"
        grep -E "REDIS_URL|ENABLE_REDIS" /home/ec2-user/ChatMRPT/.env
        
        echo ""
        echo "Service Status:"
        sudo systemctl status chatmrpt | head -5
        
        echo ""
        echo "Worker Count:"
        ps aux | grep gunicorn | grep -v grep | wc -l
        
        echo ""
        echo "Creating backup of .env file..."
        sudo cp /home/ec2-user/ChatMRPT/.env /home/ec2-user/ChatMRPT/.env.backup_$(date +%Y%m%d_%H%M%S)_redis
        echo "✅ Backup created"
PROD_STATE
DOCUMENT

echo ""
echo "📋 Current state documented and backup created."
echo ""
echo "=== NEXT STEPS ==="
echo ""
echo "1. CREATE REDIS INSTANCE IN AWS:"
echo "   - Go to AWS Console > ElastiCache > Redis"
echo "   - Click 'Create'"
echo "   - Use these settings:"
echo "     * Cluster Mode: Disabled"
echo "     * Name: chatmrpt-redis-production"
echo "     * Node type: cache.t3.micro"
echo "     * Number of replicas: 0"
echo "     * Multi-AZ: No"
echo "     * Subnet group: Use existing or create in same VPC as production"
echo "     * Security group: Create new 'chatmrpt-redis-production-sg'"
echo "       - Allow inbound TCP 6379 from production EC2 security group"
echo ""
echo "2. WAIT for Redis cluster to show 'available' status (15-20 minutes)"
echo ""
echo "3. COPY the Redis endpoint (e.g., chatmrpt-redis-production.abc123.use2.cache.amazonaws.com)"
echo ""
echo "4. RUN this script again with the endpoint:"
echo "   ./implement_production_redis.sh UPDATE <redis-endpoint>"
echo ""

# Check if we're doing the update
if [ "$1" == "UPDATE" ] && [ ! -z "$2" ]; then
    REDIS_ENDPOINT="$2"
    echo ""
    echo "=== Updating Production with New Redis Endpoint ==="
    echo "Endpoint: $REDIS_ENDPOINT"
    echo ""
    
    read -p "Is this correct? (y/n): " confirm
    if [ "$confirm" != "y" ]; then
        echo "Cancelled"
        exit 1
    fi
    
    # First test the connection
    echo ""
    echo "📋 Testing Redis connection..."
    
    ssh -i "$SSH_KEY" "$STAGING_HOST" << TEST_REDIS
        ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP << 'PROD_TEST'
            cd /home/ec2-user/ChatMRPT
            
            python3 << PYTEST
import redis
import sys

redis_url = "redis://$REDIS_ENDPOINT/0"
print(f"Testing connection to: {redis_url}")

try:
    r = redis.from_url(redis_url, socket_connect_timeout=5)
    r.ping()
    print("✅ Redis connection successful!")
except Exception as e:
    print(f"❌ Redis connection failed: {e}")
    sys.exit(1)
PYTEST
PROD_TEST
TEST_REDIS
    
    if [ $? -ne 0 ]; then
        echo "❌ Redis connection test failed. Please check:"
        echo "  - Redis cluster is 'available' status"
        echo "  - Security group allows connection from production EC2"
        echo "  - Endpoint is correct"
        exit 1
    fi
    
    # Update production
    echo ""
    echo "📋 Updating production configuration..."
    
    ssh -i "$SSH_KEY" "$STAGING_HOST" << UPDATE_PROD
        ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP << 'PROD_UPDATE'
            cd /home/ec2-user/ChatMRPT
            
            # Show current config
            echo "Current configuration:"
            grep REDIS_URL .env
            
            # Update Redis URL
            sudo sed -i "s|REDIS_URL=redis://[^/]*|REDIS_URL=redis://$REDIS_ENDPOINT|" .env
            
            # Show new config
            echo ""
            echo "New configuration:"
            grep REDIS_URL .env
            
            # Restart service
            echo ""
            echo "Restarting ChatMRPT service..."
            sudo systemctl restart chatmrpt
            
            # Wait for service to start
            sleep 10
            
            # Check status
            echo ""
            echo "Service status:"
            sudo systemctl status chatmrpt | head -10
            
            echo ""
            echo "Worker count:"
            ps aux | grep gunicorn | grep -v grep | wc -l
            
            # Check for errors
            echo ""
            echo "Recent logs (checking for errors):"
            sudo journalctl -u chatmrpt -n 20 | grep -i error || echo "No errors found"
PROD_UPDATE
UPDATE_PROD
    
    echo ""
    echo "✅ === Production Redis Update Complete ==="
    echo ""
    echo "PLEASE TEST:"
    echo "1. Go to: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/"
    echo "2. Clear browser cache or use incognito mode"
    echo "3. Test TPR workflow:"
    echo "   - Upload TPR file"
    echo "   - Complete analysis"
    echo "   - Check 'Download Processed Data' tab"
    echo "4. Test ITN export:"
    echo "   - Run ITN distribution"
    echo "   - Export package"
    echo "   - Verify dashboard HTML is included"
    echo ""
    echo "Monitor logs with:"
    echo "ssh -i $SSH_KEY $STAGING_HOST 'ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP \"sudo journalctl -u chatmrpt -f\"'"
fi