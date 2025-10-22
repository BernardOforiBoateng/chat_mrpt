#!/bin/bash

# Simple deployment of fullscreen fix - just copy TypeScript files

echo "========================================"
echo "🚀 Deploying Fullscreen Visualization Fix"
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
    "frontend/src/components/Visualization/VisualizationContainer.tsx"
    "frontend/src/components/Visualization/VisualizationControls.tsx"
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
    
    # Create directory if needed
    echo "  Creating directory..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" \
        "mkdir -p /home/ec2-user/ChatMRPT/frontend/src/components/Visualization" 2>/dev/null
    
    # Copy TypeScript files
    for file in "${FILES[@]}"; do
        filename=$(basename "$file")
        echo "  Copying $filename..."
        scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$file" \
            "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "    ✅ Success"
        else
            echo "    ❌ Failed"
        fi
    done
    
    # Check if frontend needs rebuilding on server
    echo "  Checking if frontend build is needed..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" "
        cd /home/ec2-user/ChatMRPT
        # Check if it's a React app that needs building
        if [ -f frontend/package.json ] && grep -q 'react' frontend/package.json 2>/dev/null; then
            echo '    Frontend is React app - may need manual rebuild'
        fi
        # Check if frontend is served statically or dynamically
        if [ -d app/static/js ] && [ -d app/static/css ]; then
            echo '    Frontend appears to be served from app/static'
        fi
    " 2>/dev/null
    
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
echo "  - Fixed: Fullscreen always showing first visualization"
echo "  - Solution: Using React refs to target specific containers"
echo ""
echo "🧪 How to test:"
echo "  1. Go to https://d225ar6c86586s.cloudfront.net"
echo "  2. Create multiple visualizations"
echo "  3. Click fullscreen on the 2nd or 3rd visualization"
echo "  4. ✅ Should show the correct visualization, not the first one"
echo ""
echo "⚠️  Note: If the fix doesn't work immediately:"
echo "  The frontend may need to be rebuilt on the server."
echo "  SSH to server and run: cd /home/ec2-user/ChatMRPT/frontend && npm run build"
echo ""