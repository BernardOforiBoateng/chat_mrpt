#!/bin/bash
set -e

echo "=========================================="
echo "React Hotfix Deployment"
echo "Deploying updated React build"
echo "=========================================="

# Production instance IPs
INSTANCE1_IP="3.21.167.170"
INSTANCE2_IP="18.220.103.20"
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Ensure key exists
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem $KEY_PATH
    chmod 600 $KEY_PATH
fi

echo -e "\n1. Creating deployment package..."
cd app/static/react
tar -czf /tmp/react-hotfix.tar.gz .
cd ../../..

echo -e "\n2. Deploying to both instances..."
for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo -e "\nDeploying to $IP..."
    
    # Copy tarball
    scp -i $KEY_PATH /tmp/react-hotfix.tar.gz ec2-user@$IP:/tmp/
    
    # Deploy and update
    ssh -i $KEY_PATH ec2-user@$IP 'bash -s' << 'EOF'
    set -e
    cd /home/ec2-user/ChatMRPT
    
    # Update React files
    echo "Updating React files..."
    cd app/static/react
    sudo tar -xzf /tmp/react-hotfix.tar.gz
    cd ../../..
    
    # Update main index.html in templates
    echo "Updating templates/index.html..."
    sudo cp app/static/react/index.html app/templates/index.html
    
    # Fix paths in templates/index.html
    sudo sed -i 's|href="/assets/|href="/static/react/assets/|g' app/templates/index.html
    sudo sed -i 's|src="/assets/|src="/static/react/assets/|g' app/templates/index.html
    sudo sed -i 's|href="/vite.svg"|href="/static/react/vite.svg"|g' app/templates/index.html
    
    # Clean up
    rm /tmp/react-hotfix.tar.gz
    
    echo "✅ Hotfix deployed"
EOF
done

echo -e "\n3. Restarting services..."
for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    ssh -i $KEY_PATH ec2-user@$IP 'sudo systemctl restart chatmrpt'
done

echo -e "\n4. Testing deployment..."
sleep 5
for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo -e "\nTesting $IP..."
    if ssh -i $KEY_PATH ec2-user@$IP 'curl -s http://localhost:5000/ | grep -q "ChatMRPT - Malaria Risk Analysis"'; then
        echo "✅ Title fixed!"
    fi
    
    # Check service health
    ssh -i $KEY_PATH ec2-user@$IP 'curl -s http://localhost:5000/ping && echo " - API OK"'
done

# Clean up
rm -f /tmp/react-hotfix.tar.gz

echo -e "\n=========================================="
echo "✅ HOTFIX DEPLOYED!"
echo "=========================================="
echo "Test at:"
echo "- http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "Note: CloudFront may still show cached version"
echo "=========================================="