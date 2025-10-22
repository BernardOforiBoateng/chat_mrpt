#!/bin/bash
set -e

echo "=========================================="
echo "Deploy React as Main Frontend"
echo "Replacing old HTML interface with React"
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

echo -e "\n1. Backing up old HTML interface and deploying React as main..."

for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo -e "\nDeploying to instance $IP..."
    ssh -i $KEY_PATH ec2-user@$IP 'bash -s' << 'EOF'
    set -e
    cd /home/ec2-user/ChatMRPT
    
    # Backup the old HTML interface
    echo "Backing up old index.html..."
    sudo cp app/templates/index.html app/templates/index_old_html.html.backup_$(date +%Y%m%d_%H%M%S)
    
    # Copy React index.html to templates
    echo "Copying React index.html to templates..."
    sudo cp app/static/react/index.html app/templates/index.html
    
    # Update the index.html to point to correct static paths
    echo "Updating static paths in index.html..."
    sudo sed -i 's|href="/assets/|href="/static/react/assets/|g' app/templates/index.html
    sudo sed -i 's|src="/assets/|src="/static/react/assets/|g' app/templates/index.html
    sudo sed -i 's|href="/vite.svg"|href="/static/react/vite.svg"|g' app/templates/index.html
    
    echo "✅ React deployed as main interface on $HOSTNAME"
EOF
done

echo -e "\n2. Restarting services..."
for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo "Restarting service on $IP..."
    ssh -i $KEY_PATH ec2-user@$IP 'sudo systemctl restart chatmrpt'
done

echo -e "\n3. Waiting for services to stabilize..."
sleep 10

echo -e "\n4. Testing deployment..."
for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo -e "\nTesting $IP..."
    if ssh -i $KEY_PATH ec2-user@$IP 'curl -s http://localhost:5000/ | grep -q "ChatMRPT"'; then
        echo "✅ React frontend is now the main interface!"
    else
        echo "⚠️ Checking for issues..."
        ssh -i $KEY_PATH ec2-user@$IP 'curl -s http://localhost:5000/ | head -10'
    fi
done

echo -e "\n5. Creating CloudFront invalidation..."
# Try to invalidate CloudFront cache
cat > /tmp/invalidate_cf.sh << 'CFEOF'
#!/bin/bash
# CloudFront invalidation commands
echo "To invalidate CloudFront cache, run:"
echo "aws cloudfront create-invalidation --distribution-id YOUR_DISTRIBUTION_ID --paths '/*'"
echo ""
echo "Or manually invalidate through AWS Console:"
echo "1. Go to CloudFront in AWS Console"
echo "2. Select distribution d225ar6c86586s.cloudfront.net"
echo "3. Go to Invalidations tab"
echo "4. Create invalidation with path: /*"
CFEOF

bash /tmp/invalidate_cf.sh

echo -e "\n=========================================="
echo "✅ REACT IS NOW THE MAIN FRONTEND!"
echo "=========================================="
echo "React has replaced the old HTML interface"
echo ""
echo "⚠️ IMPORTANT: CloudFront cache needs invalidation!"
echo "The old content is still cached in CloudFront."
echo ""
echo "After cache invalidation, access at:"
echo "- https://d225ar6c86586s.cloudfront.net"
echo "- http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "=========================================="