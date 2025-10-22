#!/bin/bash

# Deploy Arena Model Fix to Production AWS Instances
# This fixes the ollama_model_map to match ArenaManager's actual model names

echo "================================================"
echo "Deploying Arena Model Fix to Production"
echo "================================================"
echo ""

# Production instances (formerly staging)
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"

# Key file location (copy to /tmp for security)
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

echo "📦 Deploying to Instance 1: $INSTANCE_1"
echo "----------------------------------------"

# Copy the fixed analysis_routes.py to Instance 1
scp -i /tmp/chatmrpt-key2.pem \
    app/web/routes/analysis_routes.py \
    ec2-user@$INSTANCE_1:/home/ec2-user/ChatMRPT/app/web/routes/

# Restart service on Instance 1
ssh -i /tmp/chatmrpt-key2.pem ec2-user@$INSTANCE_1 << 'EOF'
    echo "🔄 Restarting ChatMRPT service..."
    sudo systemctl restart chatmrpt
    
    # Check service status
    echo "✅ Service status:"
    sudo systemctl status chatmrpt | grep Active
    
    # Check Ollama is running
    echo "🤖 Checking Ollama status..."
    curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "Ollama check failed"
EOF

echo ""
echo "📦 Deploying to Instance 2: $INSTANCE_2"
echo "----------------------------------------"

# Copy the fixed analysis_routes.py to Instance 2
scp -i /tmp/chatmrpt-key2.pem \
    app/web/routes/analysis_routes.py \
    ec2-user@$INSTANCE_2:/home/ec2-user/ChatMRPT/app/web/routes/

# Restart service on Instance 2
ssh -i /tmp/chatmrpt-key2.pem ec2-user@$INSTANCE_2 << 'EOF'
    echo "🔄 Restarting ChatMRPT service..."
    sudo systemctl restart chatmrpt
    
    # Check service status
    echo "✅ Service status:"
    sudo systemctl status chatmrpt | grep Active
    
    # Check Ollama is running
    echo "🤖 Checking Ollama status..."
    curl -s http://localhost:11434/api/tags | jq -r '.models[].name' 2>/dev/null || echo "Ollama check failed"
EOF

# Clean up temp key
rm -f /tmp/chatmrpt-key2.pem

echo ""
echo "================================================"
echo "✅ Arena Model Fix Deployed Successfully!"
echo "================================================"
echo ""
echo "Fixed model mapping:"
echo "  - llama3.1:8b → llama3.1:8b ✓"
echo "  - mistral:7b → mistral:7b ✓"
echo "  - phi3:mini → phi3:mini ✓"
echo ""
echo "🧪 Test the fix at:"
echo "  https://d225ar6c86586s.cloudfront.net"
echo ""
echo "Ask a general question (without uploading data) to see Arena mode responses!"