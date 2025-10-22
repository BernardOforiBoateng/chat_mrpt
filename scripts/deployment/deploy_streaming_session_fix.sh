#!/bin/bash

echo "🚀 Deploying streaming endpoint session fix to AWS..."

# AWS configuration
AWS_IP="3.137.158.17"
KEY_PATH="aws_files/chatmrpt-key.pem"
REMOTE_USER="ubuntu"
REMOTE_DIR="/home/ubuntu/ChatMRPT"

# Fix key permissions
chmod 600 "$KEY_PATH" 2>/dev/null || true

echo "📦 Copying updated analysis_routes.py..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
    app/web/routes/analysis_routes.py \
    "$REMOTE_USER@$AWS_IP:$REMOTE_DIR/app/web/routes/"

echo "🔄 Restarting application..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$REMOTE_USER@$AWS_IP" << 'EOF'
cd /home/ubuntu/ChatMRPT
sudo supervisorctl restart chatmrpt
sleep 5
sudo supervisorctl status chatmrpt
echo "✅ Deployment complete!"
EOF

echo "🎯 Streaming session fix deployed successfully!"