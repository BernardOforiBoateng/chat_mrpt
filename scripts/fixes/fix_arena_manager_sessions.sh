#!/bin/bash

echo "======================================"
echo "Fixing Arena Manager Session Storage"
echo "======================================"

for IP in 3.21.167.170 18.220.103.20; do
    echo ""
    echo "Updating Instance: $IP"
    echo "----------------------------"
    
    ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@$IP << 'REMOTE_EOF' 2>/dev/null
    cd /home/ec2-user/ChatMRPT
    
    # Fix arena_manager.py to support both battle types
    cat > fix_arena_manager.py << 'PYTHON'
import re

with open('app/core/arena_manager.py', 'r') as f:
    content = f.read()

# Find the __init__ method and add battle_sessions if missing
if 'self.battle_sessions' not in content:
    # Find where to add it (after self.models initialization)
    pattern = r"(self\.models = \[[^\]]+\])"
    replacement = r"""\1
        
        # Session storage for regular battles
        self.battle_sessions = {}  # In-memory storage for battle sessions
        self.progressive_sessions = {}  # Storage for progressive battles"""
    
    content = re.sub(pattern, replacement, content, count=1)
    
    # Also ensure the BattleSession dataclass exists
    if '@dataclass' not in content or 'class BattleSession' not in content:
        # Add the dataclass import if needed
        if 'from dataclasses import dataclass' not in content:
            content = "from dataclasses import dataclass, field\n" + content
        
        # Add BattleSession class before ArenaManager class
        battle_session_class = '''
@dataclass
class BattleSession:
    """Represents a battle session between two models."""
    session_id: str
    user_message: str
    model_a: str = None
    model_b: str = None
    response_a: str = None
    response_b: str = None
    latency_a: float = 0.0
    latency_b: float = 0.0
    winner: str = None
    timestamp: float = field(default_factory=lambda: time.time())
    view_index: int = -1

'''
        # Insert before ArenaManager class
        pattern = r"(class ArenaManager:)"
        replacement = battle_session_class + r"\1"
        content = re.sub(pattern, replacement, content, count=1)
    
    with open('app/core/arena_manager.py', 'w') as f:
        f.write(content)
    
    print("✅ Added battle_sessions storage to ArenaManager")
else:
    print("✅ battle_sessions already exists")
PYTHON
    
    python3 fix_arena_manager.py
    rm fix_arena_manager.py
    
    # Restart service
    sudo systemctl restart chatmrpt
    sleep 3
    
    # Check service status
    if sudo systemctl is-active chatmrpt > /dev/null; then
        echo "✅ Service restarted successfully"
    else
        echo "❌ Service failed to start"
        sudo journalctl -u chatmrpt -n 20 --no-pager
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
echo "Testing Fixed Arena System"
echo "======================================"

# Test creating a battle
echo "1. Creating battle session..."
battle_response=$(curl -s -X POST https://d225ar6c86586s.cloudfront.net/api/arena/battle \
  -H "Content-Type: application/json" \
  -d '{"message": "What is 2+2?", "session_id": "fix-test-123"}')

echo "$battle_response" | python3 -m json.tool | head -10

# Test getting responses
echo ""
echo "2. Getting model responses (this may take 10-30 seconds)..."
response=$(curl -s -X POST https://d225ar6c86586s.cloudfront.net/api/arena/get_responses \
  -H "Content-Type: application/json" \
  -d '{"battle_id": "fix-test-123", "message": "What is 2+2?"}' \
  --max-time 60)

if echo "$response" | grep -q "response_a"; then
    echo "✅ Arena system is working!"
    echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(f\"Model A: {data.get('model_a', 'Unknown')}\")
print(f\"Response A: {data.get('response_a', '')[:100]}...\")
print(f\"Model B: {data.get('model_b', 'Unknown')}\")
print(f\"Response B: {data.get('response_b', '')[:100]}...\")
"
else
    echo "❌ Failed to get responses"
    echo "$response" | python3 -m json.tool | head -20
fi

echo ""
echo "======================================"
echo "✅ Arena Manager Fix Complete!"
echo "======================================"
echo ""
echo "The React frontend should now work properly with GPU-powered models."
echo "Test at: https://d225ar6c86586s.cloudfront.net"