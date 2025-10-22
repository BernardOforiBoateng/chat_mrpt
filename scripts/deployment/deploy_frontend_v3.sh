#!/bin/bash

# Deploy Data Analysis V3 Frontend Updates
echo "=========================================="
echo "Deploying Frontend Updates for Data Analysis V3"
echo "=========================================="

# Configuration
STAGING_IPS="3.21.167.170 18.220.103.20"
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Files to deploy
echo "📦 Preparing frontend files..."

# Deploy to each staging instance
for IP in $STAGING_IPS; do
    echo ""
    echo "🚀 Deploying frontend to $IP..."
    
    # Copy files
    echo "📤 Copying files..."
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
        app/static/js/modules/upload/data-analysis-upload.js \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/static/js/modules/upload/
    
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
        app/templates/index.html \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/templates/
    
    # Restart service to apply changes
    echo "🔄 Restarting service..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$IP "sudo systemctl restart chatmrpt"
    
    echo "✅ Frontend deployed to $IP"
done

echo ""
echo "=========================================="
echo "✅ Frontend Deployment Complete!"
echo "=========================================="
echo ""
echo "📋 How to Test Data Analysis V3:"
echo ""
echo "1. Go to: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "2. Click the Upload button (cloud icon) in the toolbar"
echo ""
echo "3. Select the 'Data Analysis' tab"
echo ""
echo "4. Upload a CSV or Excel file"
echo ""
echo "5. After upload, ask questions like:"
echo "   - 'What's in my data?'"
echo "   - 'Show me summary statistics'"
echo "   - 'Which areas have highest values?'"
echo "   - 'Create a bar chart'"
echo ""
echo "The system will use the new LangGraph agent to analyze your data!"