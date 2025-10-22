#!/bin/bash

# Deploy debugging version and monitor logs
echo "🔍 Deploying debugging version to track TPR transition..."

# Files to deploy
FILES=(
    "app/data_analysis_v3/core/agent.py"
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
)

# Production instances
INSTANCES=(
    "3.21.167.170"
    "18.220.103.20"
)

# Copy key to /tmp for proper permissions
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

echo "📦 Deploying files with debug logging..."
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
echo "📝 Debug logging added at these points:"
echo "  1. When checking TPR transition"
echo "  2. When agent returns trigger_analysis"
echo "  3. When calling trigger_risk_analysis"
echo "  4. When workflow handler returns response"
echo ""
echo "🔍 To monitor logs in real-time:"
echo "ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 'sudo journalctl -u chatmrpt -f | grep --color=always DEBUG'"
echo ""
echo "Test at: https://d225ar6c86586s.cloudfront.net"
echo ""
echo "When you type 'yes', watch for these debug messages:"
echo "  - 🔴🔴🔴 DEBUG: Checking TPR transition..."
echo "  - 🔴🔴🔴 DEBUG: trigger_analysis=True..."
echo "  - 🔴🔴🔴 DEBUG: trigger_risk_analysis called..."
echo "  - 🔴🔴🔴 DEBUG: trigger_risk_analysis returning..."
