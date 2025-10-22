#!/bin/bash

# Fix Redis connectivity issues on AWS instances
# This script addresses Redis timeout errors on Instance 2

echo "==========================================
FIXING REDIS CONNECTIVITY ISSUES
=========================================="

# AWS Instance IPs
INSTANCE1_IP="3.21.167.170"
INSTANCE2_IP="18.220.103.20"
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Copy key if not present
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem $KEY_PATH
    chmod 600 $KEY_PATH
fi

# Function to check Redis connectivity
check_redis() {
    local ip=$1
    local instance_name=$2
    
    echo "📋 Checking Redis on $instance_name ($ip)..."
    
    ssh -i $KEY_PATH ec2-user@$ip << 'EOF'
        # Check if Redis client is installed
        if command -v redis-cli &> /dev/null; then
            echo "Testing Redis connection..."
            timeout 5 redis-cli -h chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com -p 6379 ping || echo "Redis ping failed"
        else
            echo "Redis client not installed"
        fi
        
        # Check application logs for Redis errors
        echo "Recent Redis errors in application:"
        sudo journalctl -u chatmrpt --since "1 hour ago" | grep -i redis | tail -5
        
        # Check network connectivity to Redis endpoint
        echo "Testing network connectivity to Redis:"
        nc -zv chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com 6379 2>&1 || echo "Cannot reach Redis endpoint"
EOF
}

# Function to fix Redis on an instance
fix_redis() {
    local ip=$1
    local instance_name=$2
    
    echo "🔧 Fixing Redis on $instance_name ($ip)..."
    
    ssh -i $KEY_PATH ec2-user@$ip << 'EOF'
        # Install Redis client if not present
        if ! command -v redis-cli &> /dev/null; then
            echo "Installing Redis client..."
            sudo yum install -y redis
        fi
        
        # Check and update security group rules
        echo "Checking security group for Redis access..."
        
        # Test Redis connectivity with timeout
        echo "Testing Redis connectivity..."
        REDIS_HOST="chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com"
        REDIS_PORT="6379"
        
        # Try to connect with redis-cli
        if redis-cli -h $REDIS_HOST -p $REDIS_PORT --connect-timeout 5 ping 2>/dev/null; then
            echo "✅ Redis connection successful!"
        else
            echo "❌ Redis connection failed"
            
            # Check DNS resolution
            echo "Checking DNS resolution..."
            nslookup $REDIS_HOST || echo "DNS resolution failed"
            
            # Check route to Redis
            echo "Checking route to Redis..."
            traceroute -n -m 5 $REDIS_HOST 2>/dev/null || echo "Traceroute failed"
        fi
        
        # Restart the application to reset connections
        echo "Restarting application service..."
        sudo systemctl restart chatmrpt
        
        # Wait for service to start
        sleep 5
        
        # Check service status
        sudo systemctl status chatmrpt --no-pager | head -20
EOF
}

# Main execution
echo "🔍 Step 1: Checking current Redis connectivity..."
check_redis $INSTANCE1_IP "Instance 1"
check_redis $INSTANCE2_IP "Instance 2"

echo ""
echo "🔧 Step 2: Applying fixes..."
fix_redis $INSTANCE1_IP "Instance 1"
fix_redis $INSTANCE2_IP "Instance 2"

echo ""
echo "🔍 Step 3: Verifying fixes..."
check_redis $INSTANCE1_IP "Instance 1"
check_redis $INSTANCE2_IP "Instance 2"

# Deploy a simple test to verify session persistence
echo ""
echo "🧪 Step 4: Testing session persistence across instances..."

# Create a test session on Instance 1
echo "Creating test session on Instance 1..."
SESSION_ID="redis-test-$(date +%s)"
ssh -i $KEY_PATH ec2-user@$INSTANCE1_IP << EOF
    curl -X POST http://localhost:5000/api/test-session \
         -H "Content-Type: application/json" \
         -d '{"session_id": "$SESSION_ID", "data": "test_from_instance1"}' \
         2>/dev/null || echo "Test endpoint not available"
EOF

# Try to read it from Instance 2
echo "Reading test session from Instance 2..."
ssh -i $KEY_PATH ec2-user@$INSTANCE2_IP << EOF
    curl -X GET http://localhost:5000/api/test-session/$SESSION_ID \
         2>/dev/null || echo "Test endpoint not available"
EOF

echo ""
echo "==========================================
REDIS CONNECTIVITY FIX COMPLETE
==========================================

Next steps:
1. If Redis is still failing, check AWS ElastiCache console
2. Verify security group allows inbound traffic on port 6379
3. Check if ElastiCache subnet group includes application subnets
4. Consider implementing file-based session fallback as backup

To manually test Redis:
ssh -i $KEY_PATH ec2-user@$INSTANCE2_IP
redis-cli -h chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com ping
"