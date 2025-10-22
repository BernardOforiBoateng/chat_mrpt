#!/bin/bash
set -e

echo "=========================================="
echo "Deploying Frontend Visualization Fixes"
echo "=========================================="

# Production instance IPs
INSTANCE_IPS=("3.21.167.170" "18.220.103.20")

KEY_FILE="/tmp/chatmrpt-key.pem"

# Copy SSH key if not there
if [ ! -f "$KEY_FILE" ]; then
    cp aws_files/chatmrpt-key.pem "$KEY_FILE"
    chmod 600 "$KEY_FILE"
fi

echo "Deploying React build to AWS instances..."

for ip in "${INSTANCE_IPS[@]}"; do
    echo ""
    echo "Deploying to instance: $ip"
    echo "--------------------------------"
    
    # Copy the built React files
    echo "  Copying React build files..."
    scp -i "$KEY_FILE" -r app/static/react/* "ec2-user@$ip:/home/ec2-user/ChatMRPT/app/static/react/"
    
    # Clear CloudFront cache for immediate update
    echo "  Service should auto-reload static files"
    
    echo "  ✓ Instance $ip deployment complete"
done

echo ""
echo "=========================================="
echo "✓ Frontend fixes deployed to all instances!"
echo "=========================================="
echo ""
echo "IMPORTANT: Clear browser cache or use incognito to test!"
echo "Test at: https://d225ar6c86586s.cloudfront.net"
