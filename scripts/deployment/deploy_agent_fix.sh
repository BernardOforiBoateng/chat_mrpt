#!/bin/bash

# Deploy the corrected agent.py to AWS production instances
echo "🚀 Deploying corrected agent.py (without redirect_message) to AWS..."

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

echo "📦 Deploying agent.py without redirect_message..."
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
    echo "  🔍 Verifying redirect_message is removed..."
    ssh -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no \
        "ec2-user@$ip" "grep -c 'redirect_message.*Run malaria' /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/agent.py || echo '0'"
    
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
echo "📝 The fix removes redirect_message so that:"
echo "  - TPR transition exits data analysis mode ✓"
echo "  - Main chat shows the data loaded menu (not auto-trigger risk analysis) ✓"
echo "  - User can choose what to do next ✓"
