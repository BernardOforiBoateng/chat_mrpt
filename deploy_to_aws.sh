#!/bin/bash
# Deploy TPR session persistence fixes to AWS

echo "=== Deploying TPR Session Persistence Fixes to AWS ==="
echo "This script will copy the deployment script to AWS and execute it"

# Copy the deployment script to AWS
echo "1. Copying deployment script to AWS..."
scp -i /tmp/chatmrpt-key2.pem deploy_tpr_fixes.sh ec2-user@3.137.158.17:~/

# Execute the deployment script on AWS
echo "2. Executing deployment script on AWS..."
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 'cd ~/ChatMRPT && chmod +x ~/deploy_tpr_fixes.sh && ~/deploy_tpr_fixes.sh'

echo "Deployment complete!"