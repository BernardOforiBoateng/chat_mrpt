#!/bin/bash

# Deploy Refactored Frontend to AWS Production
echo "🚀 Deploying Refactored Frontend to AWS Production..."
echo "====================================================="

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

echo "📦 Deploying new modular CSS structure..."
echo ""

for instance in $INSTANCE_1 $INSTANCE_2; do
    echo "🔄 Deploying to $instance..."
    
    # Deploy new CSS modules
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
        app/static/css/base-theme.css \
        app/static/css/layout.css \
        app/static/css/components.css \
        app/static/css/chat-interface.css \
        app/static/css/utilities.css \
        app/static/css/arena.css \
        ec2-user@$instance:/home/ec2-user/ChatMRPT/app/static/css/
    
    # Deploy updated index.html
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
        app/templates/index.html \
        ec2-user@$instance:/home/ec2-user/ChatMRPT/app/templates/
    
    # Remove old CSS files on server
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$instance << 'EOF'
    cd /home/ec2-user/ChatMRPT/app/static/css/
    # Backup old files
    mkdir -p /home/ec2-user/backups/css_$(date +%Y%m%d)
    mv modern-minimalist-theme.css /home/ec2-user/backups/css_$(date +%Y%m%d)/ 2>/dev/null || true
    mv style.css /home/ec2-user/backups/css_$(date +%Y%m%d)/ 2>/dev/null || true
    mv vertical-nav.css /home/ec2-user/backups/css_$(date +%Y%m%d)/ 2>/dev/null || true
    echo "✅ Old CSS files archived"
EOF
    
    echo "  ✅ Deployed to $instance"
done

echo ""
echo "✅ Refactoring deployed successfully!"
echo ""
echo "📊 WHAT'S CHANGED:"
echo "  ✅ Arena UI fixed - buttons now horizontal"
echo "  ✅ CSS modularized - all files under 600 lines"
echo "  ✅ Redundant files removed"
echo "  ✅ Better code organization"
echo ""
echo "📌 ACCESS URLS:"
echo "  CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "  Direct ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "⚠️ IMPORTANT: Clear browser cache (Ctrl+Shift+R) to see changes!"
echo "