#!/bin/bash

echo "=== Deploying Stable Version Setup ==="
echo "This will create a backup accessible at /stable"
echo ""

# Deploy to both production instances
for ip in 3.21.167.170 18.220.103.20; do
    echo "Setting up stable version on $ip..."
    
    # Copy react-stable directory
    echo "  - Copying react-stable directory..."
    scp -i /tmp/chatmrpt-key2.pem -r /mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/static/react-stable ec2-user@$ip:/home/ec2-user/ChatMRPT/app/static/
    
    # Update core_routes.py with stable routes
    echo "  - Updating routes..."
    scp -i /tmp/chatmrpt-key2.pem /mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/app/web/routes/core_routes.py ec2-user@$ip:/home/ec2-user/ChatMRPT/app/web/routes/
    
    # Restart service
    echo "  - Restarting service..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip 'sudo systemctl restart chatmrpt'
    
    echo "✅ Stable version deployed to $ip"
done

echo ""
echo "Creating CloudFront invalidation..."
INVALIDATION_ID=$(ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 "aws cloudfront create-invalidation --distribution-id E10A0JUW3VKH2K --paths '/*' --query 'Invalidation.Id' --output text")
echo "CloudFront invalidation created: $INVALIDATION_ID"

echo ""
echo "🎉 Stable version deployment complete!"
echo ""
echo "Access points:"
echo "  Main (for updates): https://d225ar6c86586s.cloudfront.net"
echo "  Stable (backup):    https://d225ar6c86586s.cloudfront.net/stable"
echo ""
echo "You can now make changes to the main version while the stable"
echo "version remains accessible at /stable"