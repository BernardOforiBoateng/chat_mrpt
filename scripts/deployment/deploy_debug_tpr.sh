#!/bin/bash

echo "Deploying TPR debug to production instances..."

# Copy file to staging first
echo "1. Copying to staging..."
scp -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no \
    app/data_analysis_v3/core/tpr_workflow_handler.py \
    ec2-user@3.21.167.170:/tmp/tpr_workflow_handler_debug.py

# Deploy to each production instance from staging
for ip in 172.31.44.52 172.31.43.200; do
    echo ""
    echo "2. Deploying to production instance: $ip"
    
    ssh -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no ec2-user@3.21.167.170 << EOF
        echo "   - Copying file to $ip..."
        scp -i ~/.ssh/chatmrpt-key.pem -o ConnectTimeout=10 \
            /tmp/tpr_workflow_handler_debug.py \
            ec2-user@$ip:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_workflow_handler.py
        
        echo "   - Restarting service on $ip..."
        ssh -i ~/.ssh/chatmrpt-key.pem -o ConnectTimeout=10 ec2-user@$ip \
            'sudo systemctl restart chatmrpt'
        
        echo "   ✅ Deployed to $ip"
EOF
done

echo ""
echo "3. Deployment complete!"