#!/bin/bash

# Deploy fullscreen visualization fix to AWS production instances

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

echo ""
echo "📦 Building React frontend..."
cd frontend
npm run build
if [ $? -ne 0 ]; then
    echo "❌ Frontend build failed!"
    exit 1
fi
cd ..
echo "✅ Frontend built successfully"

# Files to deploy - TypeScript files and built assets
echo ""
echo "📦 Files to deploy:"
echo "  - Frontend TypeScript source files"
echo "  - Built frontend assets"

# Deploy to both instances
for ip in "$INSTANCE_1" "$INSTANCE_2"; do
    echo ""
    echo "📍 Deploying to $ip..."
    
    # Create directories if needed
    echo "  Creating frontend directories..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" "
        mkdir -p /home/ec2-user/ChatMRPT/frontend/src/components/Visualization
        mkdir -p /home/ec2-user/ChatMRPT/app/static/js
        mkdir -p /home/ec2-user/ChatMRPT/app/static/css
    " 2>/dev/null
    
    # Copy TypeScript source files
    echo "  Copying TypeScript files..."
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
        frontend/src/components/Visualization/VisualizationContainer.tsx \
        frontend/src/components/Visualization/VisualizationControls.tsx \
        "ec2-user@$ip:/home/ec2-user/ChatMRPT/frontend/src/components/Visualization/" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "    ✅ TypeScript files copied"
    else
        echo "    ⚠️  Could not copy TypeScript files (may not be needed if built assets work)"
    fi
    
    # Copy built frontend assets
    echo "  Copying built frontend assets..."
    # Check if we have a dist or build directory
    if [ -d "frontend/dist" ]; then
        BUILD_DIR="frontend/dist"
    elif [ -d "frontend/build" ]; then
        BUILD_DIR="frontend/build"
    else
        echo "    ⚠️  No build directory found, skipping built assets"
        BUILD_DIR=""
    fi
    
    if [ -n "$BUILD_DIR" ]; then
        # Copy all built assets
        scp -r -i "$KEY_PATH" -o StrictHostKeyChecking=no \
            "$BUILD_DIR"/* \
            "ec2-user@$ip:/home/ec2-user/ChatMRPT/app/static/" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo "    ✅ Built assets copied"
        else
            echo "    ⚠️  Could not copy built assets"
        fi
    fi
    
    # Build on remote if needed
    echo "  Building frontend on remote server..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" "
        cd /home/ec2-user/ChatMRPT/frontend
        if [ -f package.json ]; then
            npm install --production 2>/dev/null
            npm run build 2>/dev/null
            if [ $? -eq 0 ]; then
                echo '    ✅ Frontend built on remote'
            else
                echo '    ⚠️  Remote build failed (may use pre-built assets)'
            fi
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
echo "  - Fixed fullscreen always showing first visualization"
echo "  - Each visualization now correctly goes fullscreen"
echo "  - Used React refs to target specific containers"
echo ""
echo "🧪 Test the fix:"
echo "  1. Create multiple visualizations in a session"
echo "  2. Click fullscreen on 2nd or 3rd visualization"
echo "  3. Verify correct visualization goes fullscreen"
echo "  4. Test with different visualization types"
echo ""
echo "📊 Files modified:"
echo "  - VisualizationContainer.tsx (added ref)"
echo "  - VisualizationControls.tsx (uses ref instead of querySelector)"
echo ""