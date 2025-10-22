#!/bin/bash

echo "=== Copying Real tpr_utils.py from Staging ==="
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Copy the actual file from staging to production via proxy
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'EOF'

echo "Getting tpr_utils.py from staging..."
scp -i ~/.ssh/chatmrpt-key.pem ec2-user@18.220.103.20:/home/ec2-user/ChatMRPT/app/core/tpr_utils.py /tmp/

echo "File size check:"
ls -lh /tmp/tpr_utils.py

# Deploy to both production instances
for PROD_IP in 172.31.44.52 172.31.43.200; do
    echo ""
    echo "Deploying real tpr_utils to: $PROD_IP"
    
    # Copy file to production
    scp -i ~/.ssh/chatmrpt-key.pem /tmp/tpr_utils.py ec2-user@$PROD_IP:/tmp/
    
    # Install on production
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP << 'INSTALL'
    # Backup existing if any
    [ -f /home/ec2-user/ChatMRPT/app/core/tpr_utils.py ] && \
        cp /home/ec2-user/ChatMRPT/app/core/tpr_utils.py /home/ec2-user/ChatMRPT/app/core/tpr_utils.py.backup
    
    # Copy to correct location
    cp /tmp/tpr_utils.py /home/ec2-user/ChatMRPT/app/core/
    
    # Set permissions
    chown ec2-user:ec2-user /home/ec2-user/ChatMRPT/app/core/tpr_utils.py
    chmod 755 /home/ec2-user/ChatMRPT/app/core/tpr_utils.py
    
    # Verify
    echo "Installed:"
    ls -lh /home/ec2-user/ChatMRPT/app/core/tpr_utils.py
    
    # Restart service
    echo "Restarting service..."
    sudo systemctl restart chatmrpt
    sleep 5
    
    echo "Service status:"
    sudo systemctl is-active chatmrpt
    
    # Check for startup errors
    echo "Recent logs:"
    sudo journalctl -u chatmrpt --since "30 seconds ago" | grep -E "ERROR|tpr_utils" | tail -5
    
    echo "✅ Real tpr_utils.py deployed to $PROD_IP"
INSTALL
done

echo ""
echo "=== Complete ==="
echo "The actual tpr_utils.py from staging has been deployed to production"

EOF