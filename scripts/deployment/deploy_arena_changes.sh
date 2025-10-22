#!/bin/bash

echo "=== Deploy Arena Changes to Production ==="
echo "Deploying to both production instances..."
echo ""

# Key file location
KEY_FILE="/tmp/chatmrpt-key2.pem"

# Check if key exists
if [ ! -f "$KEY_FILE" ]; then
    echo "Copying key file to /tmp..."
    cp aws_files/chatmrpt-key.pem "$KEY_FILE"
    chmod 600 "$KEY_FILE"
fi

# Production instance IPs (from the session summary)
INSTANCE1_IP="3.21.167.170"
INSTANCE2_IP="18.220.103.20"

# Files to deploy
FILES=(
    "app/web/routes/core_routes.py"
    "app/__init__.py"
    "app/core/arena_manager.py"
    "app/templates/arena.html"
    "app/static/js/modules/chat/arena-handler.js"
    "app/static/js/modules/ui/vertical-nav-v2.js"
)

# Deploy to both instances
for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo "📦 Deploying to instance: $IP"
    
    # Copy files
    for FILE in "${FILES[@]}"; do
        echo "  - Copying $FILE..."
        scp -o StrictHostKeyChecking=no -i "$KEY_FILE" "$FILE" "ec2-user@$IP:/home/ec2-user/ChatMRPT/$FILE" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "    ✅ Success"
        else
            echo "    ⚠️ Failed (file might not exist or connection issue)"
        fi
    done
    
    # Restart service
    echo "  - Restarting ChatMRPT service..."
    ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" "ec2-user@$IP" "sudo systemctl restart chatmrpt" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "    ✅ Service restarted"
    else
        echo "    ⚠️ Could not restart service"
    fi
    
    echo ""
done

echo "✅ Deployment complete!"
echo ""
echo "Access the application at:"
echo "  - CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "  - ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "To use legacy interface, append: ?use_legacy=true"