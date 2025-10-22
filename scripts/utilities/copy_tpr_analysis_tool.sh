#!/bin/bash

echo "=== Copying TPR Analysis Tool from Staging ==="

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'OUTER_EOF'

# Check if file exists on production first
echo "Checking production for tpr_analysis_tool.py:"
for PROD_IP in 172.31.44.52; do
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP 'ls -lh /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_analysis_tool.py 2>/dev/null || echo "Not found on production"'
done

# Get file from staging
echo ""
echo "Getting tpr_analysis_tool.py from staging..."
scp -i ~/.ssh/chatmrpt-key.pem ec2-user@18.220.103.20:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_analysis_tool.py /tmp/ 2>/dev/null
if [ ! -f /tmp/tpr_analysis_tool.py ]; then
    # Try tools directory
    scp -i ~/.ssh/chatmrpt-key.pem ec2-user@18.220.103.20:/home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/tpr_analysis_tool.py /tmp/
fi

echo "File size:"
ls -lh /tmp/tpr_analysis_tool.py

# Deploy to both production instances
for PROD_IP in 172.31.44.52 172.31.43.200; do
    echo ""
    echo "Deploying to: $PROD_IP"
    
    # Copy file to production
    scp -i ~/.ssh/chatmrpt-key.pem /tmp/tpr_analysis_tool.py ec2-user@$PROD_IP:/tmp/
    
    # Install on production - try both locations
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP << 'INSTALL'
    # Create directories if needed
    mkdir -p /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/
    mkdir -p /home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/
    
    # Copy to both locations (core and tools)
    cp /tmp/tpr_analysis_tool.py /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/
    cp /tmp/tpr_analysis_tool.py /home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/
    
    # Set permissions
    chown -R ec2-user:ec2-user /home/ec2-user/ChatMRPT/app/data_analysis_v3/
    chmod 755 /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_analysis_tool.py
    chmod 755 /home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/tpr_analysis_tool.py
    
    # Verify
    echo "Installed in core:"
    ls -lh /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_analysis_tool.py
    echo "Installed in tools:"
    ls -lh /home/ec2-user/ChatMRPT/app/data_analysis_v3/tools/tpr_analysis_tool.py
    
    # Restart service
    echo "Restarting service..."
    sudo systemctl restart chatmrpt
    sleep 5
    
    echo "Service status:"
    sudo systemctl is-active chatmrpt
    
    echo "✅ tpr_analysis_tool.py deployed to $PROD_IP"
INSTALL
done

echo ""
echo "=== Complete ==="

OUTER_EOF
