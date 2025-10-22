#!/bin/bash

echo "======================================"
echo "Adding /battle route for React frontend compatibility"
echo "======================================"

for IP in 3.21.167.170 18.220.103.20; do
    echo ""
    echo "Updating Instance: $IP"
    echo "----------------------------"
    
    ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@$IP << 'REMOTE_EOF' 2>/dev/null
    cd /home/ec2-user/ChatMRPT
    
    # Add the /battle route that maps to start_battle
    cat > add_battle_route.py << 'PYTHON'
import re

with open('app/web/routes/arena_routes.py', 'r') as f:
    content = f.read()

# Check if /battle route already exists
if "'/battle'" not in content:
    # Find the start_battle route and add /battle as an alias
    pattern = r"(@arena_bp.route\('/start_battle', methods=\['POST'\]\))"
    replacement = r"@arena_bp.route('/battle', methods=['POST'])  # Alias for React frontend\n\1"
    
    content = re.sub(pattern, replacement, content, count=1)
    
    with open('app/web/routes/arena_routes.py', 'w') as f:
        f.write(content)
    
    print("✅ Added /battle route alias")
else:
    print("✅ /battle route already exists")
PYTHON
    
    python3 add_battle_route.py
    rm add_battle_route.py
    
    # Also add /get_responses alias if needed  
    cat > add_responses_route.py << 'PYTHON'
import re

with open('app/web/routes/arena_routes.py', 'r') as f:
    content = f.read()

# Check if we need streaming endpoint too
if "'/responses'" not in content:
    # Find the get_responses route and add /responses as an alias
    pattern = r"(@arena_bp.route\('/get_responses', methods=\['POST'\]\))"
    replacement = r"@arena_bp.route('/responses', methods=['POST'])  # Alias for React frontend\n\1"
    
    content = re.sub(pattern, replacement, content, count=1)
    
    with open('app/web/routes/arena_routes.py', 'w') as f:
        f.write(content)
    
    print("✅ Added /responses route alias")
else:
    print("✅ /responses route already exists")
PYTHON
    
    python3 add_responses_route.py
    rm add_responses_route.py
    
    # Restart service
    sudo systemctl restart chatmrpt
    
    echo "✅ Routes updated and service restarted"
REMOTE_EOF
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully updated $IP"
    else
        echo "⚠️ Update to $IP may have issues"
    fi
done

echo ""
echo "======================================"
echo "Testing Arena Battle Endpoint"
echo "======================================"

# Test the /battle endpoint
echo "Testing /api/arena/battle endpoint..."
response=$(curl -s -X POST https://d225ar6c86586s.cloudfront.net/api/arena/battle \
  -H "Content-Type: application/json" \
  -d '{"message": "test", "session_id": "test-route-fix"}' \
  -w "\nHTTP_STATUS:%{http_code}")

http_status=$(echo "$response" | grep "HTTP_STATUS" | cut -d':' -f2)

if [ "$http_status" = "200" ]; then
    echo "✅ /api/arena/battle endpoint is working!"
else
    echo "❌ /api/arena/battle returned status: $http_status"
fi

echo ""
echo "======================================"
echo "✅ Route Fix Complete!"
echo "======================================"
echo ""
echo "The React frontend should now work properly."
echo "Test at: https://d225ar6c86586s.cloudfront.net"