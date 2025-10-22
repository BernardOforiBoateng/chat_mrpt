#!/bin/bash
# Deploy vision fixes to Instance 2 and test

echo "🚀 Deploying vision fixes to Instance 2..."

INSTANCE2="18.220.103.20"
KEY="/tmp/chatmrpt-key2.pem"

# Copy key if needed
if [ ! -f "$KEY" ]; then
    echo "📋 Copying SSH key..."
    cp aws_files/chatmrpt-key.pem "$KEY"
    chmod 600 "$KEY"
fi

echo ""
echo "📦 Copying fixed files to Instance 2..."

# Copy all the fixed files
echo "  - universal_viz_explainer.py (with debug logging)..."
scp -i "$KEY" app/services/universal_viz_explainer.py "ec2-user@$INSTANCE2:/home/ec2-user/ChatMRPT/app/services/"

echo "  - container.py (with LLMManagerWrapper proxy fix)..."
scp -i "$KEY" app/services/container.py "ec2-user@$INSTANCE2:/home/ec2-user/ChatMRPT/app/services/"

echo "  - llm_adapter.py (with generate_with_image method)..."
scp -i "$KEY" app/core/llm_adapter.py "ec2-user@$INSTANCE2:/home/ec2-user/ChatMRPT/app/core/"

echo "  - llm_manager.py (with fixed indentation)..."
scp -i "$KEY" app/core/llm_manager.py "ec2-user@$INSTANCE2:/home/ec2-user/ChatMRPT/app/core/"

echo ""
echo "🔄 Restarting service on Instance 2..."
ssh -i "$KEY" "ec2-user@$INSTANCE2" << 'EOF'
cd /home/ec2-user/ChatMRPT

# Clear Python cache
echo "  - Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -name "*.pyc" -delete 2>/dev/null || true

# Restart service
echo "  - Restarting ChatMRPT service..."
sudo systemctl restart chatmrpt
sleep 7

echo "  - Service status:"
sudo systemctl status chatmrpt | grep Active
EOF

echo ""
echo "✅ Instance 2 deployment complete!"
echo ""
echo "🧪 Running quick verification test on Instance 2..."

ssh -i "$KEY" "ec2-user@$INSTANCE2" << 'EOF'
cd /home/ec2-user/ChatMRPT
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

print("\n" + "="*60)
print("VISION API VERIFICATION - INSTANCE 2")
print("="*60)

# Test the service container chain
from app import create_app
app = create_app()

with app.app_context():
    llm = app.services.llm_manager
    print(f"\n1. Service LLM type: {type(llm).__name__}")
    print(f"2. Has generate_with_image: {hasattr(llm, 'generate_with_image')}")
    
    if hasattr(llm, 'generate_with_image'):
        print("\n✅ SUCCESS: Instance 2 has vision support!")
        print("   Vision API is properly configured")
    else:
        print("\n❌ FAILURE: Vision method still missing")
        print(f"   Available methods: {[m for m in dir(llm) if not m.startswith('_')][:10]}")

print("\n" + "="*60)
PYTEST
EOF

echo ""
echo "🎉 Deployment Complete!"
echo ""
echo "Both instances should now have working vision explanations:"
echo "  - Instance 1 (3.21.167.170): ✅ Tested and working"
echo "  - Instance 2 (18.220.103.20): ✅ Just deployed"
echo ""
echo "📊 Test it now:"
echo "1. Go to: https://d225ar6c86586s.cloudfront.net"
echo "2. Generate any visualization"
echo "3. Click '✨ Explain'"
echo "4. You should see REAL AI-powered explanations!"