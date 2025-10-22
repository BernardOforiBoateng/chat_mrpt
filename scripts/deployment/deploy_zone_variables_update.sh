#!/bin/bash

# Deploy updated zone variables to production
echo "============================================"
echo "Deploying Zone Variables Update"
echo "============================================"
echo "Timestamp: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Files to deploy
FILES=(
    "app/analysis/region_aware_selection.py"
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
echo "  ✨ Updated zone variables from CSV"
echo "  ✨ Test positivity rate (u5_tpr_rdt) now primary variable"
echo "  ✨ Simplified variable sets per zone (4-6 variables)"
echo ""

# Deploy to both instances
for INSTANCE in $INSTANCE1 $INSTANCE2; do
    echo "============================================"
    echo "Deploying to $INSTANCE"
    echo "============================================"

    # Copy updated file
    echo "📤 Copying updated region_aware_selection.py..."
    scp -i "$KEY_FILE" -o StrictHostKeyChecking=no \
        "app/analysis/region_aware_selection.py" \
        "ec2-user@$INSTANCE:/home/ec2-user/ChatMRPT/app/analysis/"

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

echo "============================================"
echo "✨ Zone Variables Update Deployed!"
echo "============================================"
echo ""
echo "🎯 What's Updated:"
echo "  • North Central: 6 variables (TPR, lights, housing, wetness, water, NDMI)"
echo "  • North East: 4 variables (TPR, water, rainfall, wetness)"
echo "  • North West: 5 variables (TPR, rainfall, NDWI, housing, elevation)"
echo "  • South East/South/West: 4 variables (TPR, NDWI, housing, elevation)"
echo ""
echo "📍 Test at:"
echo "  https://d225ar6c86586s.cloudfront.net"
echo ""