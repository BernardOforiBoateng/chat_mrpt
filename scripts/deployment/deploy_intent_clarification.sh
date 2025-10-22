#!/bin/bash

# Deploy Intent Clarification System to Production AWS Instances
# This deploys the new interactive intent clarification system

echo "================================================"
echo "Deploying Intent Clarification System"
echo "================================================"
echo ""

# Production instances (formerly staging)
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"

# Key file location (copy to /tmp for security)
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

echo "📦 Deploying Backend Changes to Instance 1: $INSTANCE_1"
echo "------------------------------------------------"

# Copy backend files to Instance 1
scp -i /tmp/chatmrpt-key2.pem \
    app/core/intent_clarifier.py \
    ec2-user@$INSTANCE_1:/home/ec2-user/ChatMRPT/app/core/

scp -i /tmp/chatmrpt-key2.pem \
    app/web/routes/analysis_routes.py \
    ec2-user@$INSTANCE_1:/home/ec2-user/ChatMRPT/app/web/routes/

scp -i /tmp/chatmrpt-key2.pem \
    app/web/routes/arena_routes.py \
    ec2-user@$INSTANCE_1:/home/ec2-user/ChatMRPT/app/web/routes/

echo ""
echo "📦 Deploying Backend Changes to Instance 2: $INSTANCE_2"
echo "------------------------------------------------"

# Copy backend files to Instance 2
scp -i /tmp/chatmrpt-key2.pem \
    app/core/intent_clarifier.py \
    ec2-user@$INSTANCE_2:/home/ec2-user/ChatMRPT/app/core/

scp -i /tmp/chatmrpt-key2.pem \
    app/web/routes/analysis_routes.py \
    ec2-user@$INSTANCE_2:/home/ec2-user/ChatMRPT/app/web/routes/

scp -i /tmp/chatmrpt-key2.pem \
    app/web/routes/arena_routes.py \
    ec2-user@$INSTANCE_2:/home/ec2-user/ChatMRPT/app/web/routes/

echo ""
echo "🌐 Deploying React Frontend Changes"
echo "------------------------------------------------"

# Build React frontend
echo "Building React app..."
cd frontend
npm run build
cd ..

# Copy built React files to both instances
echo "Copying React build to Instance 1..."
scp -i /tmp/chatmrpt-key2.pem -r \
    frontend/dist/* \
    ec2-user@$INSTANCE_1:/home/ec2-user/ChatMRPT/app/static/react/

echo "Copying React build to Instance 2..."
scp -i /tmp/chatmrpt-key2.pem -r \
    frontend/dist/* \
    ec2-user@$INSTANCE_2:/home/ec2-user/ChatMRPT/app/static/react/

echo ""
echo "🔄 Restarting Services"
echo "------------------------------------------------"

# Restart service on Instance 1
ssh -i /tmp/chatmrpt-key2.pem ec2-user@$INSTANCE_1 << 'EOF'
    echo "Removing old HybridLLMRouter if exists..."
    rm -f /home/ec2-user/ChatMRPT/app/core/hybrid_llm_router.py
    
    echo "Restarting ChatMRPT service..."
    sudo systemctl restart chatmrpt
    
    # Check service status
    echo "Service status:"
    sudo systemctl status chatmrpt | grep Active
EOF

# Restart service on Instance 2
ssh -i /tmp/chatmrpt-key2.pem ec2-user@$INSTANCE_2 << 'EOF'
    echo "Removing old HybridLLMRouter if exists..."
    rm -f /home/ec2-user/ChatMRPT/app/core/hybrid_llm_router.py
    
    echo "Restarting ChatMRPT service..."
    sudo systemctl restart chatmrpt
    
    # Check service status
    echo "Service status:"
    sudo systemctl status chatmrpt | grep Active
EOF

# Clean up temp key
rm -f /tmp/chatmrpt-key2.pem

echo ""
echo "================================================"
echo "✅ Intent Clarification System Deployed!"
echo "================================================"
echo ""
echo "🧪 TEST SCENARIOS:"
echo ""
echo "1. Without data: 'What is malaria?' → Arena (3 models)"
echo "2. With data: 'Tell me about vulnerability' → Clarification prompt"
echo "3. With data: 'Calculate rankings' → Tools (direct)"
echo "4. With data: 'Explain PCA' → Clarification or Arena"
echo ""
echo "📍 Test at: https://d225ar6c86586s.cloudfront.net"
echo ""
echo "When you see a clarification prompt:"
echo "  - Click option 1 for analysis with tools"
echo "  - Click option 2 for general explanation with Arena"
echo ""