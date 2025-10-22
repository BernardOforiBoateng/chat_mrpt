#!/bin/bash

# Deploy Data Analysis V3 fixes to staging
# Deploys to both staging instances

echo "==========================================="
echo "Deploying Data Analysis V3 Fixes to Staging"
echo "==========================================="

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
STAGING_IPS="3.21.167.170 18.220.103.20"

# Files to deploy
FILES_TO_DEPLOY=(
    "app/data_analysis_v3/prompts/system_prompt.py"
    "app/data_analysis_v3/core/agent.py"
    "app/data_analysis_v3/core/executor.py"
    "app/data_analysis_v3/tools/python_tool.py"
    "app/data_analysis_v3/formatters/response_formatter.py"
)

# Ensure key exists and has correct permissions
if [ ! -f "$KEY_PATH" ]; then
    echo "Copying SSH key to /tmp..."
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

# Deploy to each staging instance
for IP in $STAGING_IPS; do
    echo ""
    echo "Deploying to staging instance: $IP"
    echo "----------------------------------------"
    
    # Copy files
    for FILE in "${FILES_TO_DEPLOY[@]}"; do
        echo "  Copying $FILE..."
        scp -i "$KEY_PATH" "$FILE" "ec2-user@$IP:/home/ec2-user/ChatMRPT/$FILE"
        if [ $? -eq 0 ]; then
            echo "    ✅ Copied successfully"
        else
            echo "    ❌ Failed to copy $FILE"
            exit 1
        fi
    done
    
    # Restart service
    echo "  Restarting ChatMRPT service..."
    ssh -i "$KEY_PATH" "ec2-user@$IP" "sudo systemctl restart chatmrpt"
    if [ $? -eq 0 ]; then
        echo "    ✅ Service restarted"
    else
        echo "    ❌ Failed to restart service"
        exit 1
    fi
    
    # Check service status
    echo "  Checking service status..."
    ssh -i "$KEY_PATH" "ec2-user@$IP" "sudo systemctl is-active chatmrpt"
    
    echo "  ✅ Deployment to $IP complete"
done

echo ""
echo "==========================================="
echo "✅ Deployment Complete to ALL Staging Instances!"
echo "==========================================="
echo ""
echo "You can now test at:"
echo "  http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "To run tests:"
echo "  python tests/test_data_analysis_v3_real_simulation.py"