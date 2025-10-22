#!/bin/bash

# Simplified Production Deployment Script
# Deploys to the ACTIVE production environment (formerly staging)

echo "🚀 Deploying to Production Environment"
echo "======================================"
echo ""

# Production instances (formerly staging)
PRODUCTION_IPS=("3.21.167.170" "18.220.103.20")
INSTANCE_NAMES=("Instance 1" "Instance 2")

# Files to deploy (add your files here)
FILES_TO_DEPLOY=()
for arg in "$@"; do
    FILES_TO_DEPLOY+=("$arg")
done

if [ ${#FILES_TO_DEPLOY[@]} -eq 0 ]; then
    echo "Usage: $0 <file1> [file2] [file3] ..."
    echo ""
    echo "Example:"
    echo "  $0 app/core/request_interpreter.py"
    echo "  $0 app/tools/*.py"
    echo "  $0 app/web/routes/analysis_routes.py app/services/agent.py"
    echo ""
    exit 1
fi

echo "📦 Files to deploy:"
for FILE in "${FILES_TO_DEPLOY[@]}"; do
    echo "  - $FILE"
done
echo ""

# SSH key location
SSH_KEY="/tmp/chatmrpt-key2.pem"
if [ ! -f "$SSH_KEY" ]; then
    # Try to copy from standard location
    if [ -f "aws_files/chatmrpt-key.pem" ]; then
        cp aws_files/chatmrpt-key.pem "$SSH_KEY"
        chmod 600 "$SSH_KEY"
        echo "✅ SSH key prepared"
    else
        echo "❌ SSH key not found at aws_files/chatmrpt-key.pem"
        exit 1
    fi
fi

# Deploy to each production instance
SUCCESS_COUNT=0
for i in ${!PRODUCTION_IPS[@]}; do
    IP="${PRODUCTION_IPS[$i]}"
    NAME="${INSTANCE_NAMES[$i]}"
    
    echo ""
    echo "🔄 Deploying to $NAME ($IP)..."
    echo "-----------------------------------"
    
    # Test connectivity
    ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no -o ConnectTimeout=5 \
        "ec2-user@$IP" "echo '  ✅ Connected'" 2>/dev/null
    
    if [ $? -ne 0 ]; then
        echo "  ❌ Cannot connect to $IP"
        continue
    fi
    
    # Copy files
    ALL_SUCCESS=true
    for FILE in "${FILES_TO_DEPLOY[@]}"; do
        echo -n "  📄 Copying $(basename $FILE)... "
        
        # Ensure directory exists on remote
        DIR=$(dirname "$FILE")
        ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ec2-user@$IP" \
            "mkdir -p /home/ec2-user/ChatMRPT/$DIR" 2>/dev/null
        
        # Copy the file
        scp -i "$SSH_KEY" -o StrictHostKeyChecking=no -q \
            "$FILE" "ec2-user@$IP:/home/ec2-user/ChatMRPT/$FILE" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "✅"
        else
            echo "❌"
            ALL_SUCCESS=false
        fi
    done
    
    if [ "$ALL_SUCCESS" = true ]; then
        # Restart service
        echo "  🔄 Restarting ChatMRPT service..."
        ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ec2-user@$IP" \
            "sudo systemctl restart chatmrpt" 2>/dev/null
        
        # Check status
        sleep 2
        SERVICE_STATUS=$(ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "ec2-user@$IP" \
            "sudo systemctl is-active chatmrpt" 2>/dev/null)
        
        if [ "$SERVICE_STATUS" = "active" ]; then
            echo "  ✅ Service running on $NAME"
            ((SUCCESS_COUNT++))
        else
            echo "  ⚠️  Service may not be running properly on $NAME"
        fi
    fi
done

echo ""
echo "======================================"
if [ $SUCCESS_COUNT -eq ${#PRODUCTION_IPS[@]} ]; then
    echo "✅ Deployment SUCCESSFUL to all instances!"
else
    echo "⚠️  Deployment completed to $SUCCESS_COUNT of ${#PRODUCTION_IPS[@]} instances"
fi
echo ""
echo "🌐 Production URL: https://d225ar6c86586s.cloudfront.net"
echo "📊 ALB Health: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "To check logs:"
echo "  ssh -i $SSH_KEY ec2-user@3.21.167.170 'sudo journalctl -u chatmrpt -f'"