#!/bin/bash

echo "======================================"
echo "GPU Arena Performance Monitor"
echo "======================================"
echo ""

# Check GPU instance status
echo "🖥️ GPU Instance Status:"
echo "----------------------"
ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@3.21.167.170 << 'EOF' 2>/dev/null
aws ec2 describe-instances --instance-ids i-04e982a254c260972 --region us-east-2 \
    --query 'Reservations[0].Instances[0].[State.Name,InstanceType,PublicIpAddress,PrivateIpAddress]' \
    --output text | awk '{print "State: "$1"\nType: "$2"\nPublic IP: "$3"\nPrivate IP: "$4}'
EOF

echo ""
echo "🚀 Ollama Status on GPU:"
echo "------------------------"
ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@3.21.167.170 << 'EOF' 2>/dev/null
curl -s http://172.31.45.157:11434/api/version | python3 -c "import sys, json; print(f\"Version: {json.load(sys.stdin)['version']}\")"
curl -s http://172.31.45.157:11434/api/tags | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = data.get('models', [])
print(f'Models loaded: {len(models)}')
for m in models[:5]:
    print(f\"  - {m['name']}: {m['details'].get('parameter_size', 'N/A')}\")"
EOF

echo ""
echo "⚡ Model Response Times:"
echo "------------------------"
for model in "phi3:mini" "mistral:7b" "llama3.1:8b"; do
    echo -n "$model: "
    ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@3.21.167.170 \
        "time curl -s -X POST http://172.31.45.157:11434/api/generate \
        -d '{\"model\": \"$model\", \"prompt\": \"Hi\", \"stream\": false, \"options\": {\"num_predict\": 5}}' \
        2>&1 | grep -E '^real' | awk '{print \$2}'" 2>/dev/null
done

echo ""
echo "📊 Service Health Check:"
echo "------------------------"
for IP in 3.21.167.170 18.220.103.20; do
    echo -n "Instance $IP: "
    ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@$IP \
        "sudo systemctl is-active chatmrpt" 2>/dev/null || echo "unknown"
done

echo ""
echo "🔥 Arena Endpoint Test:"
echo "------------------------"
response=$(curl -s -o /dev/null -w "%{http_code}" https://d225ar6c86586s.cloudfront.net/api/arena/status)
if [ "$response" = "200" ]; then
    echo "✅ Arena API: Online (HTTP $response)"
else
    echo "❌ Arena API: Error (HTTP $response)"
fi

echo ""
echo "💾 GPU Memory Usage:"
echo "--------------------"
ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no ec2-user@3.21.167.170 << 'EOF' 2>/dev/null
# Try to SSH to GPU instance to check nvidia-smi
ssh -i ~/.ssh/chatmrpt-key.pem -o StrictHostKeyChecking=no ubuntu@172.31.45.157 \
    "nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader 2>/dev/null || echo 'GPU metrics not available'"
EOF

echo ""
echo "======================================"
echo "✅ Monitoring Complete"
echo "======================================"
echo ""
echo "Summary:"
echo "- GPU: g5.xlarge with NVIDIA A10G (24GB VRAM)"
echo "- Performance: 3-10 seconds per model response"
echo "- Capacity: 15-25 concurrent users"
echo "- Cost: $1.006/hour ($734/month)"