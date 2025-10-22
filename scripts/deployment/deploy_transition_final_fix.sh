#!/bin/bash

# Deploy the final fix with redirect_message to trigger data menu
echo "🚀 Deploying final TPR transition fix with redirect_message..."

# Files to deploy
FILES=(
    "app/data_analysis_v3/core/agent.py"
)

# Production instances
INSTANCES=(
    "3.21.167.170"
    "18.220.103.20"
)

# Copy key to /tmp for proper permissions
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

echo "📦 Deploying agent.py with redirect_message for data menu..."
echo ""

# Deploy to each instance
for ip in "${INSTANCES[@]}"; do
    echo "📡 Deploying to instance $ip..."
    
    # Copy files
    for file in "${FILES[@]}"; do
        echo "  📤 Copying $file..."
        scp -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no \
            "$file" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file"
        
        if [ $? -eq 0 ]; then
            echo "    ✅ Successfully copied $file"
        else
            echo "    ❌ Failed to copy $file"
            exit 1
        fi
    done
    
    # Verify the fix
    echo "  🔍 Verifying redirect_message is present..."
    ssh -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no \
        "ec2-user@$ip" "grep -q \"redirect_message.*Show me what I can do\" /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/agent.py && echo 'redirect_message found' || echo 'redirect_message NOT found'"
    
    # Restart service
    echo "  🔄 Restarting chatmrpt service..."
    ssh -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no \
        "ec2-user@$ip" "sudo systemctl restart chatmrpt"
    
    if [ $? -eq 0 ]; then
        echo "    ✅ Service restarted successfully"
    else
        echo "    ❌ Failed to restart service"
        exit 1
    fi
done

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 The fix includes redirect_message so that:"
echo "  1. TPR transition exits data analysis mode ✓"
echo "  2. Frontend sends 'Show me what I can do with my data' to main chat ✓"
echo "  3. Main chat shows the data loaded menu ✓"
echo ""
echo "🧪 Test now at: https://d225ar6c86586s.cloudfront.net"
