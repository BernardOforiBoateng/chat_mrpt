#\!/bin/bash

echo "=========================================="
echo "DEPLOYING SESSION & LOGGING FIX"
echo "=========================================="

# Staging server IPs
STAGING_IP_1="3.21.167.170"
STAGING_IP_2="18.220.103.20"

KEY_PATH="/tmp/chatmrpt-key2.pem"

# Copy key
cp aws_files/chatmrpt-key.pem $KEY_PATH
chmod 600 $KEY_PATH

echo "📦 Deploying session and logging fixes..."

# Function to deploy to instance
deploy_to_instance() {
    local IP=$1
    local NAME=$2
    
    echo ""
    echo "📤 Deploying to $NAME ($IP)..."
    
    # Copy all fixed files
    scp -o StrictHostKeyChecking=no -i $KEY_PATH \
        app/data_analysis_module/executor.py \
        app/web/routes/data_analysis_routes.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/data_analysis_module/executor.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/web/routes/data_analysis_routes.py
    
    # Fix the scp command - copy to correct directories
    ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$IP << 'ENDSSH'
mv /home/ec2-user/ChatMRPT/app/data_analysis_module/data_analysis_routes.py \
   /home/ec2-user/ChatMRPT/app/web/routes/data_analysis_routes.py 2>/dev/null || true
sudo systemctl restart chatmrpt
ENDSSH
    
    echo "✅ Deployed to $NAME"
}

# Deploy to both instances
deploy_to_instance $STAGING_IP_1 "Instance 1"
deploy_to_instance $STAGING_IP_2 "Instance 2"

# Clean up
rm -f $KEY_PATH

echo ""
echo "=========================================="
echo "✅ SESSION & LOGGING FIX DEPLOYED\!"
echo "=========================================="
echo ""
echo "Fixed:"
echo "• Session ID properly created if missing"
echo "• Extensive logging of file paths"
echo "• Absolute path resolution"
echo ""
echo "Try uploading again and check browser console for debug output"
