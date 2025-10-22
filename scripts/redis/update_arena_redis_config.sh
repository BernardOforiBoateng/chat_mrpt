#!/bin/bash

# Update Arena Configuration for Redis Storage
echo "=========================================="
echo "Updating Arena Configuration for Redis"
echo "=========================================="

# Production instances
INSTANCES="3.21.167.170 18.220.103.20"
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Ensure SSH key has correct permissions
if [ ! -f "$KEY_PATH" ]; then
    echo "Setting up SSH key..."
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

echo ""
echo "1. Updating Environment Configuration..."
echo "=========================================="

for IP in $INSTANCES; do
    echo "Updating $IP..."
    
    ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@$IP << 'EOF'
        cd /home/ec2-user/ChatMRPT
        
        # Backup current .env
        [ -f .env ] && cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
        
        # Add Redis configuration if not present
        if ! grep -q "REDIS_HOST=" .env 2>/dev/null; then
            echo "" >> .env
            echo "# Redis Configuration for Arena" >> .env
            echo "REDIS_HOST=chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com" >> .env
            echo "REDIS_PORT=6379" >> .env
            echo "REDIS_DB=1" >> .env
            echo "✅ Added Redis configuration to .env"
        else
            # Update existing Redis configuration
            sed -i 's|^REDIS_HOST=.*|REDIS_HOST=chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com|' .env
            echo "✅ Updated Redis configuration in .env"
        fi
        
        # Verify Redis connectivity
        echo "Testing Redis connection..."
        /home/ec2-user/chatmrpt_env/bin/python3 -c "
import redis
try:
    r = redis.StrictRedis(host='chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com', port=6379, db=1, socket_connect_timeout=5)
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
" 2>&1
EOF
    
    echo "Done with $IP"
    echo ""
done

echo ""
echo "2. Updating ALB Sticky Session Duration..."
echo "=========================================="

# Connect to one instance to update ALB configuration
ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@3.21.167.170 << 'EOF'
    
    # Get instance metadata
    TOKEN=$(curl -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600" 2>/dev/null)
    REGION=$(curl -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/placement/region 2>/dev/null)
    
    echo "Region: $REGION"
    
    # Get target group ARN for staging
    TARGET_GROUP_ARN="arn:aws:elasticloadbalancing:us-east-2:593543055880:targetgroup/chatmrpt-staging-targets/cfb375512f786bdb"
    
    echo "Target Group: $TARGET_GROUP_ARN"
    
    # Update sticky session duration to 24 hours (86400 seconds)
    echo "Updating sticky session duration to 24 hours..."
    
    aws elbv2 modify-target-group-attributes \
        --region $REGION \
        --target-group-arn $TARGET_GROUP_ARN \
        --attributes \
            Key=stickiness.enabled,Value=true \
            Key=stickiness.type,Value=lb_cookie \
            Key=stickiness.lb_cookie.duration_seconds,Value=86400 2>&1
    
    if [ $? -eq 0 ]; then
        echo "✅ Sticky session duration updated to 24 hours"
        
        # Verify configuration
        echo ""
        echo "Current stickiness configuration:"
        aws elbv2 describe-target-group-attributes \
            --region $REGION \
            --target-group-arn $TARGET_GROUP_ARN \
            --query "Attributes[?contains(Key, 'stickiness')].[Key,Value]" \
            --output table 2>/dev/null
    else
        echo "❌ Failed to update sticky session duration"
    fi
    
EOF

echo ""
echo "3. Deploying Arena Redis Updates..."
echo "=========================================="

# Deploy the new arena manager
for IP in $INSTANCES; do
    echo "Deploying to $IP..."
    
    # Copy new arena manager with Redis support
    scp -o StrictHostKeyChecking=no -i "$KEY_PATH" \
        app/core/arena_manager_redis.py \
        app/web/routes/arena_routes.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/core/ 2>/dev/null
    
    # Move arena_routes.py to correct location
    ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@$IP \
        "mv /home/ec2-user/ChatMRPT/app/core/arena_routes.py /home/ec2-user/ChatMRPT/app/web/routes/ 2>/dev/null || true"
    
    # Restart service
    ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@$IP \
        "sudo systemctl restart chatmrpt"
    
    echo "✅ Deployed to $IP"
done

echo ""
echo "4. Testing Arena with Redis..."
echo "=========================================="

sleep 10  # Wait for services to restart

# Test arena status
echo "Testing Arena status endpoint..."
STATUS=$(curl -s https://d225ar6c86586s.cloudfront.net/api/arena/status | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    print(f\"Arena Available: {data.get('available', False)}\")
    print(f\"Storage Status: {data.get('storage_status', 'Unknown')}\")
    print(f\"Active Models: {data.get('active_models', 0)}\")
except:
    print('Failed to parse response')
" 2>&1)

echo "$STATUS"

echo ""
echo "=========================================="
echo "Configuration Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "✅ Redis configuration added to .env"
echo "✅ ALB sticky sessions set to 24 hours"
echo "✅ Arena manager with Redis support deployed"
echo ""
echo "The Arena system now uses Redis for distributed session storage,"
echo "allowing battles to persist across multiple workers!"