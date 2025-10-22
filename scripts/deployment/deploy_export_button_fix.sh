#!/bin/bash

# Deploy export download and button text fixes

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Deploying export download fixes to AWS...${NC}"

# AWS instance details
AWS_HOST="ec2-user@3.137.158.17"
KEY_PATH="aws_files/ChatMRPT-key.pem"

echo -e "${GREEN}1. Uploading fixed export routes...${NC}"
scp -i "$KEY_PATH" app/web/routes/export_routes.py "$AWS_HOST":~/ChatMRPT/app/web/routes/

echo -e "${GREEN}2. Uploading fixed reports API routes...${NC}"
scp -i "$KEY_PATH" app/web/routes/reports_api_routes.py "$AWS_HOST":~/ChatMRPT/app/web/routes/

echo -e "${GREEN}3. Uploading updated JavaScript...${NC}"
scp -i "$KEY_PATH" app/static/js/app.js "$AWS_HOST":~/ChatMRPT/app/static/js/

echo -e "${GREEN}4. Restarting services on AWS...${NC}"
ssh -i "$KEY_PATH" "$AWS_HOST" << 'EOF'
cd ~/ChatMRPT
source chatmrpt_venv_new/bin/activate

# Restart gunicorn
echo "Restarting gunicorn..."
pkill -f gunicorn
nohup gunicorn 'run:app' --bind=0.0.0.0:8080 --timeout 300 --workers 3 > gunicorn.log 2>&1 &

# Wait for service to start
sleep 5

# Check if running
if pgrep -f gunicorn > /dev/null; then
    echo "✅ Gunicorn restarted successfully"
else
    echo "❌ Failed to restart gunicorn"
fi
EOF

echo -e "${GREEN}✅ Deployment complete!${NC}"
echo -e "${YELLOW}Fixes deployed:${NC}"
echo "- Export route now searches in subdirectories for files"
echo "- Report generation defaults to 'export' format"
echo "- Button text changed to 'Download Analysis Package'"