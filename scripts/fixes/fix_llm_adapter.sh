#!/bin/bash

echo "=== Fixing Missing llm_adapter Module ==="
echo ""

# Copy key
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Connect to staging and handle the file transfer
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 << 'OUTER_EOF'

echo "Getting llm_adapter.py from staging..."
scp -i ~/.ssh/chatmrpt-key.pem ec2-user@18.220.103.20:/home/ec2-user/ChatMRPT/app/core/llm_adapter.py /tmp/

echo "File size check:"
ls -lh /tmp/llm_adapter.py

# Deploy to both production instances
for PROD_IP in 172.31.44.52 172.31.43.200; do
    echo ""
    echo "Deploying llm_adapter to: $PROD_IP"
    
    # Copy file to production
    scp -i ~/.ssh/chatmrpt-key.pem /tmp/llm_adapter.py ec2-user@$PROD_IP:/tmp/
    
    # Install on production
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP << 'INSTALL'
    # Copy to correct location
    cp /tmp/llm_adapter.py /home/ec2-user/ChatMRPT/app/core/
    chown ec2-user:ec2-user /home/ec2-user/ChatMRPT/app/core/llm_adapter.py
    chmod 755 /home/ec2-user/ChatMRPT/app/core/llm_adapter.py
    
    # Verify
    echo "Installed:"
    ls -lh /home/ec2-user/ChatMRPT/app/core/llm_adapter.py
    
    # Restart service
    echo "Restarting service..."
    sudo systemctl restart chatmrpt
    sleep 5
    
    echo "Service status:"
    sudo systemctl is-active chatmrpt
    
    # Check for startup errors
    echo "Recent logs:"
    sudo journalctl -u chatmrpt --since "30 seconds ago" | grep -E "LLM|llm_adapter|Pure LLM Manager initialized" | tail -5
    
    echo "✅ llm_adapter.py deployed to $PROD_IP"
INSTALL
done

echo ""
echo "=== Complete ==="
echo "The llm_adapter module has been deployed to production"

OUTER_EOF
