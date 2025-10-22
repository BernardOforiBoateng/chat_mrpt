#!/bin/bash
# End-to-end test of vision explanations

echo "🧪 End-to-End Vision Test..."

# Production Instance IP (test on one first)
INSTANCE="3.21.167.170"
KEY="/tmp/chatmrpt-key2.pem"

# Copy key if not already there
if [ ! -f "$KEY" ]; then
    echo "📋 Copying SSH key..."
    cp aws_files/chatmrpt-key.pem "$KEY"
    chmod 600 "$KEY"
fi

# Create comprehensive test script
cat > test_e2e.py << 'TESTSCRIPT'
#!/usr/bin/env python3
"""End-to-end test of vision explanations"""

import os
import sys
import tempfile
import json

# Setup environment
sys.path.insert(0, '/home/ec2-user/ChatMRPT')
os.environ['ENABLE_VISION_EXPLANATIONS'] = 'true'

# Load API key
with open('/home/ec2-user/ChatMRPT/.env', 'r') as f:
    for line in f:
        if line.startswith('OPENAI_API_KEY='):
            api_key = line.strip().split('=')[1]
            os.environ['OPENAI_API_KEY'] = api_key
            break

print("="*60)
print("END-TO-END VISION TEST")
print("="*60)

# Test HTML
test_html = """
<!DOCTYPE html>
<html>
<head><title>TPR Distribution Map</title></head>
<body style="background:linear-gradient(to right, red, yellow, green); width:800px; height:600px;">
    <h1>Malaria TPR Map - Test Region</h1>
    <div style="background:#ff0000; padding:10px; margin:10px; color:white;">Zone A: 85% TPR (Critical)</div>
    <div style="background:#ffaa00; padding:10px; margin:10px;">Zone B: 55% TPR (High)</div>
    <div style="background:#00ff00; padding:10px; margin:10px;">Zone C: 12% TPR (Low)</div>
</body>
</html>
"""

# Save test HTML
with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
    f.write(test_html)
    test_path = f.name

try:
    # 1. Test LLMAdapter directly
    print("\n1. Testing LLMAdapter...")
    from app.core.llm_adapter import LLMAdapter

    adapter = LLMAdapter(backend='openai', api_key=api_key)
    print(f"   ✓ LLMAdapter created")
    print(f"   ✓ Has generate_with_image: {hasattr(adapter, 'generate_with_image')}")

    # 2. Test UniversalVisualizationExplainer
    print("\n2. Testing UniversalVisualizationExplainer...")
    from app.services.universal_viz_explainer import UniversalVisualizationExplainer

    explainer = UniversalVisualizationExplainer(llm_manager=adapter)
    print(f"   ✓ Explainer created with LLMAdapter")

    # 3. Generate explanation
    print("\n3. Generating explanation...")
    explanation = explainer.explain_visualization(
        viz_path=test_path,
        viz_type='tpr_map',
        session_id='test_e2e_999'
    )

    # 4. Check results
    print("\n4. RESULTS:")
    print("-"*60)

    # Check for fallback phrases
    fallback_indicators = [
        "This visualization shows malaria risk analysis",
        "Tpr Map Generated",
        "This TPR (Test Positivity Rate) map displays"
    ]

    is_fallback = any(phrase in explanation for phrase in fallback_indicators)

    if is_fallback:
        print("❌ STILL SEEING FALLBACK")
        print("   Explanation is generic, not AI-generated")
    else:
        # Check for specific data from our test
        if "85%" in explanation or "Zone A" in explanation or "Critical" in explanation:
            print("✅ SUCCESS: TRUE AI VISION EXPLANATION!")
            print("   The AI correctly analyzed the specific data")
        else:
            print("⚠️  PARTIAL SUCCESS")
            print("   Got an AI response but it might not have seen the image")

    print(f"\nFirst 400 chars of explanation:")
    print(explanation[:400])

    # 5. Test via Flask app route
    print("\n5. Testing via Flask route...")
    from app import create_app
    app = create_app()

    with app.test_client() as client:
        # Set up session
        with client.session_transaction() as sess:
            sess['session_id'] = 'test_flask_route'

        # Call explain endpoint
        response = client.post('/explain_visualization',
            json={
                'visualization_path': test_path,
                'viz_type': 'tpr_map',
                'title': 'Test TPR Map'
            }
        )

        if response.status_code == 200:
            data = response.json
            if data.get('status') == 'success':
                flask_explanation = data.get('explanation', '')
                is_flask_fallback = any(phrase in flask_explanation for phrase in fallback_indicators)

                if is_flask_fallback:
                    print("   ❌ Flask route returns fallback")
                else:
                    print("   ✅ Flask route returns AI explanation")
            else:
                print(f"   ❌ Flask error: {data.get('message')}")
        else:
            print(f"   ❌ Flask HTTP error: {response.status_code}")

except Exception as e:
    import traceback
    print(f"\n❌ ERROR: {e}")
    traceback.print_exc()

finally:
    # Clean up
    if os.path.exists(test_path):
        os.unlink(test_path)

print("\n" + "="*60)
print("TEST COMPLETE")
print("="*60)
TESTSCRIPT

# Copy and run test
echo ""
echo "🔬 Running test on Instance 1..."
scp -i "$KEY" test_e2e.py "ec2-user@$INSTANCE:/tmp/"

ssh -i "$KEY" "ec2-user@$INSTANCE" << 'EOF'
source /home/ec2-user/chatmrpt_env/bin/activate
cd /home/ec2-user/ChatMRPT
python /tmp/test_e2e.py
rm -f /tmp/test_e2e.py
EOF

# Clean up
rm -f test_e2e.py

echo ""
echo "📊 Test Summary:"
echo "- If you see '✅ SUCCESS: TRUE AI VISION EXPLANATION!'"
echo "  then vision is working correctly"
echo "- If you see '❌ STILL SEEING FALLBACK'"
echo "  then there's still an issue to fix"