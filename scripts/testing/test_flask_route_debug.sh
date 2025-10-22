#!/bin/bash
# Debug Flask route issue

echo "🔍 Debugging Flask Route Vision Issue..."

INSTANCE="3.21.167.170"
KEY="/tmp/chatmrpt-key2.pem"

if [ ! -f "$KEY" ]; then
    cp aws_files/chatmrpt-key.pem "$KEY"
    chmod 600 "$KEY"
fi

cat > test_flask_debug.py << 'TESTSCRIPT'
#!/usr/bin/env python3
"""Debug Flask route vision issue"""

import os
import sys

sys.path.insert(0, '/home/ec2-user/ChatMRPT')
os.environ['ENABLE_VISION_EXPLANATIONS'] = 'true'

# Load API key
with open('/home/ec2-user/ChatMRPT/.env', 'r') as f:
    for line in f:
        if line.startswith('OPENAI_API_KEY='):
            os.environ['OPENAI_API_KEY'] = line.strip().split('=')[1]
            break

print("="*60)
print("FLASK ROUTE DEBUG")
print("="*60)

# Import Flask app
from app import create_app

app = create_app()

# Test within app context
with app.app_context():
    print("\n1. Checking services container...")

    # Get llm_manager from services
    llm = app.services.llm_manager
    print(f"   LLM Manager type: {type(llm)}")
    print(f"   Has generate_with_image: {hasattr(llm, 'generate_with_image')}")

    # List all methods
    methods = [m for m in dir(llm) if not m.startswith('_')]
    print(f"   Available methods: {methods[:5]}...")

    # Check if it has generate_response (for fallback)
    print(f"   Has generate_response: {hasattr(llm, 'generate_response')}")
    print(f"   Has generate: {hasattr(llm, 'generate')}")

    print("\n2. Testing UniversalVisualizationExplainer...")
    from app.services.universal_viz_explainer import get_universal_viz_explainer

    # Test with None llm_manager (what happens by default)
    explainer1 = get_universal_viz_explainer(llm_manager=None)
    print(f"   Explainer with None: llm_manager={explainer1.llm_manager}")

    # Test with actual llm_manager
    explainer2 = get_universal_viz_explainer(llm_manager=llm)
    print(f"   Explainer with LLM: llm_manager type={type(explainer2.llm_manager)}")
    print(f"   Has generate_with_image: {hasattr(explainer2.llm_manager, 'generate_with_image') if explainer2.llm_manager else False}")

    print("\n3. Checking visualization_routes.py logic...")

    # Simulate what the route does
    from flask import current_app

    # This is what visualization_routes.py does:
    llm_manager = current_app.services.llm_manager
    print(f"   Route gets LLM type: {type(llm_manager)}")
    print(f"   Route LLM has method: {hasattr(llm_manager, 'generate_with_image')}")

    # Create explainer like the route does
    explainer = get_universal_viz_explainer(llm_manager=llm_manager)
    print(f"   Route explainer LLM: {type(explainer.llm_manager) if explainer.llm_manager else None}")
    print(f"   Route explainer check: {hasattr(explainer.llm_manager, 'generate_with_image') if explainer.llm_manager else False}")

    # Check LLMAdapter specifically
    print("\n4. LLMAdapter methods check...")
    if hasattr(llm_manager, 'generate'):
        # It's an LLMAdapter
        print(f"   ✓ This is an LLMAdapter")

        # Check if generate_response is actually a wrapper
        if hasattr(llm_manager, 'generate_response'):
            print(f"   ✓ Has generate_response method")
        else:
            print(f"   ✗ Missing generate_response method")
            print(f"   Note: LLMAdapter has 'generate' not 'generate_response'")

print("\n" + "="*60)
print("DEBUG COMPLETE")
print("="*60)
TESTSCRIPT

echo ""
echo "🔬 Running debug on Instance 1..."
scp -i "$KEY" test_flask_debug.py "ec2-user@$INSTANCE:/tmp/"

ssh -i "$KEY" "ec2-user@$INSTANCE" << 'EOF'
source /home/ec2-user/chatmrpt_env/bin/activate
cd /home/ec2-user/ChatMRPT
python /tmp/test_flask_debug.py
rm -f /tmp/test_flask_debug.py
EOF

rm -f test_flask_debug.py

echo ""
echo "📝 Debug Analysis:"
echo "This will show us exactly what type of object the Flask route is getting"
echo "and why it might not have the generate_with_image method."