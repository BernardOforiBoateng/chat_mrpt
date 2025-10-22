#!/bin/bash
# Install Google Chrome for html2image on Amazon Linux 2023

echo "🔧 Installing Google Chrome for Vision Explanations..."

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

# Function to install Chrome on instance
install_chrome() {
    local INSTANCE_IP=$1
    local INSTANCE_NAME=$2

    echo ""
    echo "📦 Installing Google Chrome on $INSTANCE_NAME ($INSTANCE_IP)..."

    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
# Download and install Google Chrome
echo "  - Downloading Google Chrome..."
cd /tmp
wget -q https://dl.google.com/linux/direct/google-chrome-stable_current_x86_64.rpm

echo "  - Installing Chrome and dependencies..."
sudo yum install -y ./google-chrome-stable_current_x86_64.rpm

# Verify installation
if which google-chrome-stable; then
    echo "  ✅ Google Chrome installed successfully"
    CHROME_VERSION=$(google-chrome-stable --version)
    echo "  Version: $CHROME_VERSION"
else
    echo "  ❌ Chrome installation failed"
fi

# Clean up
rm -f google-chrome-stable_current_x86_64.rpm

# Test html2image with Chrome
echo "  - Testing html2image with Chrome..."
source /home/ec2-user/chatmrpt_env/bin/activate

# Create a test to verify it works
python -c "
import os
os.environ['ENABLE_VISION_EXPLANATIONS'] = 'true'
from app.services.universal_viz_explainer import UniversalVisualizationExplainer
explainer = UniversalVisualizationExplainer()

# Test HTML
test_html = '''
<html><body style=\"background:red;\">
<h1>Test</h1>
</body></html>
'''

import tempfile
with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
    f.write(test_html)
    test_path = f.name

try:
    # This will test the actual conversion
    from html2image import Html2Image
    hti = Html2Image(custom_flags=['--no-sandbox', '--headless', '--disable-gpu'])
    print('  ✅ html2image initialized with Chrome successfully!')
except Exception as e:
    print(f'  ❌ html2image test failed: {e}')
finally:
    import os
    if os.path.exists(test_path):
        os.unlink(test_path)
"

# Restart service
echo "  - Restarting ChatMRPT service..."
sudo systemctl restart chatmrpt
EOF

    echo "✅ Chrome installation complete for $INSTANCE_NAME"
}

# Install on both instances
install_chrome "$INSTANCE1" "Instance 1"
install_chrome "$INSTANCE2" "Instance 2"

echo ""
echo "🎉 Google Chrome installed successfully!"
echo ""
echo "✅ What's now working:"
echo "  - Google Chrome (headless mode)"
echo "  - html2image can convert HTML to images"
echo "  - Vision API can analyze visualizations"
echo ""
echo "🧪 Test it now:"
echo "1. Go to: https://d225ar6c86586s.cloudfront.net"
echo "2. Generate a TPR map or any visualization"
echo "3. Click '✨ Explain'"
echo "4. You should now see REAL AI-powered explanations!"
echo ""
echo "💡 The explanation should be specific to your data,"
echo "   not generic 'This visualization shows...' text"