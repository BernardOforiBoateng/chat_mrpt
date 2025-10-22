#!/bin/bash
# Deploy PCA Skip Message Fix to AWS Production

echo "========================================"
echo "Deploying PCA Skip Message Fix to AWS"
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

# Production instances (formerly staging)
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"

# File to deploy
FILE="app/tools/complete_analysis_tools.py"

echo "Deploying to production instances..."
echo "Target file: $FILE"
echo ""

# Function to deploy to an instance
deploy_to_instance() {
    local ip=$1
    local instance_name=$2

    echo "----------------------------------------"
    echo "Deploying to $instance_name ($ip)..."
    echo "----------------------------------------"

    # First, backup the existing file
    echo "Creating backup on $instance_name..."
    ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@$ip \
        "cd /home/ec2-user/ChatMRPT && cp $FILE ${FILE}.backup_$(date +%Y%m%d_%H%M%S)"

    if [ $? -eq 0 ]; then
        echo "✓ Backup created"
    else
        echo "✗ Failed to create backup"
        return 1
    fi

    # Copy the new file
    echo "Copying fixed file to $instance_name..."
    scp -o StrictHostKeyChecking=no -i "$KEY_PATH" "$FILE" ec2-user@$ip:/home/ec2-user/ChatMRPT/$FILE

    if [ $? -eq 0 ]; then
        echo "✓ File copied successfully"
    else
        echo "✗ Failed to copy file"
        return 1
    fi

    # Restart the service
    echo "Restarting ChatMRPT service on $instance_name..."
    ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@$ip \
        "sudo systemctl restart chatmrpt"

    if [ $? -eq 0 ]; then
        echo "✓ Service restarted"
    else
        echo "✗ Failed to restart service"
        return 1
    fi

    # Check service status
    echo "Checking service status on $instance_name..."
    ssh -o StrictHostKeyChecking=no -i "$KEY_PATH" ec2-user@$ip \
        "sudo systemctl status chatmrpt | head -5"

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
    echo "The PCA skip message fix has been deployed to both production instances."
    echo ""
    echo "Users will now see proper messages when PCA is skipped due to statistical tests:"
    echo "- Composite analysis results"
    echo "- Statistical test explanation"
    echo "- ITN planning guidance"
    echo "- No generic fallback message"
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