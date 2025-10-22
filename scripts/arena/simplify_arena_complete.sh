#!/bin/bash

echo "======================================"
echo "SIMPLIFYING ARENA SYSTEM - ONE CLEAN IMPLEMENTATION"
echo "======================================"

for IP in 3.21.167.170 18.220.103.20; do
    echo ""
    echo "Fixing Instance: $IP"
    echo "======================================"
    
    ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@$IP << 'REMOTE_EOF' 2>/dev/null
    cd /home/ec2-user/ChatMRPT
    
    # Backup files before changes
    cp app/core/arena_manager.py app/core/arena_manager.py.backup_simplify
    cp app/web/routes/arena_routes.py app/web/routes/arena_routes.py.backup_simplify
    
    echo "Step 1: Adding get_responses() method to ArenaManager..."
    
    # Add the missing get_responses method
    python3 << 'PYTHON'
import re

with open('app/core/arena_manager.py', 'r') as f:
    content = f.read()

# Add get_responses method after start_progressive_battle
if 'async def get_responses' not in content:
    # Find where to insert it (after start_progressive_battle)
    insert_pos = content.find('def submit_progressive_choice')
    if insert_pos > 0:
        new_method = '''
    async def get_responses(self, battle_id: str) -> Dict[str, Any]:
        """
        Get responses for a battle session.
        This retrieves the responses that were already generated when the battle started.
        """
        # Get the progressive battle session
        battle = self.storage.get_progressive_battle(battle_id)
        
        if not battle:
            return {'error': 'Battle session not found'}
        
        # Check if we have responses for the current pair
        if battle.current_pair and len(battle.all_responses) >= 2:
            model_a, model_b = battle.current_pair
            
            return {
                'battle_id': battle_id,
                'model_a': model_a,
                'model_b': model_b,
                'response_a': battle.all_responses.get(model_a, ''),
                'response_b': battle.all_responses.get(model_b, ''),
                'latency_a': battle.all_latencies.get(model_a, 0),
                'latency_b': battle.all_latencies.get(model_b, 0),
                'status': 'ready',
                'remaining_comparisons': len(battle.remaining_models)
            }
        
        return {'error': 'No responses available yet', 'status': 'waiting'}
    
'''
        content = content[:insert_pos] + new_method + content[insert_pos:]
        
        with open('app/core/arena_manager.py', 'w') as f:
            f.write(content)
        
        print("✅ Added get_responses() method")
else:
    print("✅ get_responses() method already exists")
PYTHON
    
    echo "Step 2: Fixing model names to match Ollama..."
    
    # Fix model names in arena_manager.py
    sed -i "s/'llama3.2-3b'/'llama3.1:8b'/g" app/core/arena_manager.py
    sed -i "s/'phi3-mini'/'phi3:mini'/g" app/core/arena_manager.py
    sed -i "s/'mistral-7b'/'mistral:7b'/g" app/core/arena_manager.py
    sed -i "s/'gemma2-2b'/'gemma2:2b'/g" app/core/arena_manager.py
    sed -i "s/'qwen2.5-3b'/'qwen2.5:3b'/g" app/core/arena_manager.py
    
    echo "✅ Fixed model names"
    
    echo "Step 3: Simplifying routes..."
    
    # Create clean routes file
    cat > fix_routes_final.py << 'PYTHON'
import re

with open('app/web/routes/arena_routes.py', 'r') as f:
    lines = f.readlines()

# Find and replace the /battle and /get_responses routes with clean versions
new_lines = []
skip_until_next_def = False
in_route_def = None

