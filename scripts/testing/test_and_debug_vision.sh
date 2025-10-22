#!/bin/bash
# Comprehensive vision test with debugging

echo "🔬 Comprehensive Vision Test with Debugging..."

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

# Function to deploy and test
deploy_and_test() {
    local INSTANCE_IP=$1
    local INSTANCE_NAME=$2

    echo ""
    echo "🚀 Deploying to $INSTANCE_NAME ($INSTANCE_IP)..."

    # Copy all fixed files
    echo "  - Copying debugged universal_viz_explainer.py..."
    scp -i "$KEY" app/services/universal_viz_explainer.py "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/services/"

    echo "  - Copying container.py..."
    scp -i "$KEY" app/services/container.py "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/services/"

    echo "  - Copying llm_adapter.py..."
    scp -i "$KEY" app/core/llm_adapter.py "ec2-user@$INSTANCE_IP:/home/ec2-user/ChatMRPT/app/core/"

    # Create test script
    cat > test_vision_debug.py << 'TESTSCRIPT'
#!/usr/bin/env python3
"""Comprehensive vision test with debugging"""

import os
import sys
import tempfile
import logging

# Setup detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s [%(name)s] %(message)s'
)

# Setup environment
sys.path.insert(0, '/home/ec2-user/ChatMRPT')
os.environ['ENABLE_VISION_EXPLANATIONS'] = 'true'

# Load API key
with open('/home/ec2-user/ChatMRPT/.env', 'r') as f:
    for line in f:
        if line.startswith('OPENAI_API_KEY='):
            os.environ['OPENAI_API_KEY'] = line.strip().split('=')[1]
            break

print("="*70)
print("COMPREHENSIVE VISION TEST WITH DEBUGGING")
print("="*70)

# Test HTML
test_html = """
<!DOCTYPE html>
<html>
<head><title>Test Malaria Map</title></head>
<body style="background:linear-gradient(to right, red, yellow, green); width:800px; height:600px;">
    <h1>Malaria Risk Map - Test</h1>
    <div style="background:#ff0000; padding:10px; margin:10px; color:white;">Region X: 92% TPR (URGENT)</div>
    <div style="background:#ffaa00; padding:10px; margin:10px;">Region Y: 67% TPR (HIGH)</div>
    <div style="background:#00ff00; padding:10px; margin:10px;">Region Z: 15% TPR (LOW)</div>
</body>
</html>
"""

# Save test HTML
with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
    f.write(test_html)
    test_path = f.name

