#!/bin/bash

# Deploy the fix that actually calls trigger_risk_analysis
echo "🚀 Deploying fix to call trigger_risk_analysis when agent returns trigger_analysis=True..."

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

echo "📦 Deploying agent.py with trigger_risk_analysis call..."
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
    echo "  🔍 Verifying trigger_risk_analysis call is present..."
    ssh -i /tmp/chatmrpt-key2.pem -o StrictHostKeyChecking=no \
        "ec2-user@$ip" "grep -q 'trigger_risk_analysis.*=' /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/agent.py && echo 'Call to trigger_risk_analysis found (correct)' || echo 'NOT FOUND (error)'"
    
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
echo "📝 The fix now:"
echo "  1. Agent returns trigger_analysis=True"
echo "  2. Agent CALLS tpr_handler.trigger_risk_analysis()"
echo "  3. Workflow handler returns exit_data_analysis_mode + __DATA_UPLOADED__"
echo "  4. Frontend exits V3 and sends __DATA_UPLOADED__ to main chat"
echo "  5. Main chat shows data menu"
echo ""
echo "Test at: https://d225ar6c86586s.cloudfront.net"
