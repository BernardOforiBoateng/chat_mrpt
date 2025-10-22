#!/bin/bash

# Rebuild frontend on both production instances to apply fullscreen fix

echo "========================================"
echo "🔨 Rebuilding Frontend on Production Instances"
echo "========================================"

# Set variables
KEY_PATH="/tmp/chatmrpt-key2.pem"
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"

# Copy key if needed
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

# Function to rebuild frontend on an instance
rebuild_frontend() {
    local ip=$1
    echo ""
    echo "📍 Rebuilding frontend on $ip..."
    
    # SSH and rebuild
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" << 'EOF'
        set -e
        echo "  Navigating to frontend directory..."
        cd /home/ec2-user/ChatMRPT/frontend
        
        # Check if package.json exists
        if [ ! -f package.json ]; then
            echo "  ❌ No package.json found in frontend directory"
            # Try the React app location
            cd /home/ec2-user/ChatMRPT
            if [ -f package.json ]; then
                echo "  Found package.json in main directory"
            else
                echo "  ❌ Could not find package.json"
                exit 1
            fi
        fi
        
        echo "  Installing dependencies..."
        npm install --production 2>&1 | tail -5
        
        echo "  Building frontend (this may take a minute)..."
        npm run build 2>&1 | tail -10
        
        if [ $? -eq 0 ]; then
            echo "  ✅ Frontend built successfully"
            
            # Check if build output exists
            if [ -d "dist" ]; then
                echo "  Build output found in dist/"
                # Copy to static directory if needed
                if [ -d "../app/static" ]; then
                    echo "  Copying build to app/static..."
                    cp -r dist/* ../app/static/ 2>/dev/null || true
                fi
            elif [ -d "build" ]; then
                echo "  Build output found in build/"
                # Copy to static directory if needed
                if [ -d "../app/static" ]; then
                    echo "  Copying build to app/static..."
                    cp -r build/* ../app/static/ 2>/dev/null || true
                fi
            fi
        else
            echo "  ❌ Frontend build failed"
            exit 1
        fi
        
        # Restart the service
        echo "  Restarting ChatMRPT service..."
        sudo systemctl restart chatmrpt
        
        if [ $? -eq 0 ]; then
            echo "  ✅ Service restarted successfully"
        else
            echo "  ❌ Failed to restart service"
        fi
        
        echo "  Checking service status..."
        sudo systemctl status chatmrpt --no-pager | head -10
EOF
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully rebuilt frontend on $ip"
    else
        echo "❌ Failed to rebuild frontend on $ip"
    fi
}

# Rebuild on both instances
for ip in "$INSTANCE_1" "$INSTANCE_2"; do
    rebuild_frontend "$ip"
done

echo ""
echo "========================================"
echo "✅ Frontend Rebuild Complete!"
echo "========================================"
echo ""
echo "📋 Next Steps:"
echo "  1. Wait 2-3 minutes for CloudFront cache to refresh"
echo "  2. Clear your browser cache (Ctrl+Shift+R)"
echo "  3. Run: python3 test_fullscreen_fix.py"
echo "  4. Test manually at https://d225ar6c86586s.cloudfront.net"
echo ""
echo "🧪 Manual Testing:"
echo "  - Create multiple visualizations"
echo "  - Click fullscreen on 2nd or 3rd visualization"
echo "  - Verify correct visualization goes fullscreen"
echo ""