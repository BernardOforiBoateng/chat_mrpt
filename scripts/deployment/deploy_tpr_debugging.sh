#!/bin/bash

# Deploy TPR debugging enhancements to AWS production instances
# This adds comprehensive logging to identify where the TPR workflow fails

echo "🚀 Deploying TPR debugging enhancements to AWS production..."

# Copy SSH key to temp location
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Production instance IPs (formerly staging)
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"

# Files to deploy
FILES=(
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
    "app/data_analysis_v3/tools/tpr_analysis_tool.py"
    "app/web/routes/data_analysis_v3_routes.py"
)

echo "📦 Files to deploy:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done

# Deploy to both instances
for INSTANCE_IP in $INSTANCE_1 $INSTANCE_2; do
    echo ""
    echo "🎯 Deploying to instance: $INSTANCE_IP"
    
    # Copy files
    for file in "${FILES[@]}"; do
        echo "  📄 Copying $file..."
        scp -i /tmp/chatmrpt-key2.pem "$file" "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/$file"
        
        if [ $? -eq 0 ]; then
            echo "  ✅ Successfully copied $file"
        else
            echo "  ❌ Failed to copy $file"
            exit 1
        fi
    done
    
    # Restart the service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i /tmp/chatmrpt-key2.pem "ec2-user@$INSTANCE_IP" "sudo systemctl restart chatmrpt"
    
    if [ $? -eq 0 ]; then
        echo "  ✅ Service restarted successfully"
    else
        echo "  ❌ Failed to restart service"
        exit 1
    fi
    
    # Check service status
    echo "  📊 Checking service status..."
    ssh -i /tmp/chatmrpt-key2.pem "ec2-user@$INSTANCE_IP" "sudo systemctl status chatmrpt | head -5"
done

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Debug features added:"
echo "  • Comprehensive logging at every TPR workflow stage"
echo "  • Debug info in API responses (visible in browser console)"
echo "  • Debug JSON files saved to session folder"
echo "  • Detailed error tracking with stack traces"
echo "  • File creation status monitoring"
echo ""
echo "🔍 To test and view debug output:"
echo "  1. Open browser console (F12)"
echo "  2. Run TPR workflow in Data Analysis tab"
echo "  3. Check console for 'debug' field in responses"
echo "  4. Check AWS logs: sudo journalctl -u chatmrpt -f"
echo "  5. Check debug files in session folder:"
echo "     - tpr_debug.json"
echo "     - tpr_analysis_debug.json"
echo "     - tpr_error_debug.json (if errors occur)"
echo ""
echo "🌐 Access the application at:"
echo "  https://d225ar6c86586s.cloudfront.net"