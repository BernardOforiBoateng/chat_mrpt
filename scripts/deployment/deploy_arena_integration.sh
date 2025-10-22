#!/bin/bash
echo "Deploying Arena Integration to Production..."

# Production instances (Public IPs)
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

# Files to deploy
FILES=(
    "app/templates/index.html"
    "app/static/js/modules/ui/vertical-nav-v2.js"
    "app/static/js/modules/chat/core/message-handler.js"
    "app/static/js/modules/chat/chat-manager-refactored.js"
    "app/web/routes/analysis_routes.py"
    "app/static/css/style.css"
)

# Deploy to both instances
for IP in $INSTANCE1 $INSTANCE2; do
    echo "Deploying to $IP..."
    
    # Copy files
    for FILE in "${FILES[@]}"; do
        echo "  Copying $FILE..."
        scp -i /tmp/chatmrpt-key2.pem "$FILE" ec2-user@$IP:/home/ec2-user/ChatMRPT/$FILE
    done
    
    # Restart service
    echo "  Restarting service..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP 'sudo systemctl restart chatmrpt'
    
    echo "✅ Deployed to $IP"
done

echo "✅ Arena Integration deployed to all production instances!"
