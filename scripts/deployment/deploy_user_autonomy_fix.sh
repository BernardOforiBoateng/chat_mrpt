#!/bin/bash
# Deploy user autonomy fix - Remove auto-trigger of risk analysis

echo "========================================"
echo "Deploying User Autonomy Fix"
echo "========================================"
echo ""

# Check if the SSH key exists
KEY_PATH="$HOME/.ssh/chatmrpt-key.pem"
if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSH key not found at $KEY_PATH"
    echo "Trying alternate location..."
    KEY_PATH="/tmp/chatmrpt-key2.pem"
    if [ ! -f "$KEY_PATH" ]; then
        echo "Copying key to /tmp..."
        cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
        chmod 600 /tmp/chatmrpt-key2.pem
        KEY_PATH="/tmp/chatmrpt-key2.pem"
    fi
fi

echo "Using SSH key: $KEY_PATH"
echo ""

# Production instances
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"

# File to deploy
FILES=(
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
)

echo "Deploying to production instances..."
echo "Target file: app/data_analysis_v3/core/tpr_workflow_handler.py"
echo ""

# Function to deploy to an instance
deploy_to_instance() {
    local ip=$1
    local instance_name=$2

    echo "----------------------------------------"
    echo "Deploying to $instance_name ($ip)..."
    echo "----------------------------------------"

    # Deploy the file
    for file in "${FILES[@]}"; do
        echo "Deploying $file..."

        # Create backup
        ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@$ip \
            "cd /home/ec2-user/ChatMRPT && cp $file ${file}.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true"

        # Copy the new file
        scp -o StrictHostKeyChecking=no -i "$KEY_PATH" "$file" ec2-user@$ip:/home/ec2-user/ChatMRPT/$file

        if [ $? -eq 0 ]; then
            echo "  ✓ $file deployed"
        else
            echo "  ✗ Failed to deploy $file"
            return 1
        fi
    done

    # Restart the service
    echo "Restarting ChatMRPT service..."
    ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@$ip \
        "sudo systemctl restart chatmrpt"

    if [ $? -eq 0 ]; then
        echo "✓ Service restarted"
    else
        echo "✗ Failed to restart service"
        return 1
    fi

    echo "✓ Deployment to $instance_name completed"
    echo ""

    return 0
}

# Deploy to both instances
echo "Starting deployment..."
echo ""

deploy_to_instance "$INSTANCE_1" "Production Instance 1"
RESULT_1=$?

deploy_to_instance "$INSTANCE_2" "Production Instance 2"
RESULT_2=$?

echo "========================================"
echo "DEPLOYMENT SUMMARY"
echo "========================================"

if [ $RESULT_1 -eq 0 ] && [ $RESULT_2 -eq 0 ]; then
    echo "✅ DEPLOYMENT SUCCESSFUL"
    echo ""
    echo "Fixed:"
    echo "  • Removed auto-trigger of risk analysis after TPR transition"
    echo "  • Users now see the standard menu and can choose what to do"
    echo "  • User autonomy restored - no forced actions"
    echo ""
    echo "After TPR analysis completes and user says 'yes' to transition:"
    echo "  • They see: 'What would you like to do?'"
    echo "  • They can choose: risk analysis, data quality, explore variables, etc."
    echo "  • No automatic risk analysis trigger"
    echo ""
    echo "Access the application at:"
    echo "  https://d225ar6c86586s.cloudfront.net"
else
    echo "⚠️ DEPLOYMENT PARTIALLY FAILED"
    echo ""
    if [ $RESULT_1 -ne 0 ]; then
        echo "❌ Failed to deploy to Instance 1 ($INSTANCE_1)"
    fi
    if [ $RESULT_2 -ne 0 ]; then
        echo "❌ Failed to deploy to Instance 2 ($INSTANCE_2)"
    fi
    echo ""
    echo "Please check the errors above and try again."
fi

echo ""
echo "========================================"
echo "Deployment script completed"
echo "========================================"