try:
    print("\n" + "="*70)
    print("TEST 1: Direct Service Test")
    print("="*70)

    from app.services.universal_viz_explainer import UniversalVisualizationExplainer
    from app.core.llm_adapter import LLMAdapter

    # Create LLM adapter
    print("\n1. Creating LLMAdapter...")
    adapter = LLMAdapter(backend='openai', api_key=os.environ.get('OPENAI_API_KEY'))
    print(f"   ✓ LLMAdapter created")
    print(f"   ✓ Backend: {adapter.backend}")
    print(f"   ✓ Has generate_with_image: {hasattr(adapter, 'generate_with_image')}")

    # Create explainer
    print("\n2. Creating UniversalVisualizationExplainer...")
    explainer = UniversalVisualizationExplainer(llm_manager=adapter)
    print(f"   ✓ Explainer created")

    # Test explanation
    print("\n3. Calling explain_visualization...")
    print(f"   Input file: {test_path}")
    explanation = explainer.explain_visualization(
        viz_path=test_path,
        viz_type='tpr_map',
        session_id='test_debug_001'
    )

    print("\n4. Direct Test Results:")
    print("-"*70)

    # Check for specific content from our test
    test_indicators = ["92%", "Region X", "URGENT", "67%", "Region Y"]
    found_indicators = [ind for ind in test_indicators if ind in explanation]

    if found_indicators:
        print(f"✅ SUCCESS: Found test data in explanation: {found_indicators}")
        print("   Vision API is working correctly!")
    else:
        # Check for fallback
        if "This visualization shows malaria risk analysis" in explanation:
            print("❌ FALLBACK: Still getting generic explanation")
        else:
            print("⚠️  PARTIAL: Got AI response but no specific data")

    print(f"\nExplanation preview (first 400 chars):")
    print(explanation[:400])

    print("\n" + "="*70)
    print("TEST 2: Flask Route Test")
    print("="*70)

    from app import create_app
    app = create_app()

    with app.test_client() as client:
        # Set up session
        with client.session_transaction() as sess:
            sess['session_id'] = 'test_flask_debug'

        print("\n1. Testing /explain_visualization endpoint...")

        # Call endpoint
        response = client.post('/explain_visualization',
            json={
                'visualization_path': test_path,
                'viz_type': 'tpr_map',
                'title': 'Test Map'
            }
        )

        print(f"   Response status: {response.status_code}")

        if response.status_code == 200:
            data = response.json
            if data.get('status') == 'success':
                flask_explanation = data.get('explanation', '')

                # Check for test indicators
                flask_found = [ind for ind in test_indicators if ind in flask_explanation]

                if flask_found:
                    print(f"   ✅ Flask SUCCESS: Found indicators: {flask_found}")
                elif "This visualization shows malaria risk analysis" in flask_explanation:
                    print(f"   ❌ Flask FALLBACK: Generic explanation")
                else:
                    print(f"   ⚠️ Flask PARTIAL: AI response but no specific data")

                print(f"\n   Flask explanation preview:")
                print(f"   {flask_explanation[:300]}...")
            else:
                print(f"   ❌ Flask error: {data.get('message')}")
        else:
            print(f"   ❌ HTTP error: {response.status_code}")

    print("\n" + "="*70)
    print("TEST 3: Services Container Test")
    print("="*70)

    with app.app_context():
        print("\n1. Getting LLM from services container...")
        llm = app.services.llm_manager
        print(f"   Type: {type(llm).__name__}")
        print(f"   Has generate_with_image: {hasattr(llm, 'generate_with_image')}")

        if hasattr(llm, 'adapter'):
            print(f"   Adapter type: {type(llm.adapter).__name__}")
            print(f"   Adapter has method: {hasattr(llm.adapter, 'generate_with_image')}")

except Exception as e:
    import traceback
    print(f"\n❌ ERROR: {e}")
    traceback.print_exc()

finally:
    # Clean up
    if os.path.exists(test_path):
        os.unlink(test_path)

print("\n" + "="*70)
print("SUMMARY")
print("="*70)
print("Check the DEBUG log messages above to see:")
print("1. What type of LLM manager is being used")
print("2. Whether generate_with_image is available")
print("3. If image capture is successful")
print("4. What the vision API returns")
TESTSCRIPT

    # Copy and run test
    echo ""
    echo "🧪 Running comprehensive test on $INSTANCE_NAME..."
    scp -i "$KEY" test_vision_debug.py "ec2-user@$INSTANCE_IP:/tmp/"

    ssh -i "$KEY" "ec2-user@$INSTANCE_IP" << 'EOF'
cd /home/ec2-user/ChatMRPT

# Clear cache and restart
echo "  - Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

echo "  - Restarting service..."
sudo systemctl restart chatmrpt
sleep 7

echo "  - Running test..."
source /home/ec2-user/chatmrpt_env/bin/activate
python /tmp/test_vision_debug.py 2>&1 | tee /tmp/vision_test_output.log

echo ""
echo "  - Checking service logs for DEBUG messages..."
sudo journalctl -u chatmrpt -n 50 | grep -E "DEBUG:|VISION|generate_with_image" | tail -20

rm -f /tmp/test_vision_debug.py
EOF

    echo "✅ Done testing $INSTANCE_NAME"
}

# Test on Instance 1 first
deploy_and_test "$INSTANCE1" "Instance 1"

# Clean up
rm -f test_vision_debug.py

echo ""
echo "📊 Test Complete!"
echo ""
echo "Look for these indicators of success:"
echo "✅ 'Found test data in explanation' - Vision is working"
echo "❌ 'FALLBACK: Still getting generic' - Vision not working"
echo ""
echo "Check the DEBUG messages to see exactly what's happening!"