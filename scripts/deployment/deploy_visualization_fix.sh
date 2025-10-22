#!/bin/bash

# Deploy visualization fix to AWS production instances

echo "========================================"
echo "🚀 Deploying Visualization Fix"
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

# File to deploy
FILE="app/core/request_interpreter.py"

echo ""
echo "📦 File to deploy:"
echo "  - $FILE"
echo ""
echo "🎯 Target instances:"
echo "  - Instance 1: $INSTANCE_1"
echo "  - Instance 2: $INSTANCE_2"

# Deploy to both instances
for ip in "$INSTANCE_1" "$INSTANCE_2"; do
    echo ""
    echo "📍 Deploying to $ip..."
    
    # Copy the fixed file
    echo "  Copying request_interpreter.py..."
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$FILE" \
        "ec2-user@$ip:/home/ec2-user/ChatMRPT/$FILE" 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo "    ✅ Success"
    else
        echo "    ❌ Failed"
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
echo "📋 Summary of fix:"
echo ""
echo "VISUALIZATION FIX:"
echo "  - Tools now properly return visualization data in ToolExecutionResult"
echo "  - Request interpreter extracts web_path from tool results"
echo "  - Visualization data is included in the 'visualizations' array"
echo "  - Frontend can now display maps and charts properly"
echo ""
echo "🧪 How to verify:"
echo "  1. Go to https://d225ar6c86586s.cloudfront.net"
echo "  2. Upload data and run any analysis"
echo "  3. Request a visualization (e.g., 'Show me the vulnerability map')"
echo "  4. Visualization should appear in the chat"
echo ""
echo "⚠️  Note: Wait 1-2 minutes for services to fully restart"
echo ""