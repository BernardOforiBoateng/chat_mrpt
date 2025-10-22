#!/bin/bash

# Deploy React fix to production instances
echo "Deploying React fix to production instances..."

# Production IPs
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Copy key if not already there
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem $KEY_PATH
    chmod 600 $KEY_PATH
fi

# Deploy to both instances
for IP in $INSTANCE1 $INSTANCE2; do
    echo "Deploying to $IP..."
    
    # Copy React build files
    scp -i $KEY_PATH -r app/static/react/* ec2-user@$IP:/home/ec2-user/ChatMRPT/app/static/react/
    
    # Copy updated hooks
    scp -i $KEY_PATH frontend/src/hooks/useMessageStreaming.ts ec2-user@$IP:/home/ec2-user/ChatMRPT/frontend/src/hooks/
    
    # Restart service
    ssh -i $KEY_PATH ec2-user@$IP "sudo systemctl restart chatmrpt"
    
    echo "Deployed to $IP"
done

echo "Deployment complete!"