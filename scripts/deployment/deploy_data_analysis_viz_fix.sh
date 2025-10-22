#!/bin/bash

# Deploy Data Analysis V3 Visualization Fixes
echo "🚀 Deploying Data Analysis V3 Visualization Fixes to Staging..."

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
    "app/data_analysis_v3/tools/python_tool.py"
    "app/data_analysis_v3/core/agent.py"
    "app/core/request_interpreter.py"
)

# Deploy to both staging instances
for IP in "${STAGING_IPS[@]}"; do
    echo "📦 Deploying to staging instance: $IP"
    
    # Copy files
    for FILE in "${FILES[@]}"; do
        echo "  📄 Copying $FILE..."
        scp -i $KEY_PATH -o StrictHostKeyChecking=no "$FILE" "$REMOTE_USER@$IP:$REMOTE_PATH/$FILE"
    done
    
    # Create visualizations directory
    echo "  📁 Creating static visualizations directory..."
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no $REMOTE_USER@$IP "mkdir -p $REMOTE_PATH/app/static/visualizations"
    
    # Restart service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no $REMOTE_USER@$IP "sudo systemctl restart chatmrpt"
    
    echo "  ✅ Deployment to $IP complete!"
done

echo "✅ Data Analysis V3 Visualization Fixes deployed to all staging instances!"
echo "🔗 Test at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"