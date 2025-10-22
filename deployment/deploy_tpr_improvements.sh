#!/bin/bash

# Deploy TPR workflow improvements to AWS production instances
# Production instances: 3.21.167.170, 18.220.103.20

echo "🚀 Deploying TPR Workflow Improvements to AWS Production"
echo "========================================================="

# Set variables
KEY_PATH="$HOME/.ssh/chatmrpt-key.pem"
PRODUCTION_IPS=("3.21.167.170" "18.220.103.20")
FILES_TO_DEPLOY=(
    "app/data_analysis_v3/core/formatters.py"
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
    "app/data_analysis_v3/prompts/system_prompt.py"
    "app/data_analysis_v3/tools/tpr_analysis_tool.py"
    "app/web/routes/data_analysis_v3_routes.py"
)

# Check if key exists
if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSH key not found at $KEY_PATH"
    echo "Copying from aws_files..."
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

# Function to deploy to a single instance
deploy_to_instance() {
    local ip=$1
    echo ""
    echo "📦 Deploying to instance: $ip"
    echo "--------------------------------"

    # Copy each file
    for file in "${FILES_TO_DEPLOY[@]}"; do
        echo "  → Copying $file..."
        scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
            "$file" \
            "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file" 2>/dev/null

        if [ $? -eq 0 ]; then
            echo "    ✅ Success"
        else
            echo "    ❌ Failed to copy $file"
        fi
    done

    # Restart the service
    echo "  → Restarting ChatMRPT service..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" \
        "sudo systemctl restart chatmrpt" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo "    ✅ Service restarted"
    else
        echo "    ⚠️  Could not restart service"
    fi

    # Check service status
    echo "  → Checking service status..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" \
        "sudo systemctl is-active chatmrpt" 2>/dev/null

    echo "  ✅ Deployment to $ip complete"
}

# Deploy to all production instances
echo ""
echo "🔄 Starting deployment to ${#PRODUCTION_IPS[@]} production instances..."

for ip in "${PRODUCTION_IPS[@]}"; do
    deploy_to_instance "$ip" &
done

# Wait for all deployments to complete
wait

echo ""
echo "========================================================="
echo "✅ TPR Workflow Improvements Deployed Successfully!"
echo ""
echo "Changes deployed:"
echo "  • Friendly blue warning (💡) instead of red (⚠️)"
echo "  • Conversational message formatting"
echo "  • Simplified TPR results (5 lines instead of 15+)"
echo "  • Natural language understanding"
echo "  • Visual-first approach with charts"
echo ""
echo "Access the application at:"
echo "  🌐 https://d225ar6c86586s.cloudfront.net"
echo ""
echo "Test the improvements:"
echo "  1. Upload TPR data"
echo "  2. Check for blue note instead of red warning"
echo "  3. Type 'TPR' to start workflow"
echo "  4. Try conversational responses like 'yes', 'sure'"
echo "========================================================="