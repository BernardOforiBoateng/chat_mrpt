#!/bin/bash

echo "=== Updating TPR Files from Staging ==="

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'OUTER_EOF'

# Get BOTH files from staging
echo "Getting files from staging..."
scp -i ~/.ssh/chatmrpt-key.pem ec2-user@18.220.103.20:/home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/tpr_analysis_tool.py /tmp/
scp -i ~/.ssh/chatmrpt-key.pem ec2-user@18.220.103.20:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_analysis_tool.py /tmp/tpr_analysis_tool_core.py

echo "File sizes:"
ls -lh /tmp/tpr_analysis_tool*.py

# Deploy to both production instances
for PROD_IP in 172.31.44.52 172.31.43.200; do
    echo ""
    echo "Deploying to: $PROD_IP"
    
    # Copy files to production
    scp -i ~/.ssh/chatmrpt-key.pem /tmp/tpr_analysis_tool.py ec2-user@$PROD_IP:/tmp/
    scp -i ~/.ssh/chatmrpt-key.pem /tmp/tpr_analysis_tool_core.py ec2-user@$PROD_IP:/tmp/
    
    # Install on production
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP << 'INSTALL'
    
    # Update both locations
    cp /tmp/tpr_analysis_tool.py /home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/
    cp /tmp/tpr_analysis_tool_core.py /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_analysis_tool.py
    
    # Set permissions
    chown -R ec2-user:ec2-user /home/ec2-user/ChatMRPT/app/data_analysis_v3/
    chmod 755 /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_analysis_tool.py
    chmod 755 /home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/tpr_analysis_tool.py
    
    echo "Updated files:"
    ls -lh /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_analysis_tool.py
    ls -lh /home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/tpr_analysis_tool.py
    
    # Restart service
    echo "Restarting service..."
    sudo systemctl restart chatmrpt
    sleep 5
    
    echo "✅ Updated on $PROD_IP"
INSTALL
done

echo ""
echo "=== Testing Updated Workflow ==="

OUTER_EOF