for i, line in enumerate(lines):
    # Check if we're at a route definition we want to replace
    if '@arena_bp.route' in line:
        if "'/battle'" in line or "'/start_battle'" in line:
            # Add clean battle route
            if "'/battle'" in line:  # Only add once for /battle
                new_lines.append("@arena_bp.route('/battle', methods=['POST'])\n")
                new_lines.append("def battle():\n")
                new_lines.append('    """Start a new battle session."""\n')
                new_lines.append('    try:\n')
                new_lines.append('        data = request.get_json()\n')
                new_lines.append('        if not data:\n')
                new_lines.append('            return jsonify({"error": "No data provided"}), 400\n')
                new_lines.append('        \n')
                new_lines.append('        message = data.get("message", "").strip()\n')
                new_lines.append('        session_id = data.get("session_id", "").strip()\n')
                new_lines.append('        \n')
                new_lines.append('        if not message or not session_id:\n')
                new_lines.append('            return jsonify({"error": "message and session_id are required"}), 400\n')
                new_lines.append('        \n')
                new_lines.append('        # Use progressive battle logic (it works with GPU)\n')
                new_lines.append('        battle_session = asyncio.run(\n')
                new_lines.append('            arena_manager.start_progressive_battle(\n')
                new_lines.append('                session_id=session_id,\n')
                new_lines.append('                user_message=message\n')
                new_lines.append('            )\n')
                new_lines.append('        )\n')
                new_lines.append('        \n')
                new_lines.append('        if not battle_session:\n')
                new_lines.append('            return jsonify({"error": "Failed to create battle"}), 500\n')
                new_lines.append('        \n')
                new_lines.append('        return jsonify({\n')
                new_lines.append('            "battle_id": session_id,\n')
                new_lines.append('            "status": "ready",\n')
                new_lines.append('            "message": "Battle session created. Waiting for model responses.",\n')
                new_lines.append('            "models_hidden": True,\n')
                new_lines.append('            "view_index": -1\n')
                new_lines.append('        })\n')
                new_lines.append('    except Exception as e:\n')
                new_lines.append('        logger.error(f"Error in battle: {e}")\n')
                new_lines.append('        return jsonify({"error": str(e)}), 500\n')
                new_lines.append('\n')
                skip_until_next_def = True
            else:
                skip_until_next_def = True  # Skip duplicate start_battle
                
        elif "'/get_responses'" in line or "'/responses'" in line:
            if "'/get_responses'" in line:  # Only add once
                new_lines.append("@arena_bp.route('/get_responses', methods=['POST'])\n")
                new_lines.append("def get_responses():\n")
                new_lines.append('    """Get model responses for a battle."""\n')
                new_lines.append('    try:\n')
                new_lines.append('        data = request.get_json()\n')
                new_lines.append('        if not data:\n')
                new_lines.append('            return jsonify({"error": "No data provided"}), 400\n')
                new_lines.append('        \n')
                new_lines.append('        battle_id = data.get("battle_id", "").strip()\n')
                new_lines.append('        if not battle_id:\n')
                new_lines.append('            return jsonify({"error": "battle_id is required"}), 400\n')
                new_lines.append('        \n')
                new_lines.append('        # Get responses from the battle session\n')
                new_lines.append('        result = asyncio.run(\n')
                new_lines.append('            arena_manager.get_responses(battle_id)\n')
                new_lines.append('        )\n')
                new_lines.append('        \n')
                new_lines.append('        if result.get("error"):\n')
                new_lines.append('            return jsonify(result), 404\n')
                new_lines.append('        \n')
                new_lines.append('        # Return in format expected by React\n')
                new_lines.append('        return jsonify({\n')
                new_lines.append('            "battle_id": battle_id,\n')
                new_lines.append('            "model_a": result.get("model_a", "Model A"),\n')
                new_lines.append('            "model_b": result.get("model_b", "Model B"),\n')
                new_lines.append('            "response_a": result.get("response_a", ""),\n')
                new_lines.append('            "response_b": result.get("response_b", ""),\n')
                new_lines.append('            "latency_a": result.get("latency_a", 0),\n')
                new_lines.append('            "latency_b": result.get("latency_b", 0),\n')
                new_lines.append('            "models_hidden": True,\n')
                new_lines.append('            "status": "ready"\n')
                new_lines.append('        })\n')
                new_lines.append('    except Exception as e:\n')
                new_lines.append('        logger.error(f"Error getting responses: {e}")\n')
                new_lines.append('        return jsonify({"error": str(e)}), 500\n')
                new_lines.append('\n')
                skip_until_next_def = True
            else:
                skip_until_next_def = True  # Skip duplicate
                
        # Remove progressive endpoints
        elif any(x in line for x in ["'/start_progressive'", "'/get_progressive_responses'", "'/submit_progressive_choice'"]):
            skip_until_next_def = True
        else:
            new_lines.append(line)
    elif skip_until_next_def:
        # Skip lines until we find the next function definition
        if line.startswith('def ') or line.startswith('@'):
            skip_until_next_def = False
            if line.startswith('@'):
                new_lines.append(line)
    else:
        new_lines.append(line)

with open('app/web/routes/arena_routes.py', 'w') as f:
    f.writelines(new_lines)

print("✅ Simplified routes")
PYTHON
    
    python3 fix_routes_final.py
    rm fix_routes_final.py
    
    # Ensure asyncio is imported
    if ! grep -q "import asyncio" app/web/routes/arena_routes.py; then
        sed -i '/^import/a import asyncio' app/web/routes/arena_routes.py
    fi
    
    echo "✅ All fixes applied"
    
    # Restart service
    sudo systemctl restart chatmrpt
    sleep 3
    
    if sudo systemctl is-active chatmrpt > /dev/null; then
        echo "✅ Service restarted successfully on $IP"
    else
        echo "❌ Service failed on $IP"
        sudo journalctl -u chatmrpt -n 20 --no-pager
    fi
REMOTE_EOF
done

echo ""
echo "======================================"
echo "TESTING SIMPLIFIED ARENA SYSTEM"  
echo "======================================"

# Test the simplified system
echo "1. Creating battle..."
battle_response=$(curl -s -X POST https://d225ar6c86586s.cloudfront.net/api/arena/battle \
  -H "Content-Type: application/json" \
  -d '{"message": "What is artificial intelligence?", "session_id": "simple-test-'$(date +%s)'"}')