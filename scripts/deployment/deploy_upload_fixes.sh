#!/bin/bash
# Deploy React upload fixes to AWS production instances

set -e

echo "=== Deploying Upload Fixes to AWS Production ==="
echo "Date: $(date)"
echo ""

# Production instances from CLAUDE.md
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"
KEY_FILE="/tmp/chatmrpt-key2.pem"

# Copy key file to temp location
cp aws_files/chatmrpt-key.pem $KEY_FILE
chmod 600 $KEY_FILE

echo "📦 Building React application with fixes..."
cd frontend
npm run build
cd ..

echo ""
echo "🚀 Deploying to production instances..."

# Deploy to both instances
for IP in $INSTANCE_1 $INSTANCE_2; do
    echo ""
    echo "=== Deploying to $IP ==="
    
    # Copy the built React files
    echo "Copying React build files..."
    scp -i $KEY_FILE -r app/static/react/* ec2-user@$IP:/home/ec2-user/ChatMRPT/app/static/react/
    
    # Restart the service
    echo "Restarting ChatMRPT service..."
    ssh -i $KEY_FILE ec2-user@$IP "sudo systemctl restart chatmrpt"
    
    echo "✅ Deployed to $IP"
done

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "📋 Testing URLs:"
echo "  - CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "  - ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "🧪 Test the upload fixes:"
echo "  1. Open the app in a browser"
echo "  2. Click upload button"
echo "  3. Test Standard Upload - should send __DATA_UPLOADED__ message"
echo "  4. Test Data Analysis Upload - should call /api/v1/data-analysis/chat"
echo "  5. Check browser console for debug messages"