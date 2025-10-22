#!/bin/bash

# Deploy Arena Help System to Production
echo "============================================"
echo "Deploying Arena-Based Intelligent Help System"
echo "============================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Files to deploy
FILES=(
    "app/core/arena_system_prompt.py"
    "app/core/chatmrpt_system_documentation.md"
    "app/web/routes/analysis_routes.py"
    "app/web/routes/upload_routes.py"
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

echo "📦 Deploying Arena Help System:"
echo "  ✨ Complete system documentation embedded"
echo "  ✨ Dynamic context-aware suggestions"
echo "  ✨ Intelligent help for newcomers"
echo "  ✨ No external documentation needed!"
echo ""

# Deploy to both instances
for INSTANCE in $INSTANCE1 $INSTANCE2; do
    echo "============================================"
    echo "Deploying to $INSTANCE"
    echo "============================================"

    # Copy each file
    for FILE in "${FILES[@]}"; do
        echo "📤 Copying $FILE..."
        scp -i "$KEY_FILE" -o StrictHostKeyChecking=no \
            "$FILE" \
            "ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/$FILE"

        if [ $? -eq 0 ]; then
            echo "  ✅ $FILE copied"
        else
            echo "  ❌ Failed to copy $FILE"
            exit 1
        fi
    done

    # Restart service
    echo "🔄 Restarting service..."
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" \
        "sudo systemctl restart chatmrpt"

    if [ $? -eq 0 ]; then
        echo "  ✅ Service restarted"
    else
        echo "  ❌ Failed to restart service"
        exit 1
    fi

    # Check service status
    echo "🔍 Checking service status..."
    ssh -i "$KEY_FILE" -o StrictHostKeyChecking=no "ec2-user@$INSTANCE" \
        "sudo systemctl is-active chatmrpt"

    echo "✅ Deployment to $INSTANCE complete"
    echo ""
done

echo "============================================"
echo "✨ Arena Help System Deployed!"
echo "============================================"
echo ""
echo "🎯 What's New:"
echo "  • Arena models have complete system knowledge"
echo "  • Dynamic suggestions based on user context"
echo "  • Intelligent help responses"
echo "  • Newcomers can use ChatMRPT without external help"
echo ""
echo "🔬 Test it:"
echo "  1. Ask: 'What is ChatMRPT?'"
echo "  2. Ask: 'How do I upload data?'"
echo "  3. Ask: 'What should I do next?'"
echo "  4. Watch suggestions update based on context"
echo ""
echo "📍 Live at:"
echo "  https://d225ar6c86586s.cloudfront.net"
echo ""