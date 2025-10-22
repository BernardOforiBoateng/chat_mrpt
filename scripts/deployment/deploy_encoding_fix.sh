#!/bin/bash

echo "🚀 Deploying Data Analysis V3 encoding fixes to staging..."

# Copy SSH key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Files to deploy
FILES="app/data_analysis_v3/core/encoding_handler.py \
       app/data_analysis_v3/core/agent.py \
       app/data_analysis_v3/tools/python_tool.py \
       app/data_analysis_v3/core/tpr_workflow_handler.py \
       app/data_analysis_v3/core/lazy_loader.py \
       app/data_analysis_v3/core/metadata_cache.py \
       app/data_analysis_v3/tools/tpr_analysis_tool.py"

# Deploy to both staging instances
for ip in 3.21.167.170 18.220.103.20; do
    echo ""
    echo "📦 Deploying to staging instance: $ip"
    
    # Copy files
    for file in $FILES; do
        echo "  Copying $file..."
        scp -i /tmp/chatmrpt-key2.pem "$file" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file"
    done
    
    # Install chardet if not already installed
    echo "  Installing chardet package..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip "cd /home/ec2-user/ChatMRPT && source chatmrpt_venv_new/bin/activate && pip install chardet"
    
    # Restart service
    echo "  Restarting service..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip "sudo systemctl restart chatmrpt"
    
    echo "✅ Deployed to $ip"
done

echo ""
echo "✅ Encoding fixes deployed to staging!"
echo ""
echo "📝 Test with:"
echo "1. Upload TPR data with special characters (≥, <)"
echo "2. Ask: 'Show me the top 10 facilities by testing volume'"
echo "3. Verify real facility names are shown, not 'Facility A, B, C'"
echo ""
echo "URL: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"