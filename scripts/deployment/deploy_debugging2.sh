#\!/bin/bash

echo "=========================================="
echo "DEPLOYING DEBUGGING FIXES"
echo "=========================================="

# Staging server IPs
STAGING_IP_1="3.21.167.170"
STAGING_IP_2="18.220.103.20"

KEY_PATH="/tmp/chatmrpt-key2.pem"

# Copy key
cp aws_files/chatmrpt-key.pem $KEY_PATH
chmod 600 $KEY_PATH

echo "📦 Deploying debugging fixes..."

# Function to deploy to instance
deploy_to_instance() {
    local IP=$1
    local NAME=$2
    
    echo ""
    echo "📤 Deploying to $NAME ($IP)..."
    
    # Copy executor
    scp -o StrictHostKeyChecking=no -i $KEY_PATH \
        app/data_analysis_module/executor.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/data_analysis_module/
    
    # Copy routes
    scp -o StrictHostKeyChecking=no -i $KEY_PATH \
        app/web/routes/data_analysis_routes.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/web/routes/
    
    # Restart service
    ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$IP \
        "sudo systemctl restart chatmrpt"
    
    echo "✅ Deployed to $NAME"
}

# Deploy to both instances
deploy_to_instance $STAGING_IP_1 "Instance 1"
deploy_to_instance $STAGING_IP_2 "Instance 2"

# Clean up
rm -f $KEY_PATH

echo ""
echo "=========================================="
echo "✅ DEBUGGING DEPLOYED\!"
echo "=========================================="
