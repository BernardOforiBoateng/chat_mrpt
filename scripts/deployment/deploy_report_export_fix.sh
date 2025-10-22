#!/bin/bash

# Deploy report export fix to AWS
# This fixes:
# 1. Report button calling API directly instead of chat
# 2. ModernReportGenerator instantiation
# 3. Download URL mapping
# 4. Frontend export package UI

# AWS connection details
SSH_KEY="/mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT/aws_files/kano-app.pem"
REMOTE_HOST="ec2-user@3.137.158.17"
PROJECT_DIR="/home/ec2-user/ChatMRPT"

echo "📦 Starting deployment of report export fixes..."

# Files to deploy
FILES=(
    "app/services/container.py"
    "app/services/reports/modern_generator.py"
    "app/web/routes/reports_api_routes.py"
    "app/static/js/app.js"
)

# Deploy each file
for file in "${FILES[@]}"; do
    echo "📤 Deploying $file..."
    scp -i "$SSH_KEY" "$file" "$REMOTE_HOST:$PROJECT_DIR/$file"
    if [ $? -eq 0 ]; then
        echo "✅ $file deployed successfully"
    else
        echo "❌ Failed to deploy $file"
        exit 1
    fi
done

# Restart the application
echo "🔄 Restarting application..."
ssh -i "$SSH_KEY" "$REMOTE_HOST" << 'ENDSSH'
cd /home/ec2-user/ChatMRPT
source chatmrpt_venv_new/bin/activate

# Kill existing gunicorn processes
echo "Stopping existing processes..."
pkill -f gunicorn || true
sleep 2

# Start with single worker for session consistency
echo "Starting application with single worker..."
nohup gunicorn 'run:app' \
    --bind=0.0.0.0:5000 \
    --workers=1 \
    --worker-class=sync \
    --timeout=300 \
    --graceful-timeout=30 \
    --keep-alive=5 \
    --log-level=info \
    --access-logfile=logs/access.log \
    --error-logfile=logs/error.log \
    > logs/gunicorn.log 2>&1 &

echo "Waiting for application to start..."
sleep 5

# Check if running
if pgrep -f gunicorn > /dev/null; then
    echo "✅ Application started successfully"
    echo "🌐 Application running at http://3.137.158.17:5000"
else
    echo "❌ Failed to start application"
    exit 1
fi
ENDSSH

echo "🎉 Deployment complete!"
echo ""
echo "✨ Fixed in this deployment:"
echo "  - Report button now calls API directly"
echo "  - ModernReportGenerator properly instantiated"
echo "  - Download URLs correctly mapped"
echo "  - Export package UI shows proper message"
echo ""
echo "📋 Test the fix:"
echo "  1. Go to http://3.137.158.17:5000"
echo "  2. Upload data and run analysis"
echo "  3. Run ITN planning (optional)"
echo "  4. Click 'Generate Report' button"
echo "  5. You should see an export package download link"