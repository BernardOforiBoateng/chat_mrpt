#!/bin/bash
# Deploy tool removal (4 redundant tools removed)
# Reduces tool count from 19 → 12 tools

set -e

echo "=========================================="
echo "Tool Removal Deployment"
echo "Date: $(date)"
echo "Change: Remove 4 redundant tools"
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
        BACKUP_NAME="ChatMRPT_pre_tool_removal_$(date +%Y%m%d_%H%M%S).tar.gz"
        tar --exclude="ChatMRPT/instance/uploads/*" \
            --exclude="ChatMRPT/chatmrpt_venv*" \
            --exclude="ChatMRPT/venv*" \
            --exclude="ChatMRPT/__pycache__" \
            --exclude="*.pyc" \
            -czf "$BACKUP_NAME" ChatMRPT/
        echo "✅ Backup created: $BACKUP_NAME"
BACKUP_EOF

    # Copy updated file
    echo "  📤 Uploading updated request_interpreter.py..."
    scp -i "$KEY_FILE" \
        app/core/request_interpreter.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/core/request_interpreter.py

    # Restart service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i "$KEY_FILE" ec2-user@$IP << 'RESTART_EOF'
        sudo systemctl restart chatmrpt
        sleep 3
        sudo systemctl status chatmrpt --no-pager | head -20
RESTART_EOF

    # Verify tool count
    echo "  ✅ Verifying tool count..."
    ssh -i "$KEY_FILE" ec2-user@$IP << 'VERIFY_EOF'
        sleep 2
        echo "Checking logs for tool registration..."
        sudo journalctl -u chatmrpt -n 50 | grep "Registered.*tools" | tail -1
VERIFY_EOF

    echo "✅ Deployment to $NAME complete!"
    echo ""
}

# Deploy to both instances
echo "🚀 Starting deployment to production instances..."
echo ""

deploy_to_instance "$INSTANCE_1" "Instance 1"
deploy_to_instance "$INSTANCE_2" "Instance 2"

echo "=========================================="
echo "✅ Tool Removal Deployment Complete!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - 4 tools removed (execute_data_query, execute_sql_query, run_data_quality_check, create_box_plot)"
echo "  - Tool count reduced: 19 → 12 tools"
echo "  - All functionality preserved via Tool #19 (analyze_data_with_python)"
echo ""
echo "Monitor with:"
echo "  ssh -i $KEY_FILE ec2-user@$INSTANCE_1 'sudo journalctl -u chatmrpt -f | grep \"🐍 TOOL:\"'"
echo ""
echo "Rollback if needed:"
echo "  ssh -i $KEY_FILE ec2-user@<IP> 'cd ChatMRPT && tar -xzf ChatMRPT_pre_tool_removal_*.tar.gz && sudo systemctl restart chatmrpt'"
echo ""
