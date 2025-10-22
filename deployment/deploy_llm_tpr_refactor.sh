#!/bin/bash

# Deploy LLM-driven TPR refactoring to production instances
# Date: October 9, 2025
# Changes: LLM-powered slot resolution and intent classification

set -e

echo "=========================================="
echo "LLM TPR Refactoring Deployment"
echo "=========================================="
echo ""

# Production instances
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"
KEY_FILE="/tmp/chatmrpt-key2.pem"

# Files to deploy
FILES=(
    "app/data_analysis_v3/core/tpr_language_interface.py"
    "app/data_analysis_v3/tpr/workflow_manager.py"
)

echo "Files to deploy:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done
echo ""

# Function to deploy to one instance
deploy_to_instance() {
    local INSTANCE=$1
    echo "=========================================="
    echo "Deploying to Instance: $INSTANCE"
    echo "=========================================="

    # Create backup (if files exist)
    echo "[1/4] Creating backup..."
    ssh -i $KEY_FILE -o StrictHostKeyChecking=no ec2-user@$INSTANCE \
        "cd /home/ec2-user && \
        if [ -f ChatMRPT/app/data_analysis_v3/core/tpr_language_interface.py ] && [ -f ChatMRPT/app/data_analysis_v3/tpr/workflow_manager.py ]; then \
            tar -czf ChatMRPT_BEFORE_LLM_REFACTOR_\$(date +%Y%m%d_%H%M%S).tar.gz \
            ChatMRPT/app/data_analysis_v3/core/tpr_language_interface.py \
            ChatMRPT/app/data_analysis_v3/tpr/workflow_manager.py && \
            ls -lh ChatMRPT_BEFORE_LLM_REFACTOR*.tar.gz | tail -1; \
        else \
            echo 'Files are new, no backup needed'; \
        fi"

    # Upload files
    echo "[2/4] Uploading files..."
    for file in "${FILES[@]}"; do
        echo "  Uploading $file..."
        scp -i $KEY_FILE -o StrictHostKeyChecking=no "$file" \
            ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/$file
    done

    # Restart service
    echo "[3/4] Restarting chatmrpt service..."
    ssh -i $KEY_FILE -o StrictHostKeyChecking=no ec2-user@$INSTANCE \
        "sudo systemctl restart chatmrpt"

    # Verify service status
    echo "[4/4] Verifying service status..."
    ssh -i $KEY_FILE -o StrictHostKeyChecking=no ec2-user@$INSTANCE \
        "sudo systemctl status chatmrpt --no-pager | head -10"

    echo "✅ Deployment to $INSTANCE complete!"
    echo ""
}

# Check if key file exists
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ Error: SSH key not found at $KEY_FILE"
    echo "Please create the key first"
    exit 1
fi

# Deploy to both instances
deploy_to_instance $INSTANCE1
deploy_to_instance $INSTANCE2

echo "=========================================="
echo "✅ LLM TPR Refactoring deployed to ALL instances!"
echo "=========================================="
echo ""
echo "CloudFront URL: https://d225ar6c86586s.cloudfront.net"
echo ""
echo "Next steps:"
echo "1. Test data upload on CloudFront"
echo "2. Test TPR workflow with natural language"
echo "3. Verify LLM slot resolution works"
echo ""
