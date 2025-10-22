#!/bin/bash

echo "=========================================="
echo "Deploying Mistral Routing Fix"
echo "=========================================="

KEY_FILE="/tmp/chatmrpt-key2.pem"
FILE="app/web/routes/analysis_routes.py"

# Production instances
INSTANCES=("3.21.167.170" "18.220.103.20")

echo "📦 Deploying fix for visualization routing"
echo ""
echo "Changes made:"
echo "  ✅ Clarified that ALL visualization requests need tools"
echo "  ✅ Added explicit examples for plot/show/create requests"
echo "  ✅ Removed misleading context-dependent routing"
echo "  ✅ Added CRITICAL visualization rule"
echo ""

for INSTANCE in "${INSTANCES[@]}"; do
    echo "Deploying to $INSTANCE..."
    
    # Copy file
    scp -i "$KEY_FILE" -o StrictHostKeyChecking=no "$FILE" "ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/$FILE"
    
    if [ $? -eq 0 ]; then
        echo "  ✅ File copied"
    else
        echo "  ❌ Failed to copy file"
        exit 1
    fi
    
    # Restart service
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" "sudo systemctl restart chatmrpt"
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Service restarted"
    else
        echo "  ❌ Failed to restart"
        exit 1
    fi
done

echo ""
echo "✨ Deployment complete!"
echo ""
echo "Expected behavior:"
echo "  ✅ 'plot vulnerability map' → needs_tools"
echo "  ✅ 'show top 10 wards' → needs_tools"
echo "  ✅ 'plot evi distribution' → needs_tools"
echo "  ✅ 'create any visualization' → needs_tools"
echo ""
