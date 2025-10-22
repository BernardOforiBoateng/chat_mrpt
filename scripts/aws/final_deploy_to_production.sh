#!/bin/bash

echo "=== Final Production Deployment ==="
echo "Using AWS SSM or direct IP approach"

# Check if we have the production IPs in our known hosts
PROD_IPS=(
    "3.137.158.17"  # Old production IP
    "172.31.44.52"  # New instance 1
    "172.31.43.200" # New instance 2
)

STAGING_IP="3.21.167.170"

echo "Step 1: Package all files from staging"
ssh -i /tmp/chatmrpt-key2.pem ec2-user@${STAGING_IP} << 'PACKAGE_EOF'
    cd /home/ec2-user
    echo "Creating full backup of ChatMRPT..."
    tar -czf ChatMRPT_full_$(date +%Y%m%d_%H%M%S).tar.gz ChatMRPT/ \
        --exclude='ChatMRPT/instance/uploads/*/*' \
        --exclude='ChatMRPT/instance/*.db' \
        --exclude='ChatMRPT/venv' \
        --exclude='ChatMRPT/__pycache__' \
        --exclude='ChatMRPT/.git'
    
    ls -lh ChatMRPT_full_*.tar.gz | tail -1
    echo "✅ Backup created on staging"
PACKAGE_EOF

echo ""
echo "Step 2: Copy staging backup to local"
LATEST_BACKUP=$(ssh -i /tmp/chatmrpt-key2.pem ec2-user@${STAGING_IP} "ls -t ChatMRPT_full_*.tar.gz 2>/dev/null | head -1")
if [ ! -z "$LATEST_BACKUP" ]; then
    scp -i /tmp/chatmrpt-key2.pem ec2-user@${STAGING_IP}:${LATEST_BACKUP} /tmp/
    echo "✅ Backup copied to /tmp/${LATEST_BACKUP}"
fi

echo ""
echo "Step 3: Try to reach production instances"

# Try the old production IP first
echo "Trying old production IP: 3.137.158.17"
if timeout 3 nc -zv 3.137.158.17 22 2>&1 | grep -q succeeded; then
    echo "✅ Can reach 3.137.158.17!"
    
    # Deploy to old production
    scp -i /tmp/chatmrpt-key2.pem /tmp/ChatMRPT_full_*.tar.gz ec2-user@3.137.158.17:/tmp/ 2>/dev/null || true
    
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'DEPLOY_EOF' 2>/dev/null || true
        cd /home/ec2-user
        if [ -f /tmp/ChatMRPT_full_*.tar.gz ]; then
            echo "Extracting files..."
            tar -xzf /tmp/ChatMRPT_full_*.tar.gz
            sudo systemctl restart chatmrpt
            echo "✅ Deployed to 3.137.158.17"
        fi
DEPLOY_EOF
else
    echo "❌ Cannot reach 3.137.158.17"
fi

echo ""
echo "Step 4: Test production endpoints"
echo "Testing ALB..."
curl -s -o /dev/null -w "ALB Status: %{http_code}\n" http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/ping

echo ""
echo "If deployment didn't work, you need to:"
echo "1. Use AWS Console -> EC2"
echo "2. Find instances: i-06d3edfcc85a1f1c7 and i-0183aaf795bf8f24e"
echo "3. Use 'Connect' -> 'Session Manager'"
echo "4. Run on each instance:"
echo "   cd /home/ec2-user"
echo "   wget http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/backup.tar.gz"
echo "   tar -xzf backup.tar.gz"
echo "   sudo systemctl restart chatmrpt"

