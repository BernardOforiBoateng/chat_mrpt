#!/bin/bash
# Simple fix for TPR to risk analysis transition
# Sets user_message to __DATA_UPLOADED__ when TPR completes

echo "🚀 Deploying simple TPR transition fix to AWS..."

# AWS connection details
AWS_IP="3.137.158.17"
SSH_KEY="aws_files/chatmrpt-key.pem"

# Copy the fixed analysis_routes.py file
echo "📤 Copying fixed analysis_routes.py..."
scp -i $SSH_KEY app/web/routes/analysis_routes.py ubuntu@$AWS_IP:/home/ubuntu/ChatMRPT/app/web/routes/

# SSH to AWS and restart the service
echo "🔄 Restarting application..."
ssh -i $SSH_KEY ubuntu@$AWS_IP << 'EOF'
cd /home/ubuntu/ChatMRPT

# Restart the application
echo "Restarting application..."
sudo systemctl restart gunicorn

# Check status
echo "Checking application status..."
sudo systemctl status gunicorn | head -20

echo "✅ Simple TPR transition fix deployed successfully!"
echo "The fix ensures that when TPR completes and user says 'yes', the message '__DATA_UPLOADED__' is passed to the main interpreter to show the exploration menu."
EOF

echo "🎉 Deployment complete!"