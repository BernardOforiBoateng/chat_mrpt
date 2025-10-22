#!/bin/bash

# Deploy ITN threshold and missing areas fixes to AWS production instances

echo "========================================"
echo "🚀 Deploying ITN Fixes to Production"
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
    "app/analysis/itn_pipeline.py"
    "app/web/routes/itn_routes.py"
    "app/tools/itn_planning_tools.py"
    "frontend/src/components/Visualization/VisualizationFrame.tsx"
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
        if [[ $file == *.py ]]; then
            echo "  Copying $file..."
            scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$file" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file" 2>/dev/null
            if [ $? -eq 0 ]; then
                echo "    ✅ Success"
            else
                echo "    ❌ Failed"
            fi
        fi
    done
    
    # Handle TypeScript file - copy to frontend directory
    if [ -f "frontend/src/components/Visualization/VisualizationFrame.tsx" ]; then
        echo "  Copying TypeScript file..."
        ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" "mkdir -p /home/ec2-user/ChatMRPT/frontend/src/components/Visualization" 2>/dev/null
        scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "frontend/src/components/Visualization/VisualizationFrame.tsx" \
            "ec2-user@$ip:/home/ec2-user/ChatMRPT/frontend/src/components/Visualization/" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "    ✅ TypeScript file copied"
        fi
    fi
    
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
echo "📋 Summary of fixes deployed:"
echo "  1. Fixed hard-coded JavaScript values in ITN maps"
echo "  2. Implemented session-based parameter storage"
echo "  3. Added dynamic map loading (no page reload)"
echo "  4. Preserved all shapefile wards (even without data)"
echo "  5. Improved ward matching with lower threshold (70%)"
echo "  6. Added visual indicators for unmatched wards"
echo "  7. Added comprehensive logging and reports"
echo ""
echo "🧪 Test the fixes:"
echo "  1. Run ITN planning with 30% threshold"
echo "  2. Change threshold to 50% and click Update"
echo "  3. Verify map updates without page reload"
echo "  4. Check that all geographic areas appear"
echo ""
echo "📊 Check logs with:"
echo "  ssh -i $KEY_PATH ec2-user@$INSTANCE_1 'sudo journalctl -u chatmrpt -f'"
echo ""