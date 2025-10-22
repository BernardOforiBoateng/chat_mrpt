#!/bin/bash
set -e

echo "=========================================="
echo "CRITICAL FIX: Remove Old Frontend Completely"
echo "Replace with React-Only Version"
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

echo -e "\n⚠️  FOUND THE ISSUE:"
echo "The OLD HTML template with OLD JavaScript (app.js) is still running!"
echo "This is creating the loading overlay on top of React."
echo ""

for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo -e "\n🔧 Fixing instance $IP..."
    ssh -i $KEY_PATH ec2-user@$IP 'bash -s' << 'EOF'
    set -e
    cd /home/ec2-user/ChatMRPT
    
    echo "1. Backing up old frontend files..."
    sudo mkdir -p old_frontend_backup_$(date +%Y%m%d_%H%M%S)
    sudo cp app/templates/index.html old_frontend_backup_$(date +%Y%m%d_%H%M%S)/index_old.html
    sudo cp -r app/static/js old_frontend_backup_$(date +%Y%m%d_%H%M%S)/ 2>/dev/null || true
    
    echo "2. Creating clean React-only index.html..."
    cat > /tmp/react_index.html << 'HTMLEOF'
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" type="image/svg+xml" href="/static/react/vite.svg" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>ChatMRPT - Malaria Risk Analysis</title>
    <script type="module" crossorigin src="/static/react/assets/index-CWTdV2HE.js"></script>
    <link rel="stylesheet" crossorigin href="/static/react/assets/index-tn0RQdqM.css">
  </head>
  <body>
    <div id="root"></div>
  </body>
</html>
HTMLEOF
    
    echo "3. Replacing index.html with React version..."
    sudo cp /tmp/react_index.html app/templates/index.html
    
    echo "4. Removing old JavaScript files to prevent conflicts..."
    sudo mv app/static/js app/static/js_old_backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true
    
    echo "5. Verifying changes..."
    echo "   - Checking new index.html:"
    if grep -q "index-CWTdV2HE.js" app/templates/index.html; then
        echo "     ✅ React JS loaded"
    fi
    if ! grep -q "app.js" app/templates/index.html; then
        echo "     ✅ Old app.js NOT loaded"
    fi
    
    # Clean up temp file
    rm /tmp/react_index.html
    
    echo "✅ Frontend fixed on $HOSTNAME"
EOF
done

echo -e "\n6. Restarting services..."
for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo "   Restarting $IP..."
    ssh -i $KEY_PATH ec2-user@$IP 'sudo systemctl restart chatmrpt'
done

echo -e "\n7. Verification..."
sleep 5
echo "Checking what's being served..."
curl -s http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/ | head -15

echo -e "\n=========================================="
echo "✅ OLD FRONTEND REMOVED - REACT ONLY!"
echo "=========================================="
echo "The old HTML/JS/CSS that was creating the overlay"
echo "has been completely removed."
echo ""
echo "Now serving ONLY the React application."
echo ""
echo "Test at:"
echo "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo "=========================================="