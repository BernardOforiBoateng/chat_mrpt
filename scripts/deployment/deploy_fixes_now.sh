#!/bin/bash

# Deploy export fixes to AWS

# Copy key to temp location with proper permissions
cp aws_files/ChatMRPT-key.pem /tmp/deploy-key.pem
chmod 600 /tmp/deploy-key.pem

# AWS instance details
AWS_HOST="ec2-user@3.137.158.17"
KEY_PATH="/tmp/deploy-key.pem"

echo "Deploying fixes to AWS..."

# Upload files
echo "1. Uploading export_routes.py..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no app/web/routes/export_routes.py "$AWS_HOST":~/ChatMRPT/app/web/routes/

echo "2. Uploading reports_api_routes.py..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no app/web/routes/reports_api_routes.py "$AWS_HOST":~/ChatMRPT/app/web/routes/

echo "3. Uploading app.js..."
scp -i "$KEY_PATH" -o StrictHostKeyChecking=no app/static/js/app.js "$AWS_HOST":~/ChatMRPT/app/static/js/

echo "4. Restarting service..."
ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "$AWS_HOST" << 'EOF'
cd ~/ChatMRPT
source chatmrpt_venv_new/bin/activate

# Kill existing gunicorn
pkill -f gunicorn || true

# Start gunicorn
nohup gunicorn 'run:app' --bind=0.0.0.0:8080 --timeout 300 --workers 3 > gunicorn.log 2>&1 &

sleep 3
echo "Service restarted successfully"
EOF

# Cleanup
rm -f /tmp/deploy-key.pem

echo "Deployment complete!"