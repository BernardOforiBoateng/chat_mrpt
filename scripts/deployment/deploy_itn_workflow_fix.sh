#!/bin/bash
#
# Deploy ITN Workflow Fix to Production
# Fixes the bug where analysis re-runs when requesting ITN planning
#
echo "================================================"
echo "Deploying ITN Workflow Fix to Production"
echo "================================================"
echo ""

# Configuration
INSTANCES=("3.21.167.170" "18.220.103.20")  # Production instances
KEY_FILE="$HOME/.ssh/chatmrpt-key.pem"

# Prepare key file
if [ ! -f "$KEY_FILE" ]; then
    cp aws_files/chatmrpt-key.pem "$KEY_FILE"
    chmod 600 "$KEY_FILE"
    echo "✅ SSH key prepared"
fi

# Files to deploy
FILES=(
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
    "app/core/request_interpreter.py"
    "app/core/workflow_state_manager.py"
)

echo "📦 Files to deploy:"
for file in "${FILES[@]}"; do
    echo "   - $file"
done
echo ""

# Deploy to each instance
for instance_ip in "${INSTANCES[@]}"; do
    echo "🚀 Deploying to instance: $instance_ip"
    
    # Copy each file
    for file in "${FILES[@]}"; do
        echo "   📄 Copying $file..."
        scp -i "$KEY_FILE" "$file" "ec2-user@${instance_ip}:/home/ec2-user/ChatMRPT/$file"
        if [ $? -eq 0 ]; then
            echo "      ✅ Success"
        else
            echo "      ❌ Failed to copy $file"
            exit 1
        fi
    done
    
    # Restart the service
    echo "   🔄 Restarting ChatMRPT service..."
    ssh -i "$KEY_FILE" "ec2-user@${instance_ip}" 'sudo systemctl restart chatmrpt'
    if [ $? -eq 0 ]; then
        echo "      ✅ Service restarted"
    else
        echo "      ❌ Failed to restart service"
        exit 1
    fi
    
    # Check service status
    echo "   🔍 Checking service status..."
    ssh -i "$KEY_FILE" "ec2-user@${instance_ip}" 'sudo systemctl status chatmrpt | grep -E "Active:|Main PID:"'
    
    echo "   ✅ Instance $instance_ip deployment complete"
    echo ""
done

echo "================================================"
echo "✅ ITN Workflow Fix Deployed Successfully!"
echo "================================================"
echo ""
echo "📝 Changes deployed:"
echo "1. ✅ Stop deleting .analysis_complete marker during transitions"
echo "2. ✅ Preserve analysis_complete flag during workflow transitions"
echo "3. ✅ Trust evidence (marker files) over state inconsistencies"
echo "4. ✅ WorkflowStateManager preserves critical flags"
echo "5. ✅ ITN tool checks for marker file evidence"
echo ""
echo "🧪 Test the fix:"
echo "1. Complete risk analysis"
echo "2. Request ITN planning"
echo "3. Should NOT re-run analysis"
echo ""
echo "🌐 Access at: https://d225ar6c86586s.cloudfront.net"