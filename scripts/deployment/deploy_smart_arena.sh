#!/bin/bash
echo "Deploying Smart Arena Integration (No Hardcoding)..."

# Production instances
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

# Deploy the updated file
for IP in $INSTANCE1 $INSTANCE2; do
    echo "Deploying to $IP..."
    
    # Copy the updated analysis_routes.py
    scp -i /tmp/chatmrpt-key2.pem \
        app/web/routes/analysis_routes.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/web/routes/
    
    # Restart service
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP 'sudo systemctl restart chatmrpt'
    
    echo "✅ Deployed to $IP"
done

echo "✅ Smart Arena deployed! No more hardcoding!"
