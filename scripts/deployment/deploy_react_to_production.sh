#!/bin/bash
set -e

echo "=========================================="
echo "ChatMRPT React Frontend Deployment Script"
echo "Deploying React build to production instances"
echo "=========================================="

# Production instance IPs (from CLAUDE.md)
INSTANCE1_IP="3.21.167.170"
INSTANCE2_IP="18.220.103.20"
KEY_PATH="aws_files/chatmrpt-key.pem"

# Prepare the key
echo "Preparing SSH key..."
cp $KEY_PATH /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

echo -e "\n1. Creating deployment package..."
# Create a tarball of the React build
cd app/static/react
tar -czf /tmp/react-build.tar.gz .
cd ../../..

echo -e "\n2. Deploying to Production Instance 1 ($INSTANCE1_IP)..."
# Copy to instance 1
scp -i /tmp/chatmrpt-key2.pem /tmp/react-build.tar.gz ec2-user@$INSTANCE1_IP:/tmp/
ssh -i /tmp/chatmrpt-key2.pem ec2-user@$INSTANCE1_IP 'bash -s' << 'EOF'
set -e
cd /home/ec2-user/ChatMRPT

# Backup existing static files
echo "Creating backup of existing static files..."
if [ -d "app/static/react" ]; then
    sudo mv app/static/react app/static/react.backup_$(date +%Y%m%d_%H%M%S)
fi

# Create react directory and extract files
echo "Extracting React build..."
sudo mkdir -p app/static/react
cd app/static/react
sudo tar -xzf /tmp/react-build.tar.gz
sudo chown -R ec2-user:ec2-user .
cd ../../..

# Clean up
rm /tmp/react-build.tar.gz

echo "✅ React frontend deployed to Instance 1"
EOF

echo -e "\n3. Deploying to Production Instance 2 ($INSTANCE2_IP)..."
# Copy to instance 2
scp -i /tmp/chatmrpt-key2.pem /tmp/react-build.tar.gz ec2-user@$INSTANCE2_IP:/tmp/
ssh -i /tmp/chatmrpt-key2.pem ec2-user@$INSTANCE2_IP 'bash -s' << 'EOF'
set -e
cd /home/ec2-user/ChatMRPT

# Backup existing static files
echo "Creating backup of existing static files..."
if [ -d "app/static/react" ]; then
    sudo mv app/static/react app/static/react.backup_$(date +%Y%m%d_%H%M%S)
fi

# Create react directory and extract files
echo "Extracting React build..."
sudo mkdir -p app/static/react
cd app/static/react
sudo tar -xzf /tmp/react-build.tar.gz
sudo chown -R ec2-user:ec2-user .
cd ../../..

# Clean up
rm /tmp/react-build.tar.gz

echo "✅ React frontend deployed to Instance 2"
EOF

echo -e "\n4. Adding Flask route for React app..."
# Create the React route file
cat > /tmp/react_route.py << 'PYTHONEOF'
from flask import Blueprint, send_from_directory
import os

react_bp = Blueprint('react', __name__)

@react_bp.route('/react')
@react_bp.route('/react/<path:path>')
def serve_react(path='index.html'):
    """Serve the React application"""
    react_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'react')
    
    if path != "" and os.path.exists(os.path.join(react_dir, path)):
        return send_from_directory(react_dir, path)
    else:
        return send_from_directory(react_dir, 'index.html')
PYTHONEOF

# Deploy route to both instances
for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo "Deploying React route to $IP..."
    scp -i /tmp/chatmrpt-key2.pem /tmp/react_route.py ec2-user@$IP:/tmp/
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP 'bash -s' << 'EOF'
    set -e
    cd /home/ec2-user/ChatMRPT
    
    # Add React route
    sudo cp /tmp/react_route.py app/web/routes/react_route.py
    
    # Check if route is already registered
    if ! grep -q "from app.web.routes.react_route import react_bp" app/web/routes/__init__.py; then
        echo "Adding React route to __init__.py..."
        sudo bash -c "echo '' >> app/web/routes/__init__.py"
        sudo bash -c "echo '# React Frontend' >> app/web/routes/__init__.py"
        sudo bash -c "echo 'from app.web.routes.react_route import react_bp' >> app/web/routes/__init__.py"
        sudo bash -c "echo 'app.register_blueprint(react_bp)' >> app/web/routes/__init__.py"
    fi
    
    # Clean up
    rm /tmp/react_route.py
    
    echo "✅ React route configured"
EOF
done

echo -e "\n5. Restarting services on both instances..."
for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo "Restarting service on $IP..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP 'sudo systemctl restart chatmrpt'
done

echo -e "\n6. Verifying deployment..."
sleep 5
for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo -e "\nChecking $IP..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP 'bash -s' << 'EOF'
    # Check service health
    curl -s http://localhost:5000/ping && echo " - Main app OK"
    
    # Check React route
    if curl -s http://localhost:5000/react | grep -q "ChatMRPT"; then
        echo " - React frontend accessible at /react"
    else
        echo " - Warning: React frontend may not be accessible"
    fi
    
    # Check for errors
    sudo journalctl -u chatmrpt -n 10 | grep -i error || echo " - No errors in logs"
EOF
done

# Clean up temp files
rm -f /tmp/react-build.tar.gz /tmp/react_route.py /tmp/chatmrpt-key2.pem

echo -e "\n=========================================="
echo "✅ REACT FRONTEND DEPLOYMENT COMPLETE!"
echo "=========================================="
echo "Both production instances now have:"
echo "- React frontend in app/static/react/"
echo "- Route available at /react"
echo ""
echo "Access the React frontend at:"
echo "- https://d225ar6c86586s.cloudfront.net/react"
echo "=========================================="