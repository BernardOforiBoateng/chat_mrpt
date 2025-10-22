#!/bin/bash

echo "🚀 Deploying TPR Map and Ward Matching Fixes to AWS..."
echo "=================================================="

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
SERVER="ec2-user@3.137.158.17"
REMOTE_PATH="/home/ec2-user/ChatMRPT"

# Files to deploy
FILES=(
    "app/tpr_module/services/tpr_visualization_service.py"
)

echo "📦 Files to deploy:"
for file in "${FILES[@]}"; do
    echo "   - $file"
done

echo ""
echo "🔄 Deploying files..."

# Deploy each file
for file in "${FILES[@]}"; do
    echo "   Uploading $file..."
    scp -i "$KEY_PATH" "$file" "$SERVER:$REMOTE_PATH/$file"
    if [ $? -eq 0 ]; then
        echo "   ✅ $file deployed successfully"
    else
        echo "   ❌ Failed to deploy $file"
        exit 1
    fi
done

echo ""
echo "🔄 Restarting Gunicorn service..."

ssh -i "$KEY_PATH" "$SERVER" << 'EOF'
    echo "   Restarting gunicorn..."
    sudo systemctl restart gunicorn
    
    # Wait for service to start
    sleep 3
    
    # Check status
    if sudo systemctl is-active --quiet gunicorn; then
        echo "   ✅ Gunicorn restarted successfully"
    else
        echo "   ❌ Gunicorn failed to restart"
        sudo systemctl status gunicorn
        exit 1
    fi
EOF

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Summary of changes deployed:"
echo "   1. TPR map color scale fixed (zmax: 50 → 100)"
echo "   2. Fuzzy ward name matching implemented (85% similarity threshold)"
echo ""
echo "🧪 Test the changes:"
echo "   1. Upload TPR data and generate map - should show color variations"
echo "   2. Check that ~90% of wards show data (up from 80%)"
echo "   3. Run ITN planning - should match more wards"
echo ""
echo "🔗 Access the application at: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/"