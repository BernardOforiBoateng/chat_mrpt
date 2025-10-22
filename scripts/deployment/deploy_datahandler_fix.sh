#!/bin/bash

echo "🚀 Deploying DataHandler initialization fix to staging..."
echo "==========================================="

# Files to deploy
FILES=(
    "app/data_analysis_v3/core/tpr_workflow_handler.py"
)

# Staging servers
STAGING_IPS=("3.21.167.170" "18.220.103.20")
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Prepare key
echo "📋 Preparing SSH key..."
cp aws_files/chatmrpt-key.pem $KEY_PATH
chmod 600 $KEY_PATH

# Deploy to all staging instances
for IP in "${STAGING_IPS[@]}"; do
    echo ""
    echo "📦 Deploying to staging instance: $IP"
    
    # Copy files
    for FILE in "${FILES[@]}"; do
        echo "  📄 Copying $FILE..."
        scp -i $KEY_PATH -o StrictHostKeyChecking=no \
            "$FILE" \
            "ec2-user@$IP:/home/ec2-user/ChatMRPT/$FILE"
    done
    
    # Restart service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no "ec2-user@$IP" \
        "sudo systemctl restart chatmrpt && echo '  ✅ Service restarted successfully'"
done

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Test the fix at:"
echo "  http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "Test workflow:"
echo "1. Upload TPR data file"
echo "2. Say 'guide me through TPR calculation'"
echo "3. Complete TPR workflow"
echo "4. When asked about risk analysis, type 'yes'"
echo "5. Verify risk analysis runs without DataHandler error"