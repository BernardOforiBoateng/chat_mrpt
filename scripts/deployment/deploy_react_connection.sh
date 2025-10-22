#!/bin/bash

# Deploy React connection and archive old files
echo "Deploying React connection to production instances..."

# Production IPs
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Copy key if not already there
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem $KEY_PATH
    chmod 600 $KEY_PATH
fi

# Deploy to both instances
for IP in $INSTANCE1 $INSTANCE2; do
    echo "Deploying to $IP..."
    
    # Create archive folder structure
    ssh -i $KEY_PATH ec2-user@$IP "mkdir -p /home/ec2-user/ChatMRPT/app/static/archived_old_frontend/{css,js,templates}"
    
    # Archive old CSS files
    ssh -i $KEY_PATH ec2-user@$IP "cd /home/ec2-user/ChatMRPT && mv app/static/css/* app/static/archived_old_frontend/css/ 2>/dev/null || true"
    
    # Archive old JS files
    ssh -i $KEY_PATH ec2-user@$IP "cd /home/ec2-user/ChatMRPT && mv app/static/js/* app/static/archived_old_frontend/js/ 2>/dev/null || true"
    
    # Archive old HTML template
    ssh -i $KEY_PATH ec2-user@$IP "cd /home/ec2-user/ChatMRPT && cp app/templates/index.html app/static/archived_old_frontend/templates/index_old.html 2>/dev/null || true"
    
    # Copy updated Flask route file
    scp -i $KEY_PATH app/web/routes/core_routes.py ec2-user@$IP:/home/ec2-user/ChatMRPT/app/web/routes/
    
    # Copy React build files (in case they need updates)
    scp -i $KEY_PATH -r app/static/react/* ec2-user@$IP:/home/ec2-user/ChatMRPT/app/static/react/
    
    # Restart service
    ssh -i $KEY_PATH ec2-user@$IP "sudo systemctl restart chatmrpt"
    
    echo "Deployed to $IP"
done

echo "Deployment complete!"
echo ""
echo "Next steps:"
echo "1. Test the React app at http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "2. Invalidate CloudFront cache:"
echo "   aws cloudfront create-invalidation --distribution-id E3RH5SBJN1Z9L4 --paths '/*'"