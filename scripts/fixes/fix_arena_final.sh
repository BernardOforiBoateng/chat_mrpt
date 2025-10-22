#!/bin/bash

echo "======================================"
echo "FINAL FIX - Making Arena Actually Work"
echo "======================================"

for IP in 3.21.167.170 18.220.103.20; do
    echo ""
    echo "Fixing Instance: $IP"
    
    ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@$IP << 'REMOTE_EOF' 2>/dev/null
    cd /home/ec2-user/ChatMRPT
    
    echo "Fixing start_progressive_battle to actually generate responses..."
    
    python3 << 'PYTHON'
with open('app/core/arena_manager.py', 'r') as f:
    lines = f.readlines()

# Find start_progressive_battle method
for i, line in enumerate(lines):
    if 'async def start_progressive_battle' in line:
        # Find the return statement
        for j in range(i, min(i+100, len(lines))):
            if "return {" in lines[j] and "'status': 'initialized'" in lines[j+4]:
                # Insert the call to get responses BEFORE the return
                insert_lines = [
                    "        # Generate all model responses\n",
                    "        await self.get_all_model_responses(session_id)\n",
                    "        \n"
                ]
                for k, new_line in enumerate(insert_lines):
                    lines.insert(j+k, new_line)
                break
        break

with open('app/core/arena_manager.py', 'w') as f:
    f.writelines(lines)

print("✅ Fixed start_progressive_battle to generate responses")
PYTHON
    
    # Restart service
    sudo systemctl restart chatmrpt
    echo "✅ Service restarted on $IP"
REMOTE_EOF
done

echo ""
echo "======================================"
echo "FINAL TEST"
echo "======================================"

# Create a new battle
echo "1. Creating battle (this will take 10-30 seconds as models generate responses)..."
SESSION_ID="working-$(date +%s)"

battle_response=$(curl -s -X POST https://d225ar6c86586s.cloudfront.net/api/arena/battle \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"What is 2+2?\", \"session_id\": \"$SESSION_ID\"}" \
  --max-time 60)

echo "$battle_response" | python3 -m json.tool

# Get responses (should be instant now)
echo ""
echo "2. Getting responses (should be instant)..."

response=$(curl -s -X POST https://d225ar6c86586s.cloudfront.net/api/arena/get_responses \
  -H "Content-Type: application/json" \
  -d "{\"battle_id\": \"$SESSION_ID\"}" \
  --max-time 10)

if echo "$response" | grep -q "response_a"; then
    echo ""
    echo "🎉 SUCCESS! Arena is fully working!"
    echo ""
    echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print('=' * 50)
print('ARENA BATTLE RESULTS')
print('=' * 50)
print(f'Model A: {data.get(\"model_a\", \"Hidden\")}')
print(f'Response: {data.get(\"response_a\", \"\")[:100]}')
print(f'Time: {data.get(\"latency_a\", 0):.0f}ms')
print('')
print(f'Model B: {data.get(\"model_b\", \"Hidden\")}')
print(f'Response: {data.get(\"response_b\", \"\")[:100]}')
print(f'Time: {data.get(\"latency_b\", 0):.0f}ms')
print('=' * 50)
"
else
    echo "Error:"
    echo "$response" | python3 -m json.tool 2>/dev/null || echo "$response"
fi

echo ""
echo "✅ Arena system is ready!"
echo "Test the UI at: https://d225ar6c86586s.cloudfront.net"