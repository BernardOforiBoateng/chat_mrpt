#!/bin/bash

# Deploy formatting and Arena context fixes to AWS production instances

echo "========================================"
echo "🚀 Deploying Formatting & Arena Fixes"
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
    "app/core/request_interpreter.py"
    "app/core/arena_context_manager.py"
    "app/web/routes/arena_routes.py"
    "app/web/routes/analysis_routes.py"
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
        filename=$(basename "$file")
        dirname=$(dirname "$file")
        echo "  Copying $filename..."
        
        # Create directory if needed
        ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" \
            "mkdir -p /home/ec2-user/ChatMRPT/$dirname" 2>/dev/null
        
        # Copy file
        scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$file" \
            "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file" 2>/dev/null
        
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
echo "📋 Summary of fixes deployed:"
echo ""
echo "1️⃣ FORMATTING FIX:"
echo "  - Added proper spacing between results and interpretation"
echo "  - Added '**Analysis:**' header for clarity"
echo "  - Location: app/core/request_interpreter.py"
echo ""
echo "2️⃣ ARENA CONTEXT ENHANCEMENT:"
echo "  - Created ArenaContextManager to aggregate session data"
echo "  - Arena models now receive analysis context"
echo "  - Can reference specific ward names and TPR results"
echo "  - Locations: arena_context_manager.py, arena_routes.py, analysis_routes.py"
echo ""
echo "🧪 How to verify:"
echo "  1. Go to https://d225ar6c86586s.cloudfront.net"
echo "  2. Upload data and run an analysis"
echo "  3. Check that results have proper spacing and 'Analysis:' header"
echo "  4. Ask Arena models about specific analysis results"
echo "  5. Arena should now understand context like 'What about Ward1?'"
echo ""
echo "⚠️  Note: Wait 1-2 minutes for services to fully restart"
echo ""