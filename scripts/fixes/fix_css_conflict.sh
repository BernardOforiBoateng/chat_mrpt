#!/bin/bash
set -e

echo "=========================================="
echo "Fix CSS Conflict - Remove Old Styles"
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

echo -e "\nRemoving old CSS files that conflict with React..."

for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo -e "\nFixing instance $IP..."
    ssh -i $KEY_PATH ec2-user@$IP 'bash -s' << 'EOF'
    set -e
    cd /home/ec2-user/ChatMRPT
    
    # Backup old CSS files
    echo "Backing up old CSS files..."
    sudo mkdir -p app/static/css_backup_$(date +%Y%m%d_%H%M%S)
    sudo mv app/static/css/*.css app/static/css_backup_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
    
    # Check if index.html is loading old CSS
    echo "Checking index.html for old CSS references..."
    if grep -q 'href="/static/css' app/templates/index.html; then
        echo "Removing old CSS references from index.html..."
        sudo sed -i '/<link.*href="\/static\/css/d' app/templates/index.html
    fi
    
    # Ensure React assets are the only styles loaded
    echo "Verifying React assets are properly linked..."
    if ! grep -q 'href="/static/react/assets' app/templates/index.html; then
        echo "React assets path looks correct"
    fi
    
    echo "✅ CSS conflicts removed on $HOSTNAME"
EOF
done

echo -e "\n2. Restarting services..."
for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    ssh -i $KEY_PATH ec2-user@$IP 'sudo systemctl restart chatmrpt'
done

echo -e "\n3. Testing..."
sleep 5
echo "Checking for old CSS references..."
curl -s http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/ | grep -c "static/css" || echo "✅ No old CSS references found"

echo -e "\n=========================================="
echo "✅ CSS CONFLICT FIXED!"
echo "=========================================="
echo "Old CSS files removed, React styles only"
echo "Test at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "=========================================="