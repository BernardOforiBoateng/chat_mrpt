#!/bin/bash

# Deploy TPR workflow consistency fixes to AWS
# This script deploys the Phase 1, 2, and 3 fixes for TPR workflow issues

echo "=== Deploying TPR Workflow Consistency Fixes to AWS ==="
echo "Fixes include:"
echo "1. Session persistence with session.modified = True"
echo "2. Enhanced intent classification for state names"
echo "3. Smart session state management for page refresh"
echo ""

# Configuration
AWS_HOST="3.137.158.17"
AWS_USER="ec2-user"
AWS_KEY_PATH="/tmp/chatmrpt-key2.pem"
REMOTE_PROJECT_DIR="/home/ec2-user/ChatMRPT"

# Files to deploy
FILES_TO_DEPLOY=(
    "app/tpr_module/integration/tpr_handler.py"
    "app/tpr_module/integration/tpr_workflow_router.py"
    "app/web/routes/core_routes.py"
)

echo "Deploying the following files:"
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo "  - $file"
done
echo ""

# Check if AWS key exists
if [ ! -f "$AWS_KEY_PATH" ]; then
    echo "Error: AWS key not found at $AWS_KEY_PATH"
    echo "Please ensure your AWS key is in the correct location"
    exit 1
fi

# Deploy each file
echo "=== Deploying Files ==="
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo "Deploying $file..."
    scp -i "$AWS_KEY_PATH" "$file" "$AWS_USER@$AWS_HOST:$REMOTE_PROJECT_DIR/$file"
    if [ $? -eq 0 ]; then
        echo "✓ Successfully deployed $file"
    else
        echo "✗ Failed to deploy $file"
        exit 1
    fi
done

echo ""
echo "=== Restarting Gunicorn on AWS ==="
ssh -i "$AWS_KEY_PATH" "$AWS_USER@$AWS_HOST" << 'EOF'
    # Restart Gunicorn to load the new code
    echo "Stopping Gunicorn..."
    pkill -f gunicorn || true
    
    sleep 2
    
    echo "Starting Gunicorn with 4 workers..."
    cd /home/ec2-user/ChatMRPT
    source /home/ec2-user/chatmrpt_env/bin/activate
    nohup gunicorn 'run:app' --bind=0.0.0.0:80 --workers=4 --timeout=300 --worker-class=sync --log-file=/home/ec2-user/gunicorn.log --log-level=info > /dev/null 2>&1 &
    
    sleep 3
    
    # Check if Gunicorn started successfully
    if pgrep -f gunicorn > /dev/null; then
        echo "✓ Gunicorn restarted successfully"
        echo "Gunicorn processes:"
        ps aux | grep gunicorn | grep -v grep
    else
        echo "✗ Failed to start Gunicorn"
        tail -20 /home/ec2-user/gunicorn.log
        exit 1
    fi
    
    # Show recent TPR-related log entries
    echo ""
    echo "=== Recent TPR Log Entries ==="
    grep -i "TPR" /home/ec2-user/gunicorn.log | tail -10
EOF

echo ""
echo "=== Deployment Complete ==="
echo "TPR workflow consistency fixes have been deployed to AWS."
echo ""
echo "Test the fixes by:"
echo "1. Upload a TPR file"
echo "2. When prompted for state, just type 'Adamawa' (without 'State')"
echo "3. Refresh the browser - TPR workflow should remain active"
echo "4. Continue selecting facility level and age group"
echo "5. Verify downloads persist in the download tab"
echo ""
echo "Monitor logs with:"
echo "ssh -i ~/.ssh/chatmrpt-aws.pem ec2-user@3.137.158.17 'tail -f /home/ec2-user/gunicorn.log | grep -E \"(TPR|Intent|session)\"'"
echo ""
echo "Key improvements:"
echo "✓ Session persistence in multi-worker environment"
echo "✓ State names never trigger 'paused TPR' message"
echo "✓ Page refresh preserves TPR workflow state"
echo "✓ Download links persist across requests"
echo "✓ Enhanced logging for debugging"