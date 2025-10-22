#!/bin/bash

echo "=== Deploying Staging to Production ==="

# Copy everything from staging to production via bastion approach
STAGING_IP="3.21.167.170"
PROD_IPS=("172.31.44.52" "172.31.43.200")

echo "Step 1: Copying files from staging to production instances..."

# For each production instance
for PROD_IP in "${PROD_IPS[@]}"; do
    echo ""
    echo "Deploying to Production Instance: $PROD_IP"
    
    # SSH to staging, then copy to production from there
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@${STAGING_IP} << DEPLOY_EOF
        echo "Syncing ChatMRPT directory to $PROD_IP..."
        
        # First ensure SSH key is available
        if [ ! -f ~/.ssh/chatmrpt-key.pem ]; then
            echo "Setting up SSH key..."
            cp /home/ec2-user/ChatMRPT/aws_files/chatmrpt-key.pem ~/.ssh/ 2>/dev/null || true
            chmod 600 ~/.ssh/chatmrpt-key.pem 2>/dev/null || true
        fi
        
        # Sync the entire ChatMRPT folder
        rsync -avz \
            --exclude='instance/uploads/*/*' \
            --exclude='instance/*.db' \
            --exclude='instance/app.log' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='venv/' \
            --exclude='.git/' \
            /home/ec2-user/ChatMRPT/ \
            ec2-user@${PROD_IP}:/home/ec2-user/ChatMRPT/
        
        # Restart service
        ssh ec2-user@${PROD_IP} "sudo systemctl restart chatmrpt"
        
        echo "✅ Deployment complete for $PROD_IP"
DEPLOY_EOF
done

echo ""
echo "Step 2: Verifying deployment..."
sleep 10

# Test the load balancer
echo "Testing production ALB..."
for i in {1..3}; do
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/ping)
    echo "  Attempt $i: HTTP $HTTP_CODE"
    sleep 2
done

echo ""
echo "✅ Deployment complete!"
echo "Access at: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"
