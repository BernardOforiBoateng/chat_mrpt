#!/bin/bash

# Deploy Redis State Manager Integration directly to Production
echo "Deploying Redis Integration Fix to PRODUCTION"
echo "============================================="

# Files to deploy
FILES="app/tools/complete_analysis_tools.py app/tools/itn_planning_tools.py app/core/redis_state_manager.py"

# Use staging as jump host
STAGING_IP="3.21.167.170"
PROD_IPS="172.31.44.52 172.31.43.200"
KEY="/tmp/chatmrpt-key2.pem"

echo "Copying files to staging for transfer..."
for file in $FILES; do
    echo "  - $file"
    scp -i "$KEY" "$file" "ec2-user@$STAGING_IP:/tmp/$(basename $file)"
done

echo ""
echo "Deploying to production instances..."

# Deploy to each production instance
ssh -i "$KEY" "ec2-user@$STAGING_IP" << 'ENDSSH'
    # Production IPs
    for PROD_IP in 172.31.44.52 172.31.43.200; do
        echo "Deploying to production: $PROD_IP"
        
        # Copy files
        scp -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem \
            /tmp/complete_analysis_tools.py \
            ec2-user@$PROD_IP:/home/ec2-user/ChatMRPT/app/tools/complete_analysis_tools.py
            
        scp -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem \
            /tmp/itn_planning_tools.py \
            ec2-user@$PROD_IP:/home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py
            
        scp -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem \
            /tmp/redis_state_manager.py \
            ec2-user@$PROD_IP:/home/ec2-user/ChatMRPT/app/core/redis_state_manager.py
        
        # Restart service
        ssh -o StrictHostKeyChecking=no -i ~/.ssh/chatmrpt-key.pem \
            ec2-user@$PROD_IP 'sudo systemctl restart chatmrpt'
            
        echo "✓ Deployed to $PROD_IP"
    done
    
    echo "Production deployment complete!"
ENDSSH

echo ""
echo "====================================="
echo "✓ Redis Integration Fix Deployed!"
echo "====================================="
echo ""
echo "What this fixes:"
echo "  - Analysis won't re-run when asking for bed net planning"
echo "  - Workers now share state through Redis"
echo ""
echo "Test at: https://d225ar6c86586s.cloudfront.net"