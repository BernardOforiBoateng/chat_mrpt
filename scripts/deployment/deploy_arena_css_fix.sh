#!/bin/bash

# Deploy Arena CSS Fix - Proper Button Layout
echo "🎨 Deploying Arena CSS Fix to AWS Production..."
echo "================================================="

# Production instances
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Check key
if [ ! -f "$KEY_PATH" ]; then
    if [ -f "aws_files/chatmrpt-key.pem" ]; then
        cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
        chmod 600 /tmp/chatmrpt-key2.pem
    fi
fi

echo "📦 Deploying corrected CSS files..."
echo ""

for instance in $INSTANCE_1 $INSTANCE_2; do
    echo "🔄 Deploying to $instance..."
    
    # Deploy the corrected modern-minimalist-theme.css
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
        app/static/css/modern-minimalist-theme.css \
        ec2-user@$instance:/home/ec2-user/ChatMRPT/app/static/css/
    
    # Also deploy arena.css as backup
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
        app/static/css/arena.css \
        ec2-user@$instance:/home/ec2-user/ChatMRPT/app/static/css/
    
    echo "  ✅ CSS deployed to $instance"
done

echo ""
echo "✅ Arena CSS fix deployed!"
echo ""
echo "🎯 What's fixed:"
echo "  ✅ Horizontal button layout (not vertical list)"
echo "  ✅ Proper button styling with borders and hover effects"
echo "  ✅ Correct spacing and alignment"
echo "  ✅ View counter separated from voting buttons"
echo ""
echo "⚠️ IMPORTANT: Clear browser cache and hard refresh!"
echo "  Use: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "  (Direct ALB avoids CloudFront cache)"
echo ""