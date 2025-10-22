#!/bin/bash

# Deploy 3-model Arena configuration to production instances

echo "Deploying 3-model Arena configuration to production instances..."

# Production instance IPs
PRODUCTION_IPS=("3.21.167.170" "18.220.103.20")

# Files to deploy
FILES_TO_DEPLOY="app/core/arena_manager.py app/web/routes/arena_routes.py"

for IP in "${PRODUCTION_IPS[@]}"; do
    echo "\nDeploying to $IP..."
    
    # Copy files
    for FILE in $FILES_TO_DEPLOY; do
        echo "  Copying $FILE..."
        scp -o StrictHostKeyChecking=no -i /tmp/chatmrpt-key2.pem "$FILE" ec2-user@$IP:/home/ec2-user/ChatMRPT/$FILE
    done
    
    # Restart service
    echo "  Restarting ChatMRPT service..."
    ssh -o StrictHostKeyChecking=no -i /tmp/chatmrpt-key2.pem ec2-user@$IP "sudo systemctl restart chatmrpt"
    
    echo "  ✓ Deployment to $IP complete"
done

echo "\n✓ 3-model Arena configuration deployed to all production instances"
echo "Arena is now running with 3 models: phi3:mini, mistral:7b, qwen2.5:7b"