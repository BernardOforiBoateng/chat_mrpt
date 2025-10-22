#!/bin/bash

# Deploy "Always Show Suggestions" update to production
echo "==========================================="
echo "Deploying Persistent Suggestions Update"
echo "==========================================="
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Files to deploy
FILES=(
    "app/web/routes/analysis_routes.py"
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

echo "📦 Deploying update:"
echo "  ✨ Suggestions now appear with EVERY response"
echo "  ✨ Users can toggle suggestions on/off"
echo "  ✨ Suggestions persist across session"
echo ""

# Deploy to both instances
for INSTANCE in $INSTANCE1 $INSTANCE2; do
    echo "==========================================="
    echo "Deploying to $INSTANCE"
    echo "==========================================="

    # Copy updated file
    echo "📤 Copying updated analysis_routes.py..."
    scp -i "$KEY_FILE" -o StrictHostKeyChecking=no \
        "app/web/routes/analysis_routes.py" \
        "ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/app/web/routes/"

    if [ $? -eq 0 ]; then
        echo "  ✅ File copied successfully"
    else
        echo "  ❌ Failed to copy file"
        exit 1
    fi

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

echo "==========================================="
echo "✨ Persistent Suggestions Deployed!"
echo "==========================================="
echo ""
echo "🎯 What's New:"
echo "  • Suggestions appear with EVERY response"
echo "  • Top 5 relevant actions always shown"
echo "  • Workflow status displayed"
echo "  • Toggle endpoint: POST /toggle_suggestions"
echo ""
echo "📍 Test it at:"
echo "  https://d225ar6c86586s.cloudfront.net"
echo ""
echo "💡 Frontend can now:"
echo "  1. Show suggestions panel by default"
echo "  2. Let users hide/show with toggle button"
echo "  3. Persist preference in session"
echo ""