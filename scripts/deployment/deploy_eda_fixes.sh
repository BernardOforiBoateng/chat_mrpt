#\!/bin/bash

# Deploy EDA Fixes to Staging
echo "=========================================="
echo "DEPLOYING EDA ANALYSIS & MODAL FIXES"
echo "=========================================="

# Staging server IPs
STAGING_IP_1="3.21.167.170"
STAGING_IP_2="18.220.103.20"

KEY_PATH="/tmp/chatmrpt-key2.pem"

# Copy key
cp aws_files/chatmrpt-key.pem $KEY_PATH
chmod 600 $KEY_PATH

echo "📦 Deploying EDA output and modal auto-close fixes..."

# Function to deploy to instance
deploy_to_instance() {
    local IP=$1
    local NAME=$2
    
    echo ""
    echo "📤 Deploying to $NAME ($IP)..."
    
    # Copy fixed executor (mock code generator fix)
    scp -o StrictHostKeyChecking=no -i $KEY_PATH \
        app/data_analysis_module/executor.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/data_analysis_module/
    
    # Copy fixed JavaScript (modal auto-close)
    scp -o StrictHostKeyChecking=no -i $KEY_PATH \
        app/static/js/modules/data-analysis-upload.js \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/static/js/modules/
    
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
echo "✅ EDA FIXES DEPLOYED\!"
echo "=========================================="
echo ""
echo "Fixed issues:"
echo "• EDA now shows actual analysis output (fixed syntax error in mock code)"
echo "• Upload modal automatically closes after successful analysis"
echo "• Multi-sheet Excel files properly analyzed"
echo ""
echo "Test at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
