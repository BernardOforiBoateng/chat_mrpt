#!/bin/bash

# Deploy Newcomer Helper modules to production
echo "==========================================="
echo "Deploying Newcomer Helper Modules"
echo "==========================================="
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Files to deploy
FILES=(
    # Helper modules
    "app/helpers/__init__.py"
    "app/helpers/welcome_helper.py"
    "app/helpers/data_requirements_helper.py"
    "app/helpers/workflow_progress_helper.py"
    "app/helpers/tool_discovery_helper.py"
    "app/helpers/error_recovery_helper.py"

    # Updated routes with helper integration
    "app/web/routes/analysis_routes.py"
    "app/web/routes/upload_routes.py"

    # Enhanced help tool
    "app/tools/chatmrpt_help_tool.py"
)

# Production instances
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

KEY_FILE="/tmp/chatmrpt-key2.pem"

# Check key file
if [ ! -f "$KEY_FILE" ]; then
    echo "❌ Key file not found at $KEY_FILE"
    exit 1
fi

echo "📦 Files to deploy:"
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file (NOT FOUND)"
    fi
done

echo ""
echo "🎯 Target instances:"
echo "  - Instance 1: $INSTANCE1"
echo "  - Instance 2: $INSTANCE2"
echo ""

# Function to deploy to an instance
deploy_to_instance() {
    local INSTANCE=$1
    local INSTANCE_NUM=$2

    echo "==========================================="
    echo "Deploying to Instance $INSTANCE_NUM: $INSTANCE"
    echo "==========================================="

    # Create helpers directory if it doesn't exist
    echo "📁 Creating helpers directory..."
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" \
        "mkdir -p /home/ec2-user/ChatMRPT/app/helpers"

    # Copy files
    for FILE in "${FILES[@]}"; do
        if [ -f "$FILE" ]; then
            echo "📤 Copying $FILE..."
            scp -i "$KEY_FILE" -o StrictHostKeyChecking=no \
                "$FILE" "ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/$FILE"

            if [ $? -eq 0 ]; then
                echo "  ✅ Success"
            else
                echo "  ❌ Failed to copy $FILE"
                return 1
            fi
        fi
    done

    # Restart service
    echo "🔄 Restarting ChatMRPT service..."
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" \
        "sudo systemctl restart chatmrpt"

    if [ $? -eq 0 ]; then
        echo "  ✅ Service restarted"
    else
        echo "  ❌ Failed to restart service"
        return 1
    fi

    # Check service status
    echo "🔍 Checking service status..."
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" \
        "sudo systemctl is-active chatmrpt"

    echo "✅ Deployment to Instance $INSTANCE_NUM complete"
    echo ""

    return 0
}

# Deploy to both instances
SUCCESS=true
deploy_to_instance "$INSTANCE1" "1" || SUCCESS=false
deploy_to_instance "$INSTANCE2" "2" || SUCCESS=false

echo "==========================================="
if [ "$SUCCESS" = true ]; then
    echo "✨ Deployment Complete!"
    echo "==========================================="
    echo ""
    echo "🚀 Newcomer Helper Features Deployed:"
    echo "  ✅ Welcome message for first-time users"
    echo "  ✅ Data requirements validation"
    echo "  ✅ Workflow progress tracking"
    echo "  ✅ Tool discovery assistance"
    echo "  ✅ Error recovery suggestions"
    echo "  ✅ Proactive help system"
    echo ""
    echo "📍 Access points:"
    echo "  - CloudFront: https://d225ar6c86586s.cloudfront.net"
    echo "  - ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
    echo ""
    echo "🧪 Test the new features:"
    echo "  1. New user sees welcome message"
    echo "  2. 'What can I do?' shows available tools"
    echo "  3. 'Show progress' displays workflow status"
    echo "  4. 'Data requirements' explains format needs"
    echo "  5. Errors show helpful recovery suggestions"
else
    echo "⚠️ Deployment Partially Failed!"
    echo "==========================================="
    echo "Check the logs above for errors"
fi
echo ""