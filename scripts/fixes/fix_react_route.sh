#!/bin/bash
set -e

echo "=========================================="
echo "Fixing React Route Registration"
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

echo "Fixing route registration on both instances..."

for IP in $INSTANCE1_IP $INSTANCE2_IP; do
    echo -e "\nFixing instance $IP..."
    ssh -i $KEY_PATH ec2-user@$IP 'bash -s' << 'EOF'
    set -e
    cd /home/ec2-user/ChatMRPT
    
    # Remove the incorrect registration
    echo "Removing incorrect registration..."
    sudo sed -i '/# React Frontend/,/app.register_blueprint(react_bp)/d' app/web/routes/__init__.py
    
    # Update the __init__.py to properly register React route
    echo "Creating proper registration function..."
    cat > /tmp/fix_init.py << 'PYTHONEOF'
import sys
import os

# Read the current file
with open('app/web/routes/__init__.py', 'r') as f:
    lines = f.readlines()

# Find where to insert the React route registration
insert_index = -1
for i, line in enumerate(lines):
    if 'def register_all_routes(app):' in line:
        # Find the end of the function
        for j in range(i+1, len(lines)):
            if lines[j].strip() and not lines[j].startswith(' ') and not lines[j].startswith('\t'):
                insert_index = j - 1
                break
            if 'main_bp = core_bp' in lines[j]:
                insert_index = j + 1
                break
        break

if insert_index > 0:
    # Add React route registration
    new_lines = lines[:insert_index]
    new_lines.append('\n')
    new_lines.append('    # React Frontend\n')
    new_lines.append('    try:\n')
    new_lines.append('        from app.web.routes.react_route import react_bp\n')
    new_lines.append('        app.register_blueprint(react_bp)\n')
    new_lines.append('        logger.info("✅ React frontend routes registered")\n')
    new_lines.append('    except ImportError as e:\n')
    new_lines.append('        logger.warning(f"React routes not available: {e}")\n')
    new_lines.extend(lines[insert_index:])
    
    # Write back
    with open('app/web/routes/__init__.py', 'w') as f:
        f.writelines(new_lines)
    print("✅ Fixed __init__.py")
else:
    print("⚠️ Could not find insertion point")
PYTHONEOF
    
    sudo python3 /tmp/fix_init.py
    rm /tmp/fix_init.py
    
    echo "Restarting service..."
    sudo systemctl restart chatmrpt
    sleep 5
    
    echo "Checking service status..."
    if sudo systemctl is-active chatmrpt | grep -q active; then
        echo "✅ Service is running"
        
        # Test React route
        if curl -s http://localhost:5000/react | grep -q "<!doctype html>"; then
            echo "✅ React route is working!"
        else
            echo "⚠️ React route may not be accessible"
        fi
    else
        echo "❌ Service failed to start"
        sudo journalctl -u chatmrpt -n 20
    fi
EOF
done

echo -e "\n=========================================="
echo "✅ React route fix complete!"
echo "=========================================="