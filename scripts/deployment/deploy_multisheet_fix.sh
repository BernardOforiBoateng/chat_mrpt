#\!/bin/bash

# Deploy Multi-Sheet Excel Fix to Staging
echo "=========================================="
echo "DEPLOYING MULTI-SHEET EXCEL FIX"
echo "=========================================="

# Staging server IPs
STAGING_IP_1="3.21.167.170"
STAGING_IP_2="18.220.103.20"

KEY_PATH="/tmp/chatmrpt-key2.pem"

# Copy key
cp aws_files/chatmrpt-key.pem $KEY_PATH
chmod 600 $KEY_PATH

echo "📦 Deploying multi-sheet Excel handling fix..."

# Function to deploy to instance
deploy_to_instance() {
    local IP=$1
    local NAME=$2
    
    echo ""
    echo "📤 Deploying to $NAME ($IP)..."
    
    # Copy updated executor with multi-sheet support
    scp -o StrictHostKeyChecking=no -i $KEY_PATH \
        app/data_analysis_module/executor.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/data_analysis_module/
    
    # Copy updated prompts
    scp -o StrictHostKeyChecking=no -i $KEY_PATH \
        app/data_analysis_module/prompts.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/data_analysis_module/
    
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
echo "✅ MULTI-SHEET EXCEL FIX DEPLOYED\!"
echo "=========================================="
echo ""
echo "Changes:"
echo "• Excel files with multiple sheets now fully accessible to LLM"
echo "• All sheets loaded as dictionary for analysis"
echo "• LLM can analyze any/all sheets as needed"
echo "• Automatic sheet detection and info display"
echo ""
echo "Test at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "Upload the NMEP file to see all sheets properly analyzed"
