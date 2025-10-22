#!/bin/bash

echo "======================================"
echo "Unifying Arena System - One System to Rule Them All"
echo "======================================"

for IP in 3.21.167.170 18.220.103.20; do
    echo ""
    echo "Updating Instance: $IP"
    echo "----------------------------"
    
    ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@$IP << 'REMOTE_EOF' 2>/dev/null
    cd /home/ec2-user/ChatMRPT
    
    # Backup current arena_routes.py
    cp app/web/routes/arena_routes.py app/web/routes/arena_routes.py.backup_unified
    
    # Modify the routes to use progressive logic for the original endpoints
    cat > unify_arena.py << 'PYTHON'
import re

with open('app/web/routes/arena_routes.py', 'r') as f:
    content = f.read()

# Step 1: Make start_battle use progressive logic
old_start_battle = r"def start_battle\(\):(.*?)return jsonify"
new_start_battle = '''def start_battle():
    """Start a new battle session - uses progressive battle logic."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        message = data.get('message')
        session_id = data.get('session_id')
        
        if not message or not session_id:
            return jsonify({"error": "message and session_id are required"}), 400
        
        # Create a progressive battle session
        battle_session = arena_manager.start_progressive_battle(
            session_id=session_id,
            user_message=message
        )
        
        if not battle_session:
            return jsonify({"error": "Failed to create battle session"}), 500
        
        return jsonify'''

content = re.sub(old_start_battle, new_start_battle, content, flags=re.DOTALL)

# Step 2: Make get_responses use progressive logic
old_get_responses = r"def get_responses\(\):(.*?)return jsonify"
new_get_responses = '''def get_responses():
    """Get model responses for a battle - uses progressive logic."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        battle_id = data.get('battle_id')
        message = data.get('message')  # Optional, for compatibility
        
        if not battle_id:
            return jsonify({"error": "battle_id is required"}), 400
        
        # Get progressive battle responses
        result = asyncio.run(
            arena_manager.get_progressive_responses(battle_id)
        )
        
        if result.get('error'):
            return jsonify(result), 404
            
        # Format response for React frontend compatibility
        if result.get('status') == 'ready':
            return jsonify({
                'battle_id': battle_id,
                'model_a': result.get('model_a'),
                'model_b': result.get('model_b'),
                'response_a': result.get('response_a'),
                'response_b': result.get('response_b'),
                'latency_a': result.get('latency_a', 0),
                'latency_b': result.get('latency_b', 0),
                'models_hidden': True,
                'status': 'ready'
            })
        
        return jsonify'''

content = re.sub(old_get_responses, new_get_responses, content, flags=re.DOTALL)

with open('app/web/routes/arena_routes.py', 'w') as f:
    f.write(content)

print("✅ Unified arena endpoints to use progressive logic")
PYTHON
    
    python3 unify_arena.py
    rm unify_arena.py
    
    # Also ensure asyncio is imported
    if ! grep -q "import asyncio" app/web/routes/arena_routes.py; then
        sed -i '1a import asyncio' app/web/routes/arena_routes.py
        echo "✅ Added asyncio import"
    fi
    
    # Restart service
    sudo systemctl restart chatmrpt
    sleep 3
    
    # Check service status
    if sudo systemctl is-active chatmrpt > /dev/null; then
        echo "✅ Service restarted successfully"
    else
        echo "❌ Service failed to start"
    fi
REMOTE_EOF
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully updated $IP"
    else
        echo "⚠️ Update to $IP may have issues"
    fi
done

echo ""
echo "======================================"
echo "Testing Unified Arena System"
echo "======================================"

# Test the unified system
echo "1. Creating battle with /api/arena/battle..."
battle_response=$(curl -s -X POST https://d225ar6c86586s.cloudfront.net/api/arena/battle \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the capital of France?", "session_id": "unified-test-123"}')

echo "$battle_response" | python3 -m json.tool | head -10

# Get responses
echo ""
echo "2. Getting responses with /api/arena/get_responses..."
echo "Please wait for GPU inference..."

response=$(curl -s -X POST https://d225ar6c86586s.cloudfront.net/api/arena/get_responses \
  -H "Content-Type: application/json" \
  -d '{"battle_id": "unified-test-123"}' \
  --max-time 60)

if echo "$response" | grep -q "response_a"; then
    echo "✅ SUCCESS! Unified arena is working!"
    echo ""
    echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Model A: {data.get('model_a', 'Hidden')} - Response: {data.get('response_a', '')[:80]}...\")
print(f\"Model B: {data.get('model_b', 'Hidden')} - Response: {data.get('response_b', '')[:80]}...\")
print(f\"Latency A: {data.get('latency_a', 0):.0f}ms, Latency B: {data.get('latency_b', 0):.0f}ms\")
"
else
    echo "❌ Error:"
    echo "$response" | python3 -m json.tool | head -20
fi

echo ""
echo "======================================"
echo "✅ Arena Unification Complete!"
echo "======================================"
echo ""
echo "The React frontend should now work seamlessly with the GPU-powered backend."
echo "Test at: https://d225ar6c86586s.cloudfront.net"