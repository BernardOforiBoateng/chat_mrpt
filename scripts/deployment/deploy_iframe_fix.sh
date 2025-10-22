#!/bin/bash

# Deploy iframe HTML removal fixes to AWS production instances

echo "========================================"
echo "🚀 Deploying iframe HTML Removal Fixes"
echo "========================================"

# Set variables
KEY_PATH="/tmp/chatmrpt-key2.pem"
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"

# Copy key if needed
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

# Files to deploy
FILES=(
    "app/tools/visualization_maps_tools.py"
    "app/tools/variable_distribution.py"
    "app/tools/itn_planning_tools.py"
)

echo ""
echo "📦 Files to deploy:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done

echo ""
echo "🎯 Target instances:"
echo "  - Instance 1: $INSTANCE_1"
echo "  - Instance 2: $INSTANCE_2"

# Deploy to both instances
for ip in "$INSTANCE_1" "$INSTANCE_2"; do
    echo ""
    echo "📍 Deploying to $ip..."
    
    # Copy Python files
    for file in "${FILES[@]}"; do
        echo "  Copying $file..."
        scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$file" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "    ✅ Success"
        else
            echo "    ❌ Failed"
        fi
    done
    
    # Restart service
    echo "  Restarting ChatMRPT service..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" "sudo systemctl restart chatmrpt" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "    ✅ Service restarted"
    else
        echo "    ❌ Failed to restart service"
    fi
done

echo ""
echo "========================================"
echo "✅ Deployment Complete!"
echo "========================================"
echo ""
echo "📋 Summary of fix:"
echo "  - Removed raw iframe HTML from chat messages"
echo "  - Frontend will render visualizations using web_path"
echo "  - Chat interface now clean and professional"
echo ""
echo "🧪 Test the fix:"
echo "  1. Run any visualization tool"
echo "  2. Verify NO raw HTML appears in chat"
echo "  3. Verify visualizations still render below messages"
echo ""
echo "📊 Affected tools:"
echo "  - Variable distribution maps"
echo "  - Vulnerability maps (composite and PCA)"
echo "  - ITN distribution maps"
echo "  - All visualization map tools"
echo ""