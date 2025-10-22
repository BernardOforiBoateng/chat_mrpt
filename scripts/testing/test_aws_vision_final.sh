#!/bin/bash
# Final test of vision explanations on AWS

echo "🧪 Testing Vision Explanations on AWS..."

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

# Test script content
cat > test_vision_final.py << 'TESTSCRIPT'
#!/usr/bin/env python3
"""Final test of vision explanations"""

import os
import sys
import tempfile

# Add parent to path
sys.path.insert(0, '/home/ec2-user/ChatMRPT')

# Set environment
os.environ['ENABLE_VISION_EXPLANATIONS'] = 'true'
os.environ['FLASK_ENV'] = 'development'

# Get API key
with open('/home/ec2-user/ChatMRPT/.env', 'r') as f:
    for line in f:
        if line.startswith('OPENAI_API_KEY='):
            api_key = line.strip().split('=')[1]
            os.environ['OPENAI_API_KEY'] = api_key
            break

# Import after setting env
from app.services.universal_viz_explainer import UniversalVisualizationExplainer
from app.core.llm_manager import LLMManager

print("="*60)
print("VISION EXPLANATION TEST")
print("="*60)

# Test HTML
test_html = """
<!DOCTYPE html>
<html>
<head><title>TPR Distribution Map</title></head>
<body style="background:linear-gradient(to right, red, yellow, green); width:800px; height:600px; padding:20px;">
    <h1>Malaria Test Positivity Rate Map - Kano State</h1>
    <div style="background:#ff0000; padding:10px; margin:10px; color:white;">Dala Ward: 78% TPR (Critical)</div>
    <div style="background:#ffaa00; padding:10px; margin:10px;">Fagge Ward: 45% TPR (High)</div>
    <div style="background:#ffff00; padding:10px; margin:10px;">Kumbotso Ward: 32% TPR (Moderate)</div>
    <div style="background:#00ff00; padding:10px; margin:10px;">Gwale Ward: 5% TPR (Low)</div>
    <p>Data from December 2024 surveillance reports</p>
</body>
</html>
"""

# Create temp file
with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
    f.write(test_html)
    test_path = f.name

try:
    print("1. Testing LLMManager...")
    llm_manager = LLMManager(api_key=os.environ.get('OPENAI_API_KEY'))
    print(f"   ✓ LLMManager created")
    print(f"   ✓ Has generate_with_image: {hasattr(llm_manager, 'generate_with_image')}")

    print("\n2. Testing UniversalVisualizationExplainer...")
    explainer = UniversalVisualizationExplainer(llm_manager=llm_manager)
    print(f"   ✓ Explainer created with LLM manager")

    print("\n3. Explaining visualization...")
    explanation = explainer.explain_visualization(
        viz_path=test_path,
        viz_type='tpr_map',
        session_id='test_final_789'
    )

    print("\n4. RESULTS:")
    print("-"*60)

    # Check if it's a fallback
    fallback_phrases = [
        "This visualization shows malaria risk analysis",
        "Tpr Map Generated",
        "This TPR (Test Positivity Rate) map displays"
    ]

    is_fallback = any(phrase in explanation for phrase in fallback_phrases)

    if is_fallback:
        print("❌ FALLBACK EXPLANATION DETECTED")
        print("   Still getting generic text instead of AI analysis")
    else:
        print("✅ SUCCESS: DYNAMIC AI EXPLANATION!")
        print("   Vision API is working correctly")

    print("\nExplanation preview (first 500 chars):")
    print(explanation[:500])

    print("\nFull length:", len(explanation), "characters")

except Exception as e:
    import traceback
    print(f"\n❌ ERROR: {e}")
    traceback.print_exc()

finally:
    # Clean up
    if os.path.exists(test_path):
        os.unlink(test_path)

print("\n" + "="*60)
TESTSCRIPT

# Function to test on instance
test_instance() {
    local INSTANCE_IP=$1
    local INSTANCE_NAME=$2

    echo ""
    echo "🔬 Testing on $INSTANCE_NAME ($INSTANCE_IP)..."

    # Copy test script
    scp -i "$KEY" test_vision_final.py "ec2-user@$INSTANCE_IP:/tmp/"

    # Run test
    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
source /home/ec2-user/chatmrpt_env/bin/activate
cd /home/ec2-user/ChatMRPT
python /tmp/test_vision_final.py
rm -f /tmp/test_vision_final.py
EOF
}

# Test both instances
test_instance "$INSTANCE1" "Instance 1"
test_instance "$INSTANCE2" "Instance 2"

# Clean up local test script
rm -f test_vision_final.py

echo ""
echo "🎯 Test complete!"
echo ""
echo "If both instances show '✅ SUCCESS: DYNAMIC AI EXPLANATION!',"
echo "then vision explanations are working correctly!"
echo ""
echo "Next: Test in browser at https://d225ar6c86586s.cloudfront.net"