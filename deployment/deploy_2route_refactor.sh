#!/bin/bash
# Deploy 2-Route Architecture Refactor to Production
# Date: 2025-10-12
# Changes: Simplified 7-intent to 2-route, removed hardcoded responses

set -e  # Exit on error

echo "============================================"
echo "Deploying 2-Route Architecture Refactor"
echo "============================================"

# SSH key
KEY="/tmp/chatmrpt-key2.pem"

# Production instances
PROD_INSTANCES=(
    "3.21.167.170"
    "18.220.103.20"
)

# Files to deploy
FILES=(
    "app/data_analysis_v3/core/tpr_language_interface.py"
    "app/web/routes/data_analysis_v3_routes.py"
    "app/data_analysis_v3/tpr/workflow_manager.py"
)

echo ""
echo "Files to deploy:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done
echo ""

# Deploy to each instance
for instance in "${PROD_INSTANCES[@]}"; do
    echo "============================================"
    echo "Deploying to instance: $instance"
    echo "============================================"

    # Copy files
    echo "📦 Copying files..."
    for file in "${FILES[@]}"; do
        echo "  Copying $file..."
        scp -i "$KEY" -o StrictHostKeyChecking=no "$file" "ec2-user@$instance:/home/ec2-user/ChatMRPT/$file"
    done

    echo "✅ Files copied successfully"

    # Restart service
    echo "🔄 Restarting ChatMRPT service..."
    ssh -i "$KEY" -o StrictHostKeyChecking=no "ec2-user@$instance" \
        'sudo systemctl restart chatmrpt && echo "✅ Service restarted" && sudo systemctl status chatmrpt --no-pager -l | head -20'

    echo "✅ Deployment complete for $instance"
    echo ""
done

echo "============================================"
echo "✅ ALL DEPLOYMENTS COMPLETE"
echo "============================================"
echo ""
echo "Changes deployed:"
echo "  1. Simplified tpr_language_interface.py (classify_intent → extract_command)"
echo "  2. Implemented 2-route logic in data_analysis_v3_routes.py"
echo "  3. Simplified workflow_manager.py (removed 298 lines of intent logic)"
echo ""
echo "Production instances:"
echo "  - Instance 1: http://3.21.167.170"
echo "  - Instance 2: http://18.220.103.20"
echo "  - CloudFront: https://d225ar6c86586s.cloudfront.net"
echo ""
echo "Ready for testing!"
