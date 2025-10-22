#!/bin/bash
# Install image conversion dependencies for vision explanations

echo "🔧 Installing Vision Explanation Dependencies..."

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

# Function to install deps on an instance
install_on_instance() {
    local INSTANCE_IP=$1
    local INSTANCE_NAME=$2

    echo ""
    echo "📦 Installing on $INSTANCE_NAME ($INSTANCE_IP)..."

    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
# Update packages
echo "  - Updating package lists..."
sudo yum update -y

# Install wkhtmltopdf (includes wkhtmltoimage)
echo "  - Installing wkhtmltopdf/wkhtmltoimage..."
sudo yum install -y wkhtmltopdf

# Verify installation
which wkhtmltoimage && echo "  ✅ wkhtmltoimage installed" || echo "  ❌ wkhtmltoimage failed"

# Install Python packages in virtual environment
echo "  - Installing Python packages..."
source /home/ec2-user/chatmrpt_env/bin/activate
pip install html2image

# Alternative: Install playwright (heavier but more reliable)
# pip install playwright
# playwright install chromium

echo "  - Verifying installation..."
python -c "from html2image import Html2Image; print('  ✅ html2image imported successfully')" || echo "  ❌ html2image import failed"

# Clear any cached explanations to force regeneration
echo "  - Clearing explanation cache..."
rm -rf /home/ec2-user/ChatMRPT/instance/cache/explanations/*

echo "  - Restarting service..."
sudo systemctl restart chatmrpt
EOF

    echo "✅ Installation complete for $INSTANCE_NAME"
}

# Install on both instances
install_on_instance "$INSTANCE1" "Instance 1"
install_on_instance "$INSTANCE2" "Instance 2"

echo ""
echo "🎉 Vision dependencies installed!"
echo ""
echo "✅ What was installed:"
echo "  - wkhtmltoimage (system package)"
echo "  - html2image (Python package)"
echo ""
echo "🧪 To verify it's working:"
echo "1. Go to: https://d225ar6c86586s.cloudfront.net"
echo "2. Generate a visualization"
echo "3. Click '✨ Explain'"
echo "4. Should now see REAL AI-powered explanations!"
echo ""
echo "💡 Note: Cleared explanation cache to force new generation"