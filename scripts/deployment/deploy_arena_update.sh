#!/bin/bash
# Deploy Arena updates to production instances

echo "================================================"
echo "  Deploying Arena Updates to Production"
echo "================================================"

# Production instances (former staging)
INSTANCE1_IP="3.21.167.170"
INSTANCE2_IP="18.220.103.20"
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Files to deploy
FILES_TO_DEPLOY=".env app/core/arena_manager.py"

echo ""
echo "Files to deploy:"
echo "- .env (updated model names)"
echo "- app/core/arena_manager.py (updated model configs)"
echo ""

# Deploy to both instances
for ip in $INSTANCE1_IP $INSTANCE2_IP; do
    echo "Deploying to instance: $ip"
    
    # Copy files
    for file in $FILES_TO_DEPLOY; do
        echo "  Copying $file..."
        scp -i $KEY_PATH -o StrictHostKeyChecking=no $file ec2-user@$ip:/home/ec2-user/ChatMRPT/$file
    done
    
    # Restart service
    echo "  Restarting service..."
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no ec2-user@$ip "sudo systemctl restart chatmrpt"
    
    echo "  Done!"
    echo ""
done

echo "================================================"
echo "  Deployment Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. Test Arena at: https://d225ar6c86586s.cloudfront.net"
echo "2. Click the Arena mode toggle in navigation"
echo "3. Test switching between model views with arrow buttons"
echo ""
echo "GPU Instance Status:"
echo "- IP: 18.118.171.148"
echo "- Models: Llama 3.1, OpenHermes 2.5, Qwen 3, BioMistral, Phi-3"
echo "- Server: http://172.31.45.157:8000"