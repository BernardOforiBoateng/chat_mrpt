#!/bin/bash
# Deploy TPR Workflow Vertical Spacing Fix
# Adds proper vertical spacing between options in TPR workflow

set -e

echo "=========================================="
echo "TPR Workflow Spacing Fix Deployment"
echo "Date: $(date)"
echo "=========================================="
echo ""

# Production instances
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"
KEY_FILE="/tmp/chatmrpt-key2.pem"

# Ensure key exists
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ Key file not found: $KEY_FILE"
    echo "Copying from aws_files..."
    cp aws_files/chatmrpt-key.pem "$KEY_FILE"
    chmod 600 "$KEY_FILE"
fi

# Function to deploy to an instance
deploy_to_instance() {
    local IP=$1
    local NAME=$2

    echo "📦 Deploying to $NAME ($IP)..."

    # Create backup first
    echo "  📋 Creating backup..."
    ssh -i "$KEY_FILE" ec2-user@$IP << 'BACKUP_EOF'
        cd /home/ec2-user
        BACKUP_NAME="ChatMRPT_pre_tpr_spacing_$(date +%Y%m%d_%H%M%S).tar.gz"
        tar --exclude="ChatMRPT/instance/uploads/*" \
            --exclude="ChatMRPT/chatmrpt_venv*" \
            --exclude="ChatMRPT/venv*" \
            --exclude="ChatMRPT/__pycache__" \
            --exclude="*.pyc" \
            -czf "$BACKUP_NAME" ChatMRPT/
        echo "✅ Backup created: $BACKUP_NAME"
BACKUP_EOF

    # Copy updated formatter file
    echo "  📤 Uploading TPR formatter with spacing fixes..."
    scp -i "$KEY_FILE" \
        app/data_analysis_v3/core/formatters.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/formatters.py

    # Restart service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i "$KEY_FILE" ec2-user@$IP << 'RESTART_EOF'
        sudo systemctl restart chatmrpt
        sleep 3
        sudo systemctl status chatmrpt --no-pager | head -20
RESTART_EOF

    echo "✅ Deployment to $NAME complete!"
    echo ""
}

# Deploy to both instances
echo "🚀 Starting deployment to production instances..."
echo ""

deploy_to_instance "$INSTANCE_1" "Instance 1"
deploy_to_instance "$INSTANCE_2" "Instance 2"

echo "=========================================="
echo "✅ TPR Spacing Fix Deployed!"
echo "=========================================="
echo ""
echo "Changes deployed:"
echo "  - Added \\n\\n after each facility option (lines 82, 124)"
echo "  - Added \\n\\n after each age group option (line 181)"
echo "  - Normalized bullet points in state selection (• → -)"
echo ""
echo "Expected improvements:"
echo "  - Better vertical spacing between facility levels"
echo "  - Better spacing between age group options"
echo "  - Consistent bullet point style (dash instead of bullet)"
echo ""
echo "Test queries:"
echo "  1. Start TPR workflow and observe spacing"
echo "  2. Check facility selection screen"
echo "  3. Check age group selection screen"
echo ""
echo "Monitor with:"
echo "  ssh -i $KEY_FILE ec2-user@$INSTANCE_1 'sudo journalctl -u chatmrpt -f'"
echo ""
