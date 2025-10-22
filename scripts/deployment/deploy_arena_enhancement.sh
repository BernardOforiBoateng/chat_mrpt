#!/bin/bash

# Deploy Arena Enhancement to AWS Production
# This script deploys the Arena multi-model interpretation enhancement

echo "========================================="
echo "Deploying Arena Enhancement to Production"
echo "========================================="

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
PRODUCTION_IPS="3.21.167.170 18.220.103.20"
REMOTE_USER="ec2-user"
REMOTE_PATH="/home/ec2-user/ChatMRPT"

# Files to deploy
ARENA_FILES=(
    "app/core/arena_data_context.py"
    "app/core/arena_prompt_builder.py"
    "app/core/arena_trigger_detector.py"
    "app/core/enhanced_arena_manager.py"
    "app/core/arena_integration_patch.py"
    "tests/test_arena_integration.py"
    "tasks/project_notes/arena_enhancement_implementation.md"
)

# Check if key exists
if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSH key not found at $KEY_PATH"
    echo "Copying key to /tmp..."
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

echo ""
echo "📦 Files to deploy:"
for file in "${ARENA_FILES[@]}"; do
    echo "  - $file"
done

echo ""
echo "🎯 Target instances:"
for ip in $PRODUCTION_IPS; do
    echo "  - $ip"
done

echo ""
echo "Starting deployment..."
echo ""

# Deploy to each production instance
for ip in $PRODUCTION_IPS; do
    echo "----------------------------------------"
    echo "Deploying to instance: $ip"
    echo "----------------------------------------"

    # Create backup on remote
    echo "Creating backup on remote..."
    ssh -i "$KEY_PATH" "$REMOTE_USER@$ip" "cd $REMOTE_PATH && tar -czf backups/pre_arena_$(date +%Y%m%d_%H%M%S).tar.gz app/core/*.py tests/*.py --ignore-failed-read 2>/dev/null || true"

    # Copy Arena enhancement files
    echo "Copying Arena enhancement files..."
    for file in "${ARENA_FILES[@]}"; do
        if [ -f "$file" ]; then
            echo "  Copying $file..."
            # Create directory if needed
            dir=$(dirname "$file")
            ssh -i "$KEY_PATH" "$REMOTE_USER@$ip" "mkdir -p $REMOTE_PATH/$dir"
            # Copy file
            scp -i "$KEY_PATH" "$file" "$REMOTE_USER@$ip:$REMOTE_PATH/$file"
        else
            echo "  ⚠️  Warning: $file not found locally"
        fi
    done

    # Test imports on remote
    echo "Testing Arena imports..."
    ssh -i "$KEY_PATH" "$REMOTE_USER@$ip" "cd $REMOTE_PATH && source chatmrpt_venv_new/bin/activate && python -c 'from app.core.arena_trigger_detector import ConversationalArenaTrigger; from app.core.arena_data_context import ArenaDataContextManager; print(\"✅ Arena imports successful\")' 2>&1"

    # Restart service
    echo "Restarting ChatMRPT service..."
    ssh -i "$KEY_PATH" "$REMOTE_USER@$ip" "sudo systemctl restart chatmrpt"

    # Wait for service to start
    sleep 3

    # Check service status
    echo "Checking service status..."
    ssh -i "$KEY_PATH" "$REMOTE_USER@$ip" "sudo systemctl status chatmrpt | head -n 5"

    echo "✅ Deployment to $ip completed"
    echo ""
done

echo "========================================="
echo "Arena Enhancement Deployment Complete!"
echo "========================================="
echo ""
echo "🔍 Next steps:"
echo "1. Test Arena triggers with: 'What does this mean?' after analysis"
echo "2. Check for automatic triggers on high-risk results"
echo "3. Verify model responses include data context"
echo "4. Monitor logs for Arena activation: sudo journalctl -u chatmrpt -f | grep Arena"
echo ""
echo "📊 To verify Arena is working:"
echo "- Upload test data and run analysis"
echo "- Ask 'Explain these results' - should trigger Arena"
echo "- Look for '🎯 Arena Analysis' in response"
echo "- Check for three model perspectives"
echo ""
echo "🌐 Access points:"
echo "- CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "- Direct ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"