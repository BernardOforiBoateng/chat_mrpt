#!/bin/bash

# Deploy Progressive Arena System to AWS Production Instances
# This script deploys the new progressive battle functionality to all production instances

echo "================================================"
echo "Deploying Progressive Arena System to AWS"
echo "================================================"

# Copy SSH key to /tmp for proper permissions
echo "Setting up SSH key..."
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key.pem
chmod 600 /tmp/chatmrpt-key.pem

# Production Instance IPs (from CLAUDE.md)
INSTANCE1_IP="3.21.167.170"
INSTANCE2_IP="18.220.103.20"

# Files to deploy
FILES_TO_DEPLOY="
app/core/arena_manager.py
app/core/ollama_adapter.py
app/web/routes/arena_routes.py
test_progressive_arena.py
setup_ollama_models.sh
.env.ollama.example
"

echo ""
echo "Deploying to Production Instance 1 ($INSTANCE1_IP)..."
echo "================================================"

# Deploy to Instance 1
for file in $FILES_TO_DEPLOY; do
    echo "Copying $file..."
    scp -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no \
        "$file" "ec2-user@$INSTANCE1_IP:/home/ec2-user/ChatMRPT/$file" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ $file deployed"
    else
        echo "⚠️  Failed to deploy $file"
    fi
done

echo ""
echo "Deploying to Production Instance 2 ($INSTANCE2_IP)..."
echo "================================================"

# Deploy to Instance 2
for file in $FILES_TO_DEPLOY; do
    echo "Copying $file..."
    scp -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no \
        "$file" "ec2-user@$INSTANCE2_IP:/home/ec2-user/ChatMRPT/$file" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "✅ $file deployed"
    else
        echo "⚠️  Failed to deploy $file"
    fi
done

echo ""
echo "Restarting services on both instances..."
echo "================================================"

# Restart services on Instance 1
echo "Restarting Instance 1..."
ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    "ec2-user@$INSTANCE1_IP" "sudo systemctl restart chatmrpt" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Instance 1 restarted"
else
    echo "⚠️  Failed to restart Instance 1"
fi

# Restart services on Instance 2
echo "Restarting Instance 2..."
ssh -i /tmp/chatmrpt-key.pem -o StrictHostKeyChecking=no \
    "ec2-user@$INSTANCE2_IP" "sudo systemctl restart chatmrpt" 2>/dev/null
if [ $? -eq 0 ]; then
    echo "✅ Instance 2 restarted"
else
    echo "⚠️  Failed to restart Instance 2"
fi

echo ""
echo "================================================"
echo "Deployment Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "1. SSH into one of the instances to set up Ollama models:"
echo "   ssh -i /tmp/chatmrpt-key.pem ec2-user@$INSTANCE1_IP"
echo ""
echo "2. Once connected, run the setup script:"
echo "   cd /home/ec2-user/ChatMRPT"
echo "   chmod +x setup_ollama_models.sh"
echo "   ./setup_ollama_models.sh"
echo ""
echo "3. Test the progressive arena:"
echo "   python test_progressive_arena.py"
echo ""
echo "4. Access the arena via CloudFront:"
echo "   https://d225ar6c86586s.cloudfront.net"