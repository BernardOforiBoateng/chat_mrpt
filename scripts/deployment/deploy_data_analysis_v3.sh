#!/bin/bash

# Deploy Data Analysis V3 to AWS Staging
# This script deploys the new LangGraph-based data analysis system

echo "=========================================="
echo "Deploying Data Analysis V3 to AWS Staging"
echo "=========================================="

# Configuration
STAGING_IPS="3.21.167.170 18.220.103.20"
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Copy key if needed
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

# Files to deploy
echo "📦 Preparing files to deploy..."

# Create deployment package
tar -czf data_analysis_v3.tar.gz \
    app/data_analysis_v3/ \
    app/core/request_interpreter.py \
    requirements.txt

echo "✅ Deployment package created"

# Deploy to each staging instance
for IP in $STAGING_IPS; do
    echo ""
    echo "🚀 Deploying to $IP..."
    
    # Copy files
    echo "📤 Copying files..."
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no \
        data_analysis_v3.tar.gz \
        ec2-user@$IP:/home/ec2-user/
    
    # Install and restart
    echo "⚙️ Installing on server..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no ec2-user@$IP << 'EOF'
        cd /home/ec2-user/ChatMRPT
        
        # Backup existing files
        echo "📦 Creating backup..."
        cp -r app/core/request_interpreter.py app/core/request_interpreter.py.backup
        
        # Extract new files
        echo "📂 Extracting files..."
        tar -xzf /home/ec2-user/data_analysis_v3.tar.gz
        
        # Install dependencies
        echo "📚 Installing dependencies..."
        source venv/bin/activate
        pip install langgraph langchain-core langchain-openai --quiet
        
        # Restart service
        echo "🔄 Restarting service..."
        sudo systemctl restart chatmrpt
        
        # Check status
        sleep 3
        if sudo systemctl is-active --quiet chatmrpt; then
            echo "✅ Service restarted successfully on $(hostname -I | awk '{print $1}')"
        else
            echo "❌ Service failed to start on $(hostname -I | awk '{print $1}')"
            sudo journalctl -u chatmrpt -n 20
        fi
EOF
    
    echo "✅ Deployed to $IP"
done

# Cleanup
rm -f data_analysis_v3.tar.gz

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "Test URLs:"
echo "1. http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "2. http://3.21.167.170:5000"
echo "3. http://18.220.103.20:5000"
echo ""
echo "Test queries after uploading data:"
echo "- 'What's in my data?'"
echo "- 'Show me summary statistics'"
echo "- 'Which areas have highest values?'"
echo "- 'Create a bar chart of the data'"