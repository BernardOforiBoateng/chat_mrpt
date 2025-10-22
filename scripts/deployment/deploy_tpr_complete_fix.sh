#!/bin/bash
# Complete TPR Fix Deployment Script
# This script applies all fixes for TPR workflow issues on AWS

set -e  # Exit on any error

echo "=== TPR Complete Fix Deployment ==="
echo "This script will apply all TPR workflow fixes"
echo ""

# SSH key path
SSH_KEY="/tmp/chatmrpt-key.pem"
AWS_HOST="ec2-user@3.137.158.17"

# Copy key to /tmp if needed
if [ -f "aws_files/chatmrpt-key.pem" ]; then
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key.pem
    chmod 600 /tmp/chatmrpt-key.pem
fi

# Check if SSH key exists
if [ ! -f "$SSH_KEY" ]; then
    echo "❌ Error: SSH key not found at $SSH_KEY"
    exit 1
fi

echo "📋 Creating backup of current files..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$AWS_HOST" << 'BACKUP'
    cd /home/ec2-user/ChatMRPT
    
    # Create backup directory
    BACKUP_DIR="backups/tpr_fix_$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    
    # Backup files
    cp app/config/base.py "$BACKUP_DIR/"
    cp app/tpr_module/integration/tpr_handler.py "$BACKUP_DIR/"
    cp app/tpr_module/core/tpr_state_manager.py "$BACKUP_DIR/"
    
    echo "✅ Backups created in $BACKUP_DIR"
BACKUP

echo ""
echo "🔧 Verifying Redis is running..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$AWS_HOST" << 'CHECK_REDIS'
    if ! systemctl is-active --quiet redis6; then
        echo "❌ Redis is not running! Please run install_redis_aws.sh first"
        exit 1
    fi
    echo "✅ Redis is running"
CHECK_REDIS

echo ""
echo "📝 Checking current status..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$AWS_HOST" << 'STATUS'
    cd /home/ec2-user/ChatMRPT
    
    # Check if fixes are already applied
    if grep -q "_sync_to_session" app/tpr_module/core/tpr_state_manager.py 2>/dev/null; then
        echo "ℹ️  TPR session persistence already implemented"
    else
        echo "⚠️  TPR session persistence not found - will apply fix"
    fi
    
    if grep -q "age_group_selection" app/tpr_module/integration/tpr_handler.py 2>/dev/null; then
        echo "ℹ️  Stage map fix already applied"
    else
        echo "⚠️  Stage map fix needed"
    fi
STATUS

echo ""
echo "🚀 Deploying fixes..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$AWS_HOST" << 'DEPLOY'
    cd /home/ec2-user/ChatMRPT
    
    # Apply all fixes via the Python scripts created earlier
    if [ -f "simple_tpr_session_fix.py" ]; then
        python3 simple_tpr_session_fix.py
        echo "✅ Applied TPR session persistence fix"
    fi
    
    if [ -f "fix_tpr_stage_map.py" ]; then
        python3 fix_tpr_stage_map.py
        echo "✅ Applied stage map fix"
    fi
    
    if [ -f "add_tpr_debug_logging.py" ]; then
        python3 add_tpr_debug_logging.py
        echo "✅ Added debug logging"
    fi
DEPLOY

echo ""
echo "♻️  Restarting ChatMRPT service..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$AWS_HOST" << 'RESTART'
    sudo systemctl restart chatmrpt
    
    # Wait for service to start
    sleep 5
    
    if systemctl is-active --quiet chatmrpt; then
        echo "✅ ChatMRPT service restarted successfully"
    else
        echo "❌ ChatMRPT failed to start!"
        sudo systemctl status chatmrpt
        exit 1
    fi
RESTART

echo ""
echo "🔍 Running verification checks..."
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$AWS_HOST" << 'VERIFY'
    cd /home/ec2-user/ChatMRPT
    
    # Check Redis sessions
    echo "Redis sessions:"
    redis6-cli keys "session:*" | wc -l
    
    # Check for recent errors
    echo ""
    echo "Recent error count (last 100 lines):"
    sudo journalctl -u chatmrpt -n 100 | grep -c ERROR || echo "0"
    
    # Check workers
    echo ""
    echo "Active workers:"
    ps aux | grep gunicorn | grep -v grep | wc -l
VERIFY

echo ""
echo "✅ === TPR Fix Deployment Complete ==="
echo ""
echo "📋 Next Steps:"
echo "1. Test the TPR workflow at: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/"
echo "2. Upload NMEP TPR file"
echo "3. Test all stages:"
echo "   - State selection"
echo "   - Facility confirmation"
echo "   - Facility type selection"
echo "   - Age group selection"
echo ""
echo "📊 Monitor with:"
echo "   ssh -i $SSH_KEY $AWS_HOST 'sudo journalctl -u chatmrpt -f | grep -i tpr'"
echo ""
echo "🔍 Check Redis sessions:"
echo "   ssh -i $SSH_KEY $AWS_HOST 'redis6-cli monitor | grep tpr_states'"