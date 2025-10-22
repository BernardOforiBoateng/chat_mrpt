#!/bin/bash

echo "=== Deploying Arena Fixes to Production ==="
echo "Target instances: 3.21.167.170 and 18.220.103.20"
echo "============================================"

# Production instance IPs (formerly staging)
PROD_IP1="3.21.167.170"
PROD_IP2="18.220.103.20"

# Files to deploy
echo ""
echo "Files to deploy:"
echo "- Frontend build (app/static/react/)"
echo "- app/web/routes/arena_routes.py"
echo "- app/core/arena_manager.py"
echo ""

# Check if we have the SSH key
if [ ! -f /tmp/chatmrpt-key2.pem ]; then
    echo "❌ SSH key not found at /tmp/chatmrpt-key2.pem"
    echo "Please copy the key file first:"
    echo "  cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem"
    echo "  chmod 600 /tmp/chatmrpt-key2.pem"
    exit 1
fi

# Deploy to both production instances
for PROD_IP in $PROD_IP1 $PROD_IP2; do
    echo "================================================"
    echo "Deploying to $PROD_IP..."
    echo "================================================"
    
    # Copy React build files
    echo "1. Copying React build files..."
    rsync -avz -e "ssh -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no" \
        app/static/react/ \
        ec2-user@${PROD_IP}:/home/ec2-user/ChatMRPT/app/static/react/
    
    if [ $? -eq 0 ]; then
        echo "   ✅ React files deployed"
    else
        echo "   ❌ Failed to deploy React files"
    fi
    
    # Copy arena_routes.py
    echo "2. Copying arena_routes.py..."
    scp -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no \
        app/web/routes/arena_routes.py \
        ec2-user@${PROD_IP}:/home/ec2-user/ChatMRPT/app/web/routes/
    
    if [ $? -eq 0 ]; then
        echo "   ✅ arena_routes.py deployed"
    else
        echo "   ❌ Failed to deploy arena_routes.py"
    fi
    
    # Copy arena_manager.py
    echo "3. Copying arena_manager.py..."
    scp -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no \
        app/core/arena_manager.py \
        ec2-user@${PROD_IP}:/home/ec2-user/ChatMRPT/app/core/
    
    if [ $? -eq 0 ]; then
        echo "   ✅ arena_manager.py deployed"
    else
        echo "   ❌ Failed to deploy arena_manager.py"
    fi
    
    # Restart the service
    echo "4. Restarting ChatMRPT service..."
    ssh -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no \
        ec2-user@${PROD_IP} "sudo systemctl restart chatmrpt"
    
    if [ $? -eq 0 ]; then
        echo "   ✅ Service restarted"
    else
        echo "   ❌ Failed to restart service"
    fi
    
    echo ""
done

echo "============================================"
echo "Deployment complete!"
echo ""
echo "Testing endpoints:"
echo "- CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "- ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""

# Test the endpoints
echo "Health check results:"
curl -s -o /dev/null -w "CloudFront: %{http_code}\n" https://d225ar6c86586s.cloudfront.net/ping
curl -s -o /dev/null -w "ALB: %{http_code}\n" http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/ping

echo ""
echo "✅ Arena fixes deployed to both production instances!"
echo "Please test the Arena mode at: https://d225ar6c86586s.cloudfront.net"