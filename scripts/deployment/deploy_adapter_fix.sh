#!/bin/bash
# Deploy LLMAdapter fix to enable vision explanations

echo "🚀 Deploying LLMAdapter Vision Fix..."

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

# Function to deploy to instance
deploy_fix() {
    local INSTANCE_IP=$1
    local INSTANCE_NAME=$2

    echo ""
    echo "🔧 Deploying to $INSTANCE_NAME ($INSTANCE_IP)..."

    # Copy the fixed files
    echo "  - Copying llm_adapter.py..."
    scp -i "$KEY" app/core/llm_adapter.py "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/core/"

    # Restart service and test
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
cd /home/ec2-user/ChatMRPT

echo "  - Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

echo "  - Restarting service..."
sudo systemctl restart chatmrpt
sleep 5

echo "  - Verifying fix..."
source /home/ec2-user/chatmrpt_env/bin/activate
python3 << 'PYTEST'
import sys
sys.path.insert(0, '/home/ec2-user/ChatMRPT')

# Test LLMAdapter has the method
from app.core.llm_adapter import LLMAdapter
print(f"LLMAdapter has generate_with_image: {hasattr(LLMAdapter, 'generate_with_image')}")

# Test the actual service container
from app.services.container import ServiceContainer
container = ServiceContainer()
llm = container.llm_manager
print(f"Service LLM has generate_with_image: {hasattr(llm, 'generate_with_image')}")

if hasattr(llm, 'generate_with_image'):
    print("✅ Vision method is available in service container!")
else:
    print("❌ Vision method NOT available in service container")
PYTEST

echo "  - Service status:"
sudo systemctl status chatmrpt | grep Active
EOF

    echo "✅ Done for $INSTANCE_NAME"
}

# Deploy to both instances
deploy_fix "$INSTANCE1" "Instance 1"
deploy_fix "$INSTANCE2" "Instance 2"

echo ""
echo "🎉 LLMAdapter fix deployed!"
echo ""
echo "📝 Testing instructions:"
echo "1. Clear browser cache (Ctrl+Shift+R)"
echo "2. Go to: https://d225ar6c86586s.cloudfront.net"
echo "3. Generate any visualization (TPR map, EVI map, etc.)"
echo "4. Click the '✨ Explain' button"
echo "5. You should now see REAL AI-powered explanations!"
echo ""
echo "If still seeing cached content, run:"
echo "  ./invalidate_cloudfront.sh"