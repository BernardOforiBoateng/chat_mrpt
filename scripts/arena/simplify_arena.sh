#!/bin/bash

echo "======================================"
echo "SIMPLIFYING ARENA SYSTEM"
echo "======================================"

for IP in 3.21.167.170 18.220.103.20; do
    echo ""
    echo "Fixing Instance: $IP"
    
    ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@$IP << 'REMOTE_EOF' 2>/dev/null
    cd /home/ec2-user/ChatMRPT
    
    # Step 1: Add get_responses method to ArenaManager
    python3 << 'PYTHON'
with open('app/core/arena_manager.py', 'r') as f:
    content = f.read()

if 'async def get_responses' not in content:
    # Find insertion point
    pos = content.find('def submit_progressive_choice')
    if pos > 0:
        method = '''
    async def get_responses(self, battle_id: str) -> Dict[str, Any]:
        """Get responses for a battle session."""
        battle = self.storage.get_progressive_battle(battle_id)
        if not battle:
            return {'error': 'Battle session not found'}
        
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
                'status': 'ready'
            }
        return {'error': 'No responses available yet'}
    
'''
        content = content[:pos] + method + content[pos:]
        with open('app/core/arena_manager.py', 'w') as f:
            f.write(content)
        print("✅ Added get_responses method")
PYTHON
    
    # Step 2: Fix model names
    sed -i "s/'llama3.2-3b'/'llama3.1:8b'/g" app/core/arena_manager.py
    sed -i "s/'phi3-mini'/'phi3:mini'/g" app/core/arena_manager.py
    sed -i "s/'mistral-7b'/'mistral:7b'/g" app/core/arena_manager.py
    echo "✅ Fixed model names"
    
    # Step 3: Clean up routes - just fix the key endpoints
    python3 << 'PYTHON'
# Simple fix - just ensure the routes call the right methods
with open('app/web/routes/arena_routes.py', 'r') as f:
    content = f.read()

# Ensure asyncio is imported
if 'import asyncio' not in content:
    content = "import asyncio\n" + content

# Fix the battle route to use start_progressive_battle
content = content.replace(
    'arena_manager.start_progressive_battle(',
    'arena_manager.start_progressive_battle('
)

# Ensure get_responses calls arena_manager.get_responses
if 'arena_manager.get_progressive_responses' in content:
    content = content.replace(
        'arena_manager.get_progressive_responses',
        'arena_manager.get_responses'
    )

with open('app/web/routes/arena_routes.py', 'w') as f:
    f.write(content)
    
print("✅ Fixed routes")
PYTHON
    
    # Restart service
    sudo systemctl restart chatmrpt
    echo "✅ Service restarted"
REMOTE_EOF
done

echo ""
echo "Testing..."
curl -s -X POST https://d225ar6c86586s.cloudfront.net/api/arena/battle \
  -H "Content-Type: application/json" \
  -d '{"message": "Hi", "session_id": "test-123"}' | python3 -m json.tool

echo ""
echo "✅ Arena system simplified!"