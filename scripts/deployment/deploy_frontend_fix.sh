#!/bin/bash
# Deploy frontend fix to production instances
# This script deploys the fixed React build to both production instances

set -e

echo "=========================================="
echo "Deploying Data Analysis Frontend Fix"
echo "=========================================="
echo ""

# Production instance IPs (from CLAUDE.md)
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"

# Check if SSH key exists
KEY_PATH="/tmp/chatmrpt-key2.pem"
if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSH key not found at $KEY_PATH"
    echo "Please copy the key file first:"
    echo "cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem"
    echo "chmod 600 /tmp/chatmrpt-key2.pem"
    exit 1
fi

echo "📦 Preparing deployment package..."
# Create a temporary directory for the build files
TEMP_DIR=$(mktemp -d)
cp -r app/static/react/* $TEMP_DIR/

echo "✅ Build files prepared"
echo ""

# Function to deploy to an instance
deploy_to_instance() {
    local IP=$1
    local INSTANCE_NAME=$2
    
    echo "=== Deploying to $INSTANCE_NAME ($IP) ==="
    
    # Copy the build files
    echo "📤 Copying React build files..."
    scp -i $KEY_PATH -r $TEMP_DIR/* ec2-user@$IP:/home/ec2-user/ChatMRPT/app/static/react/
    
    if [ $? -eq 0 ]; then
        echo "✅ Files copied successfully"
    else
        echo "❌ Failed to copy files to $INSTANCE_NAME"
        return 1
    fi
    
    # Restart the service
    echo "🔄 Restarting ChatMRPT service..."
    ssh -i $KEY_PATH ec2-user@$IP "sudo systemctl restart chatmrpt"
    
    if [ $? -eq 0 ]; then
        echo "✅ Service restarted successfully"
    else
        echo "⚠️ Failed to restart service on $INSTANCE_NAME"
    fi
    
    # Verify the service is running
    echo "🔍 Verifying service status..."
    ssh -i $KEY_PATH ec2-user@$IP "sudo systemctl status chatmrpt | grep Active"
    
    echo "✅ Deployment to $INSTANCE_NAME complete"
    echo ""
}

# Deploy to both instances
echo "📋 Starting deployment to production instances..."
echo ""

# Deploy to Instance 1
deploy_to_instance $INSTANCE_1 "Instance 1"

# Deploy to Instance 2
deploy_to_instance $INSTANCE_2 "Instance 2"

# Clean up
rm -rf $TEMP_DIR

echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "The Data Analysis upload fix has been deployed to both production instances."
echo ""
echo "Test the fix at:"
echo "  CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "  ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "To verify the fix:"
echo "1. Navigate to the Data Analysis tab"
echo "2. Upload a CSV file"
echo "3. Confirm that analysis results appear in the chat"
echo ""