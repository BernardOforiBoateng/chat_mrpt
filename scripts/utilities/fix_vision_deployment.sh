#!/bin/bash
# Fix vision explanations by ensuring generate_with_image method is available

echo "🔧 Fixing Vision Explanations on AWS..."

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

# Function to fix vision on instance
fix_vision() {
    local INSTANCE_IP=$1
    local INSTANCE_NAME=$2

    echo ""
    echo "🔧 Fixing vision on $INSTANCE_NAME ($INSTANCE_IP)..."

    # Copy the correct llm_manager.py
    echo "  - Copying llm_manager.py..."
    scp -i "$KEY" app/core/llm_manager.py "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/core/"

    # SSH and fix
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
cd /home/ec2-user/ChatMRPT

echo "  - Stopping service..."
sudo systemctl stop chatmrpt

echo "  - Clearing all Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

echo "  - Verifying generate_with_image method exists..."
if grep -q "def generate_with_image" app/core/llm_manager.py; then
    echo "  ✅ Method found in file"
    LINE=$(grep -n "def generate_with_image" app/core/llm_manager.py | cut -d: -f1)
    echo "  At line: $LINE"
else
    echo "  ❌ Method NOT found in file!"
fi

echo "  - Starting service fresh..."
sudo systemctl start chatmrpt
sleep 5

echo "  - Testing with Python directly..."
source /home/ec2-user/chatmrpt_env/bin/activate
python3 << 'PYTEST'
import sys
import os
sys.path.insert(0, '/home/ec2-user/ChatMRPT')
os.environ['ENABLE_VISION_EXPLANATIONS'] = 'true'

# Force reload the module
import importlib
if 'app.core.llm_manager' in sys.modules:
    del sys.modules['app.core.llm_manager']

from app.core.llm_manager import LLMManager

# Test
print(f"LLMManager methods: {[m for m in dir(LLMManager) if not m.startswith('_')]}")
print(f"Has generate_with_image: {hasattr(LLMManager, 'generate_with_image')}")

if hasattr(LLMManager, 'generate_with_image'):
    print("✅ Method is available!")
    # Try to instantiate
    try:
        manager = LLMManager()
        if hasattr(manager, 'generate_with_image'):
            print("✅ Instance also has the method!")
        else:
            print("❌ Instance doesn't have the method")
    except Exception as e:
        print(f"Error creating instance: {e}")
else:
    print("❌ Method not found in class")
PYTEST

echo "  - Service status:"
sudo systemctl status chatmrpt | grep Active
EOF

    echo "✅ Done for $INSTANCE_NAME"
}

# Fix both instances
fix_vision "$INSTANCE1" "Instance 1"
fix_vision "$INSTANCE2" "Instance 2"

echo ""
echo "🎉 Vision fix deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Test at: https://d225ar6c86586s.cloudfront.net"
echo "2. Generate a TPR map"
echo "3. Click '✨ Explain'"
echo "4. Should see real AI explanations now"