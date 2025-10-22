#!/bin/bash
# Deploy V3 tool execution fixes to staging servers

echo "🚀 Deploying V3 tool execution fixes to staging..."

# Staging server IPs (NEW as of Jan 7, 2025)
STAGING_IP1="3.21.167.170"
STAGING_IP2="18.220.103.20"

# Key path
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Check if key exists
if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSH key not found at $KEY_PATH"
    echo "Copying key..."
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
    chmod 600 /tmp/chatmrpt-key2.pem
fi

# Files to deploy
FILES_TO_DEPLOY=(
    "app/web/routes/data_analysis_v3_routes.py"
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
    "app/core/request_interpreter.py"
)

echo "📦 Files to deploy:"
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo "  - $file"
done

# Deploy to both staging servers
for ip in $STAGING_IP1 $STAGING_IP2; do
    echo ""
    echo "🔧 Deploying to staging server: $ip"
    
    # Copy files
    for file in "${FILES_TO_DEPLOY[@]}"; do
        echo "  📋 Copying $file..."
        scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$file" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file"
        if [ $? -eq 0 ]; then
            echo "    ✅ Successfully copied $file"
        else
            echo "    ❌ Failed to copy $file"
        fi
    done
    
    # Restart service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" "sudo systemctl restart chatmrpt"
    if [ $? -eq 0 ]; then
        echo "    ✅ Service restarted successfully"
    else
        echo "    ❌ Failed to restart service"
    fi
    
    # Check service status
    echo "  📊 Checking service status..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" "sudo systemctl status chatmrpt | head -10"
done

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📝 Summary of fixes deployed:"
echo "1. V3 routes now call trigger_risk_analysis() on transition"
echo "2. Flask session flags are properly set with Redis sync"
echo "3. RequestInterpreter detects V3 transition and ensures tools are registered"
echo "4. Data quality check tool is available after transition"
echo ""
echo "🧪 Test at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "Expected behavior:"
echo "1. Upload TPR file in Data Analysis tab"
echo "2. Complete TPR workflow (state, facility, age group)"
echo "3. Say 'yes' to proceed to risk analysis"
echo "4. Ask 'Check data quality'"
echo "5. Should see actual data quality results (not Python code)"