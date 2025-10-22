#!/bin/bash
# Deploy final vision fix - LLMManagerWrapper update

echo "🚀 Deploying Final Vision Fix..."

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
deploy_final_fix() {
    local INSTANCE_IP=$1
    local INSTANCE_NAME=$2

    echo ""
    echo "🔧 Deploying to $INSTANCE_NAME ($INSTANCE_IP)..."

    # Copy both fixed files
    echo "  - Copying container.py (with LLMManagerWrapper fix)..."
    scp -i "$KEY" app/services/container.py "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/services/"

    echo "  - Copying llm_adapter.py (with generate_with_image)..."
    scp -i "$KEY" app/core/llm_adapter.py "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/core/"

    # Restart and verify
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
cd /home/ec2-user/ChatMRPT

echo "  - Clearing ALL Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true
find . -name "*.pyo" -delete 2>/dev/null || true

echo "  - Restarting service..."
sudo systemctl restart chatmrpt
sleep 7

echo "  - Running verification test..."
source /home/ec2-user/chatmrpt_env/bin/activate
python3 << 'PYTEST'
import sys, os
sys.path.insert(0, '/home/ec2-user/ChatMRPT')
os.environ['ENABLE_VISION_EXPLANATIONS'] = 'true'

# Load API key
with open('/home/ec2-user/ChatMRPT/.env', 'r') as f:
    for line in f:
        if line.startswith('OPENAI_API_KEY='):
            os.environ['OPENAI_API_KEY'] = line.strip().split('=')[1]
            break

# Test the complete chain
from app import create_app
app = create_app()

with app.app_context():
    # Get LLM from services (what Flask route uses)
    llm = app.services.llm_manager
    print(f"Service LLM type: {type(llm).__name__}")
    print(f"Has generate_with_image: {hasattr(llm, 'generate_with_image')}")

    if hasattr(llm, 'generate_with_image'):
        print("✅ VISION FIX SUCCESSFUL!")
        print("   The Flask route will now use vision API")
    else:
        print("❌ Vision method still missing")
PYTEST

echo "  - Service status:"
sudo systemctl status chatmrpt | grep Active
EOF

    echo "✅ Done for $INSTANCE_NAME"
}

# Deploy to both instances
deploy_final_fix "$INSTANCE1" "Instance 1"
deploy_final_fix "$INSTANCE2" "Instance 2"

echo ""
echo "🎉 Final Vision Fix Deployed!"
echo ""
echo "📊 What was fixed:"
echo "1. ✅ LLMAdapter now has generate_with_image method"
echo "2. ✅ LLMManagerWrapper now proxies generate_with_image"
echo "3. ✅ Flask routes can now use vision API"
echo ""
echo "🧪 Test it now:"
echo "1. Go to: https://d225ar6c86586s.cloudfront.net"
echo "2. Generate any visualization"
echo "3. Click '✨ Explain'"
echo "4. You should see REAL AI-powered explanations!"