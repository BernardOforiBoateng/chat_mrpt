#!/bin/bash

# Deploy TPR Ward Name Matching Fix
# This script deploys the enhanced ward name matching for TPR analysis

echo "====================================="
echo "Deploying TPR Ward Name Matching Fix"
echo "====================================="

# Copy the key file to /tmp if it exists locally
if [ -f "aws_files/chatmrpt-key2.pem" ]; then
    cp aws_files/chatmrpt-key2.pem /tmp/
    chmod 600 /tmp/chatmrpt-key2.pem
    echo "✓ Key file copied to /tmp"
else
    echo "⚠ Key file not found locally, assuming it's already in /tmp"
fi

# SSH connection details
SSH_KEY="/tmp/chatmrpt-key2.pem"
SSH_USER="ec2-user"
SSH_HOST="3.137.158.17"
REMOTE_DIR="/home/ec2-user/ChatMRPT"

echo ""
echo "Deploying enhanced TPR ward name matching..."
echo ""

# Copy the updated TPR pipeline file
echo "1. Copying updated tpr_pipeline.py..."
scp -i "$SSH_KEY" \
    app/tpr_module/core/tpr_pipeline.py \
    "$SSH_USER@$SSH_HOST:$REMOTE_DIR/app/tpr_module/core/"

# Execute commands on the remote server
echo ""
echo "2. Restarting application on AWS..."
ssh -i "$SSH_KEY" "$SSH_USER@$SSH_HOST" << 'ENDSSH'
    cd /home/ec2-user/ChatMRPT
    source /home/ec2-user/chatmrpt_env/bin/activate
    
    # Stop the current application
    echo "Stopping current application..."
    pkill -f gunicorn || true
    sleep 2
    
    # Clear any Python cache
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    
    # Start the application
    echo "Starting application with enhanced ward matching..."
    nohup gunicorn 'run:app' \
        --bind 0.0.0.0:8080 \
        --workers 2 \
        --timeout 300 \
        --log-file /home/ec2-user/ChatMRPT/instance/gunicorn.log \
        --error-logfile /home/ec2-user/ChatMRPT/instance/gunicorn-error.log \
        --access-logfile /home/ec2-user/ChatMRPT/instance/gunicorn-access.log \
        > /home/ec2-user/ChatMRPT/instance/app.log 2>&1 &
    
    sleep 3
    
    # Check if the application started successfully
    if pgrep -f gunicorn > /dev/null; then
        echo "✓ Application restarted successfully"
        echo ""
        echo "Enhanced ward matching features:"
        echo "- Improved normalization (removes WARD, LGA, STATE, special chars)"
        echo "- Fuzzy matching with 0.85 similarity threshold"
        echo "- Detailed logging for debugging"
        echo ""
        echo "Monitor logs for ward matching details:"
        echo "tail -f /home/ec2-user/ChatMRPT/instance/app.log | grep -E 'ward|Ward|match|Match'"
    else
        echo "✗ Failed to start application"
        echo "Check logs: tail -f /home/ec2-user/ChatMRPT/instance/gunicorn-error.log"
        exit 1
    fi
ENDSSH

echo ""
echo "====================================="
echo "Deployment Complete!"
echo "====================================="
echo ""
echo "Test the fix by:"
echo "1. Upload TPR data with known ward name mismatches"
echo "2. Check logs for fuzzy matching messages"
echo "3. Verify more wards are matched in the output"
echo ""
echo "To monitor ward matching in real-time:"
echo "ssh -i $SSH_KEY $SSH_USER@$SSH_HOST 'tail -f /home/ec2-user/ChatMRPT/instance/app.log | grep -i ward'"