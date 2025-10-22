#!/bin/bash

# Deploy TPR transition fixes to AWS production instances
echo "🚀 Deploying TPR transition fixes to AWS production instances..."

# Files to deploy
FILES=(
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
    "app/web/routes/data_analysis_v3_routes.py"
)

# Production instances (formerly staging)
INSTANCES=(
    "3.21.167.170"
    "18.220.103.20"
)

# Copy key to /tmp for proper permissions
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

echo "📦 Files to deploy:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done

echo ""
echo "🎯 Target instances:"
for ip in "${INSTANCES[@]}"; do
    echo "  - $ip"
done

echo ""
echo "Starting deployment..."

# Deploy to each instance
for ip in "${INSTANCES[@]}"; do
    echo ""
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
    
    # Check service status
    echo "  📊 Checking service status..."
    ssh -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no \
        "ec2-user@$ip" "sudo systemctl status chatmrpt --no-pager | head -10"
done

echo ""
echo "✅ Deployment complete to all instances!"
echo ""
echo "📝 Summary of changes deployed:"
echo "  1. Fixed TPR workflow to create raw_data.csv for main chat compatibility"
echo "  2. Added Flask session persistence when TPR transition triggers"
echo "  3. Ensured agent_state.json is updated for multi-worker sync"
echo "  4. Fixed transition response to show data loaded menu (not auto-trigger risk analysis)"
echo ""
echo "🧪 Test the fix:"
echo "  1. Go to https://d225ar6c86586s.cloudfront.net"
echo "  2. Upload data through Data Analysis tab"
echo "  3. Complete TPR workflow (select state, facility level, age group)"
echo "  4. When asked about transitioning to risk analysis, type 'yes'"
echo "  5. You should see the data loaded menu (not go directly to risk analysis)"
echo ""
echo "🔍 Monitor logs with:"
echo "  ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 'sudo journalctl -u chatmrpt -f'"
