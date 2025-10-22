#!/bin/bash

echo "======================================"
echo "Deploying Optimized Arena Configuration"
echo "Using GPU Ollama for Fast Inference"
echo "======================================"

# Updated arena_manager.py configuration
cat > arena_manager_update.py << 'EOF'
# Arena Manager Update - Line to replace in __init__ method
        
        # Optimized model configuration for GPU Ollama
        # Using the 3 fastest and most capable models
        self.models = [
            'llama3.1:8b',    # Best overall capability (8B params)
            'mistral:7b',     # Strong reasoning (7.2B params)
            'phi3:mini'       # Ultra-fast responses (3.8B params)
        ]
        
        # Display names for UI
        self.model_display_names = {
            'llama3.1:8b': 'Llama 3.1 8B',
            'mistral:7b': 'Mistral 7B',
            'phi3:mini': 'Phi-3 Mini'
        }
EOF

# Deploy to both instances
for IP in 3.21.167.170 18.220.103.20; do
    echo ""
    echo "Deploying to Instance: $IP"
    echo "----------------------------"
    
    ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@$IP << 'REMOTE_EOF' 2>/dev/null
    cd /home/ec2-user/ChatMRPT
    
    # Backup current arena_manager.py
    cp app/core/arena_manager.py app/core/arena_manager.py.backup
    
    # Update the models list in arena_manager.py
    cat > temp_update.py << 'PYTHON'
import re

with open('app/core/arena_manager.py', 'r') as f:
    content = f.read()

# Find and replace the models list
pattern = r"self\.models = \[[^\]]+\]"
replacement = """self.models = [
            'llama3.1:8b',    # Best overall capability (8B params)
            'mistral:7b',     # Strong reasoning (7.2B params)
            'phi3:mini'       # Ultra-fast responses (3.8B params)
        ]"""

content = re.sub(pattern, replacement, content, count=1)

# Update display names
display_pattern = r"self\.model_display_names = \{[^\}]+\}"
display_replacement = """self.model_display_names = {
            'llama3.1:8b': 'Llama 3.1 8B',
            'mistral:7b': 'Mistral 7B',
            'phi3:mini': 'Phi-3 Mini'
        }"""

content = re.sub(display_pattern, display_replacement, content, count=1)

with open('app/core/arena_manager.py', 'w') as f:
    f.write(content)
    
print("✅ Updated arena_manager.py with optimized model configuration")
PYTHON
    
    python3 temp_update.py
    rm temp_update.py
    
    # Also update ollama_adapter timeout
    sed -i 's/timeout=aiohttp.ClientTimeout(total=120)/timeout=aiohttp.ClientTimeout(total=180)/' app/core/ollama_adapter.py
    
    # Restart service
    sudo systemctl restart chatmrpt
    
    echo "✅ Configuration deployed and service restarted"
REMOTE_EOF
    
    if [ $? -eq 0 ]; then
        echo "✅ Successfully deployed to $IP"
    else
        echo "⚠️ Deployment to $IP may have issues"
    fi
done

echo ""
echo "======================================"
echo "Testing GPU Ollama Performance"
echo "======================================"

# Test each model on GPU
echo "Testing model response times from production..."
ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@3.21.167.170 << 'TEST_EOF' 2>/dev/null
echo ""
echo "1. Testing Llama 3.1 8B..."
time curl -s -X POST http://172.31.45.157:11434/api/generate \
    -d '{"model": "llama3.1:8b", "prompt": "What is 2+2?", "stream": false, "options": {"num_predict": 20}}' \
    | python3 -c "import sys, json; data = json.load(sys.stdin); print(f\"Response: {data.get('response', 'ERROR')[:50]}...\")"

echo ""
echo "2. Testing Mistral 7B..."
time curl -s -X POST http://172.31.45.157:11434/api/generate \
    -d '{"model": "mistral:7b", "prompt": "What is 2+2?", "stream": false, "options": {"num_predict": 20}}' \
    | python3 -c "import sys, json; data = json.load(sys.stdin); print(f\"Response: {data.get('response', 'ERROR')[:50]}...\")"

echo ""
echo "3. Testing Phi-3 Mini..."
time curl -s -X POST http://172.31.45.157:11434/api/generate \
    -d '{"model": "phi3:mini", "prompt": "What is 2+2?", "stream": false, "options": {"num_predict": 20}}' \
    | python3 -c "import sys, json; data = json.load(sys.stdin); print(f\"Response: {data.get('response', 'ERROR')[:50]}...\")"
TEST_EOF

echo ""
echo "======================================"
echo "✅ Arena GPU Configuration Complete!"
echo "======================================"
echo ""
echo "Configuration Summary:"
echo "- GPU Instance: 172.31.45.157 (g5.xlarge with A10G)"
echo "- Models: Llama 3.1 8B, Mistral 7B, Phi-3 Mini"
echo "- Expected Response Time: 3-10 seconds per model"
echo "- Timeout: Increased to 180 seconds"
echo ""
echo "Test the arena at: https://d225ar6c86586s.cloudfront.net"