#!/bin/bash

# Deploy Arena UI Improvements to Production
echo "==========================================="
echo "Deploying Arena UI Improvements"
echo "==========================================="

# Production instance IPs
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

# Key location
KEY="/tmp/chatmrpt-key.pem"

# Copy key to temp location with proper permissions
cp aws_files/chatmrpt-key.pem $KEY
chmod 600 $KEY

echo ""
echo "📦 Files to deploy:"
echo "  - app/static/css/style.css (Professional Arena styling)"
echo "  - app/static/js/modules/chat/core/message-handler.js (Updated labels and structure)"
echo ""

# Deploy to each instance
for IP in $INSTANCE1 $INSTANCE2; do
    echo "🚀 Deploying to instance: $IP"
    
    # Copy CSS file
    echo "  📄 Copying style.css..."
    scp -i $KEY -o StrictHostKeyChecking=no \
        app/static/css/style.css \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/static/css/
    
    # Copy JavaScript file
    echo "  📄 Copying message-handler.js..."
    scp -i $KEY -o StrictHostKeyChecking=no \
        app/static/js/modules/chat/core/message-handler.js \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/static/js/modules/chat/core/
    
    # Restart the service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i $KEY -o StrictHostKeyChecking=no ec2-user@$IP \
        "sudo systemctl restart chatmrpt"
    
    echo "  ✅ Deployment to $IP complete!"
    echo ""
done

echo "==========================================="
echo "✅ Arena UI Improvements Deployed!"
echo "==========================================="
echo ""
echo "Key improvements deployed:"
echo "  • Professional card-based design with shadows"
echo "  • 'Assistant A/B' labels instead of 'Response A/B'"
echo "  • Better voting buttons: 'Left/Right is Better', etc."
echo "  • Arena mode indicator with 'Blind Test' badge"
echo "  • Smooth animations and transitions"
echo "  • Improved mobile responsiveness"
echo ""
echo "🌐 Access via:"
echo "  - CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "  - ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "Note: CloudFront may cache old files. Use ALB URL for immediate testing."