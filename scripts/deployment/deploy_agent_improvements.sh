#!/bin/bash

# Deploy Improved Data Analysis V3 Agent
echo "🚀 Deploying Improved Data Analysis V3 Agent to Staging..."

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
STAGING_IPS=("3.21.167.170" "18.220.103.20")
REMOTE_USER="ec2-user"
REMOTE_PATH="/home/ec2-user/ChatMRPT"

# Copy SSH key
cp aws_files/chatmrpt-key.pem $KEY_PATH
chmod 600 $KEY_PATH

# Files to deploy
FILES=(
    "app/data_analysis_v3/prompts/system_prompt.py"
    "app/data_analysis_v3/formatters/response_formatter.py"
    "app/data_analysis_v3/core/agent.py"
)

# Deploy to both staging instances
for IP in "${STAGING_IPS[@]}"; do
    echo "📦 Deploying to staging instance: $IP"
    
    # Copy files
    for FILE in "${FILES[@]}"; do
        echo "  📄 Copying $FILE..."
        scp -i $KEY_PATH -o StrictHostKeyChecking=no "$FILE" "$REMOTE_USER@$IP:$REMOTE_PATH/$FILE"
    done
    
    # Restart service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no $REMOTE_USER@$IP "sudo systemctl restart chatmrpt"
    
    echo "  ✅ Deployment to $IP complete!"
done

echo "✅ Improved Data Analysis V3 Agent deployed to all staging instances!"
echo "🔗 Test at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "📝 Changes deployed:"
echo "  - Agent now explores data structure first before analysis"
echo "  - Removed hardcoded solutions"
echo "  - Agent adapts to actual available columns"
echo "  - Better error handling without prescriptive fixes"