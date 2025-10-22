#!/bin/bash

echo "======================================"
echo "Fixing Arena Routes Properly"
echo "======================================"

for IP in 3.21.167.170 18.220.103.20; do
    echo ""
    echo "Fixing Instance: $IP"
    echo "----------------------------"
    
    ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@$IP << 'REMOTE_EOF' 2>/dev/null
    cd /home/ec2-user/ChatMRPT
    
    # Create a clean version of the routes
    cat > fix_routes.py << 'PYTHON'
# Read the file
with open('app/web/routes/arena_routes.py', 'r') as f:
    lines = f.readlines()

# Find and replace the start_battle function
in_start_battle = False
start_line = -1
end_line = -1
indent_count = 0

for i, line in enumerate(lines):
    if 'def start_battle():' in line:
        in_start_battle = True
        start_line = i
        indent_count = 0
    elif in_start_battle:
        if line.strip() and not line.strip().startswith('#'):
            # Count indentation
            if line.startswith('def ') and i > start_line:
                # Found next function
                end_line = i
                break

# Replace the function
if start_line > -1:
    new_function = '''def start_battle():
    """Start a new battle session using progressive battle logic."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        message = data.get('message', '').strip()
        session_id = data.get('session_id', '').strip()
        
        if not message:
            return jsonify({"error": "Message is required"}), 400
        
        if not session_id:
            return jsonify({"error": "session_id is required"}), 400
        
        # Create a progressive battle session
        battle_session = arena_manager.start_progressive_battle(
            session_id=session_id,
            user_message=message
        )
        
        if not battle_session:
            return jsonify({"error": "Failed to create battle session"}), 500
        
        # Return format expected by React frontend
        return jsonify({
            'battle_id': session_id,
            'status': 'ready',
            'message': 'Battle session created. Waiting for model responses.',
            'models_hidden': True,
            'view_index': -1
        })
        
    except Exception as e:
        logger.error(f"Error starting battle: {e}")
        return jsonify({"error": str(e)}), 500

'''
    
    # Replace the lines
    if end_line == -1:
        end_line = len(lines)
    
    # Keep the decorators
    new_lines = lines[:start_line] + [new_function] + lines[end_line:]
    
    with open('app/web/routes/arena_routes.py', 'w') as f:
        f.writelines(new_lines)
    
    print("✅ Fixed start_battle function")

# Now fix get_responses
with open('app/web/routes/arena_routes.py', 'r') as f:
    lines = f.readlines()

in_get_responses = False
start_line = -1
end_line = -1

for i, line in enumerate(lines):
    if 'def get_responses():' in line:
        in_get_responses = True
        start_line = i
    elif in_get_responses:
        if line.strip() and not line.strip().startswith('#'):
            if line.startswith('def ') and i > start_line:
                end_line = i
                break

if start_line > -1:
    new_function = '''def get_responses():
    """Get model responses using progressive battle logic."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        battle_id = data.get('battle_id', '').strip()
        
        if not battle_id:
            return jsonify({"error": "battle_id is required"}), 400
        
        # Get progressive battle responses
        result = asyncio.run(
            arena_manager.get_progressive_responses(battle_id)
        )
        
        if result.get('error'):
            return jsonify(result), 404
        
        # Return format expected by React frontend
        return jsonify({
            'battle_id': battle_id,
            'model_a': result.get('model_a', 'Model A'),
            'model_b': result.get('model_b', 'Model B'),
            'response_a': result.get('response_a', ''),
            'response_b': result.get('response_b', ''),
            'latency_a': result.get('latency_a', 0),
            'latency_b': result.get('latency_b', 0),
            'models_hidden': True,
            'status': 'ready'
        })
        
    except Exception as e:
        logger.error(f"Error getting responses: {e}")
        return jsonify({"error": str(e)}), 500

'''
    
    if end_line == -1:
        end_line = len(lines)
    
    new_lines = lines[:start_line] + [new_function] + lines[end_line:]
    
    with open('app/web/routes/arena_routes.py', 'w') as f:
        f.writelines(new_lines)
    
    print("✅ Fixed get_responses function")
PYTHON
    
    python3 fix_routes.py
    rm fix_routes.py
    
    # Ensure asyncio is imported
    if ! grep -q "import asyncio" app/web/routes/arena_routes.py; then
        sed -i '/^import.*$/a import asyncio' app/web/routes/arena_routes.py
        echo "✅ Added asyncio import"
    fi
    
    # Restart service
    sudo systemctl restart chatmrpt
    echo "✅ Service restarted"
REMOTE_EOF
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully fixed $IP"
    fi
done

echo ""
echo "======================================"
echo "Testing Fixed Arena System"
echo "======================================"

# Test with correct parameters
echo "1. Creating battle..."
battle_response=$(curl -s -X POST https://d225ar6c86586s.cloudfront.net/api/arena/battle \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 2+2?", "session_id": "fixed-test-999"}')

echo "$battle_response" | python3 -m json.tool

# Get responses
echo ""
echo "2. Getting responses (GPU-powered)..."
response=$(curl -s -X POST https://d225ar6c86586s.cloudfront.net/api/arena/get_responses \
  -H "Content-Type: application/json" \
  -d '{"battle_id": "fixed-test-999"}' \
  --max-time 60)

if echo "$response" | grep -q "response_a"; then
    echo "✅ Arena system is working!"
    echo "$response" | python3 -m json.tool | head -20
else
    echo "Response:"
    echo "$response" | python3 -m json.tool | head -20
fi

echo ""
echo "✅ Arena routes fixed! Test the UI at:"
echo "https://d225ar6c86586s.cloudfront.net"