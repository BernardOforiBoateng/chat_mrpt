#!/bin/bash
# Deploy Phase 1: Formatting Fixes
# - Updated formatters.py with ResponseFormatter class
# - Updated python_tool.py to use ResponseFormatter
# - Updated system_prompt.py with formatting rules
# - Updated analysis_routes.py with streaming formatter

set -e

echo "=========================================="
echo "Phase 1: Formatting Fixes Deployment"
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
        BACKUP_NAME="ChatMRPT_pre_formatting_$(date +%Y%m%d_%H%M%S).tar.gz"
        tar --exclude="ChatMRPT/instance/uploads/*" \
            --exclude="ChatMRPT/chatmrpt_venv*" \
            --exclude="ChatMRPT/venv*" \
            --exclude="ChatMRPT/__pycache__" \
            --exclude="*.pyc" \
            -czf "$BACKUP_NAME" ChatMRPT/
        echo "✅ Backup created: $BACKUP_NAME"
BACKUP_EOF

    # Copy updated files
    echo "  📤 Uploading formatting fixes..."

    # 1. Updated formatters.py (ResponseFormatter added)
    scp -i "$KEY_FILE" \
        app/data_analysis_v3/core/formatters.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/formatters.py

    # 2. Updated python_tool.py (uses ResponseFormatter)
    scp -i "$KEY_FILE" \
        app/data_analysis_v3/tools/python_tool.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/python_tool.py

    # 3. Updated system_prompt.py (formatting rules)
    scp -i "$KEY_FILE" \
        app/data_analysis_v3/prompts/system_prompt.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/data_analysis_v3/prompts/system_prompt.py

    # 4. Updated analysis_routes.py (streaming formatter)
    scp -i "$KEY_FILE" \
        app/web/routes/analysis_routes.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/web/routes/analysis_routes.py

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
echo "✅ Phase 1: Formatting Fixes Deployed!"
echo "=========================================="
echo ""
echo "Changes deployed:"
echo "  1. ResponseFormatter class added to formatters.py"
echo "  2. Python tool updated to use ResponseFormatter.normalize_spacing()"
echo "  3. System prompt updated with formatting rules for AI"
echo "  4. Streaming route updated with format_response() function"
echo ""
echo "Expected improvements:"
echo "  - Bullet points on separate lines"
echo "  - DataFrames as markdown tables"
echo "  - Proper vertical spacing"
echo "  - Statistics formatted with bullets"
echo ""
echo "Test queries:"
echo "  1. 'Show me the first 10 rows' → Should show markdown table"
echo "  2. 'List all wards in Demsa LGA' → Should show bullet points"
echo "  3. 'What's the mean TPR?' → Should show formatted statistics"
echo ""
echo "Monitor with:"
echo "  ssh -i $KEY_FILE ec2-user@$INSTANCE_1 'sudo journalctl -u chatmrpt -f'"
echo ""
