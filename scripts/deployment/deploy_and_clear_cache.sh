#!/bin/bash

echo "=== Deploying New React Build with Upload Modal ==="
echo ""

# Copy SSH key to temp location
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Production IPs
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

echo "1. Deploying to Production Instance 1 ($INSTANCE1)..."
# Copy React build files
scp -i /tmp/chatmrpt-key2.pem -r app/static/react/* ec2-user@$INSTANCE1:/home/ec2-user/ChatMRPT/app/static/react/
# Copy updated frontend components
scp -i /tmp/chatmrpt-key2.pem frontend/src/components/Sidebar/Sidebar.tsx ec2-user@$INSTANCE1:/home/ec2-user/ChatMRPT/frontend/src/components/Sidebar/
scp -i /tmp/chatmrpt-key2.pem frontend/src/components/Modal/UploadModal.tsx ec2-user@$INSTANCE1:/home/ec2-user/ChatMRPT/frontend/src/components/Modal/
scp -i /tmp/chatmrpt-key2.pem frontend/src/components/Chat/InputArea.tsx ec2-user@$INSTANCE1:/home/ec2-user/ChatMRPT/frontend/src/components/Chat/
# Restart service
ssh -i /tmp/chatmrpt-key2.pem ec2-user@$INSTANCE1 'sudo systemctl restart chatmrpt'
echo "Instance 1 deployment complete."
echo ""

echo "2. Deploying to Production Instance 2 ($INSTANCE2)..."
# Copy React build files
scp -i /tmp/chatmrpt-key2.pem -r app/static/react/* ec2-user@$INSTANCE2:/home/ec2-user/ChatMRPT/app/static/react/
# Copy updated frontend components
scp -i /tmp/chatmrpt-key2.pem frontend/src/components/Sidebar/Sidebar.tsx ec2-user@$INSTANCE2:/home/ec2-user/ChatMRPT/frontend/src/components/Sidebar/
scp -i /tmp/chatmrpt-key2.pem frontend/src/components/Modal/UploadModal.tsx ec2-user@$INSTANCE2:/home/ec2-user/ChatMRPT/frontend/src/components/Modal/
scp -i /tmp/chatmrpt-key2.pem frontend/src/components/Chat/InputArea.tsx ec2-user@$INSTANCE2:/home/ec2-user/ChatMRPT/frontend/src/components/Chat/
# Restart service
ssh -i /tmp/chatmrpt-key2.pem ec2-user@$INSTANCE2 'sudo systemctl restart chatmrpt'
echo "Instance 2 deployment complete."
echo ""

echo "3. Creating CloudFront invalidation..."
echo ""
echo "Since AWS CLI is not configured locally, please run this command from an EC2 instance:"
echo ""
echo "ssh -i /tmp/chatmrpt-key2.pem ec2-user@$INSTANCE1"
echo "aws cloudfront create-invalidation --distribution-id E3JGYN03YJG5E2 --paths '/*'"
echo ""
echo "Or use the AWS Console:"
echo "1. Go to CloudFront in AWS Console"
echo "2. Select distribution E3JGYN03YJG5E2"
echo "3. Go to Invalidations tab"
echo "4. Create invalidation with path: /*"
echo ""

# Also clear any local browser cache
echo "4. Clear your browser cache:"
echo "   - Chrome: Ctrl+Shift+Delete → Cached images and files → Clear data"
echo "   - Firefox: Ctrl+Shift+Delete → Cache → Clear Now"
echo "   - Safari: Develop → Empty Caches"
echo ""
echo "5. After CloudFront invalidation completes (2-3 minutes), try:"
echo "   - https://d225ar6c86586s.cloudfront.net/?v=$(date +%s)"
echo "   - This adds a cache-busting parameter to force fresh load"
echo ""

echo "Deployment complete! New upload modal should be visible after cache clear."