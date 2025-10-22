#!/bin/bash

echo "=== Copying tpr_workflow_handler.py from Staging ==="

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'OUTER_EOF'

# Get file from staging
echo "Getting tpr_workflow_handler.py from staging..."
scp -i ~/.ssh/chatmrpt-key.pem ec2-user@18.220.103.20:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_workflow_handler.py /tmp/

echo "File size:"
ls -lh /tmp/tpr_workflow_handler.py

# Deploy to both production instances
for PROD_IP in 172.31.44.52 172.31.43.200; do
    echo ""
    echo "Deploying to: $PROD_IP"
    
    # Copy file to production
    scp -i ~/.ssh/chatmrpt-key.pem /tmp/tpr_workflow_handler.py ec2-user@$PROD_IP:/tmp/
    
    # Install on production
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP << 'INSTALL'
    # Backup existing if any
    [ -f /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_workflow_handler.py ] && \
        cp /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_workflow_handler.py \
           /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_workflow_handler.py.backup
    
    # Copy to correct location
    cp /tmp/tpr_workflow_handler.py /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/
    chown ec2-user:ec2-user /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_workflow_handler.py
    chmod 755 /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_workflow_handler.py
    
    # Verify
    echo "Installed:"
    ls -lh /home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_workflow_handler.py
    
    # Restart service
    echo "Restarting service..."
    sudo systemctl restart chatmrpt
    sleep 5
    
    echo "Service status:"
    sudo systemctl is-active chatmrpt
    
    echo "✅ tpr_workflow_handler.py deployed to $PROD_IP"
INSTALL
done

echo ""
echo "=== Complete ==="

OUTER_EOF
