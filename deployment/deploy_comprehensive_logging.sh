#!/bin/bash
# Deploy Comprehensive Logging to Production

echo "=========================================="
echo "🔍 DEPLOYING COMPREHENSIVE LOGGING"
echo "=========================================="

# Production instances (former staging)
PROD_INSTANCES=(
    "3.21.167.170"
    "18.220.103.20"
)

SSH_KEY="/tmp/chatmrpt-key2.pem"

# Files to deploy
FILES=(
    "app/web/routes/data_analysis_v3_routes.py"
    "app/data_analysis_v3/core/agent.py"
)

echo ""
echo "📦 Files to deploy:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done
echo ""

# Deploy to each production instance
for instance in "${PROD_INSTANCES[@]}"; do
    echo "=========================================="
    echo "📤 Deploying to Production Instance: $instance"
    echo "=========================================="

    # Copy files
    for file in "${FILES[@]}"; do
        echo "  📄 Copying $file..."
        scp -i "$SSH_KEY" "$file" "ec2-user@$instance:/home/ec2-user/ChatMRPT/$file"
        if [ $? -eq 0 ]; then
            echo "  ✅ $file copied"
        else
            echo "  ❌ Failed to copy $file"
            exit 1
        fi
    done

    # Restart service
    echo ""
    echo "  🔄 Restarting chatmrpt service..."
    ssh -i "$SSH_KEY" "ec2-user@$instance" 'sudo systemctl restart chatmrpt'

    if [ $? -eq 0 ]; then
        echo "  ✅ Service restarted on $instance"
    else
        echo "  ❌ Failed to restart service on $instance"
        exit 1
    fi

    echo ""
done

echo "=========================================="
echo "✅ COMPREHENSIVE LOGGING DEPLOYED!"
echo "=========================================="
echo ""
echo "📋 Next Steps:"
echo "1. Upload a file to trigger the workflow"
echo "2. Check logs with:"
echo "   ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170"
echo "   sudo journalctl -u chatmrpt -f | grep -E 'ROUTE|AGENT|_GET_INPUT_DATA|_AGENT_NODE'"
echo ""
echo "🔍 Look for these log patterns:"
echo "   - [ROUTE] 🎯 ENTERING PURE AGENT FLOW"
echo "   - [AGENT] 🤖 AGENT.ANALYZE() CALLED"
echo "   - [_GET_INPUT_DATA] 📂 LOADING UPLOADED DATA"
echo "   - [_AGENT_NODE] 🧠 Agent node called"
echo "   - [AGENT STEP 3.1] ⚠️  THIS IS THE CRITICAL CALL"
echo ""
