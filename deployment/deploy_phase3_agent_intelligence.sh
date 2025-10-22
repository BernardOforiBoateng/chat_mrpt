#!/bin/bash
# Deploy Phase 3: Agent Intelligence (Simplified)
# - Schema awareness (prevents errors)
# - Smart error messages (helpful, not hardcoded)
# - Smart pagination (UX improvement)
# - AI-driven interpretation (via system prompt)

set -e

echo "=========================================="
echo "Phase 3: Agent Intelligence Deployment"
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
        BACKUP_NAME="ChatMRPT_pre_phase3_$(date +%Y%m%d_%H%M%S).tar.gz"
        tar --exclude="ChatMRPT/instance/uploads/*" \
            --exclude="ChatMRPT/chatmrpt_venv*" \
            --exclude="ChatMRPT/venv*" \
            --exclude="ChatMRPT/__pycache__" \
            --exclude="*.pyc" \
            -czf "$BACKUP_NAME" ChatMRPT/
        echo "✅ Backup created: $BACKUP_NAME"
BACKUP_EOF

    # Copy updated files
    echo "  📤 Uploading Phase 3 improvements..."

    # 1. Schema awareness in agent
    scp -i "$KEY_FILE" \
        app/data_analysis_v3/core/agent.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/agent.py

    # 2. Simplified error handling in python_tool
    scp -i "$KEY_FILE" \
        app/data_analysis_v3/tools/python_tool.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/python_tool.py

    # 3. Smart pagination in formatters
    scp -i "$KEY_FILE" \
        app/data_analysis_v3/core/formatters.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/formatters.py

    # 4. AI interpretation guidance in system prompt
    scp -i "$KEY_FILE" \
        app/data_analysis_v3/prompts/system_prompt.py \
        ec2-user@$IP:/home/ec2-user/ChatMRPT/app/data_analysis_v3/prompts/system_prompt.py

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
echo "✅ Phase 3: Agent Intelligence Deployed!"
echo "=========================================="
echo ""
echo "Improvements deployed:"
echo "  1. Schema awareness - AI sees column names/types before writing code"
echo "  2. Smart error messages - Helpful column suggestions, not technical errors"
echo "  3. Smart pagination - 20/100/500 row thresholds with suggestions"
echo "  4. AI interpretation - System prompt guides AI to explain everything"
echo ""
echo "Philosophy:"
echo "  ✅ Lean on AI intelligence"
echo "  ❌ Avoid hardcoded rules"
echo ""
echo "Expected improvements:"
echo "  - 90% fewer 'column not found' errors"
echo "  - No technical errors shown to users"
echo "  - No browser hangs with large results"
echo "  - All outputs include plain-English interpretation"
echo ""
echo "Test queries:"
echo "  1. 'Show me wards with latitude > 9' → Should handle column name smartly"
echo "  2. 'Calculate statistics for TPR' → Should include interpretation"
echo "  3. 'Show all wards' → Should paginate with helpful suggestions"
echo ""
echo "Monitor with:"
echo "  ssh -i $KEY_FILE ec2-user@$INSTANCE_1 'sudo journalctl -u chatmrpt -f'"
echo ""
