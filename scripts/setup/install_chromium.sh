#!/bin/bash
# Install Chromium browser for html2image

echo "🔧 Installing Chromium for Vision Explanations..."

# Production Instance IPs
INSTANCE1="3.21.167.170"
INSTANCE2="18.220.103.20"

# Key location
KEY="/tmp/chatmrpt-key2.pem"

# Copy key if not already there
if [ ! -f "$KEY" ]; then
    echo "📋 Copying SSH key..."
    cp aws_files/chatmrpt-key.pem "$KEY"
    chmod 600 "$KEY"
fi

# Function to install chromium on instance
install_chromium() {
    local INSTANCE_IP=$1
    local INSTANCE_NAME=$2

    echo ""
    echo "📦 Installing Chromium on $INSTANCE_NAME ($INSTANCE_IP)..."

    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
# Install Chromium and dependencies
echo "  - Installing Chromium browser..."
sudo yum install -y chromium

# Verify installation
which chromium-browser && echo "  ✅ Chromium installed" || echo "  ⚠️ Checking alternate names..."

# Check if it's installed as chromium (not chromium-browser)
which chromium && echo "  ✅ Chromium installed as 'chromium'" || echo "  ❌ Chromium not found"

# Install additional dependencies that might be needed
echo "  - Installing additional dependencies..."
sudo yum install -y \
    libX11 libXcomposite libXcursor libXdamage \
    libXext libXi libXtst libXrandr libXScrnSaver \
    libxcb libxkbcommon gtk3 at-spi2-atk

# Test html2image with Chrome
echo "  - Testing html2image with Chromium..."
source /home/ec2-user/chatmrpt_env/bin/activate
python -c "
from html2image import Html2Image
try:
    hti = Html2Image(browser_executable='/usr/bin/chromium')
    print('  ✅ html2image initialized successfully with Chromium')
except Exception as e:
    print(f'  ❌ html2image failed: {e}')
"

# Restart service
echo "  - Restarting ChatMRPT service..."
sudo systemctl restart chatmrpt
EOF

    echo "✅ Chromium installation complete for $INSTANCE_NAME"
}

# Install on both instances
install_chromium "$INSTANCE1" "Instance 1"
install_chromium "$INSTANCE2" "Instance 2"

echo ""
echo "🎉 Chromium installed on both instances!"
echo ""
echo "🧪 Test the vision explanations now:"
echo "1. Go to: https://d225ar6c86586s.cloudfront.net"
echo "2. Generate a visualization"
echo "3. Click '✨ Explain'"
echo "4. Should see REAL AI explanations!"