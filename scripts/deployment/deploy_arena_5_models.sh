#!/bin/bash

# Deploy Arena Mode expansion from 3 to 5 models

echo "========================================"
echo "🚀 Deploying Arena Mode 5-Model Expansion"
echo "========================================"

# Set variables
KEY_PATH="/tmp/chatmrpt-key2.pem"
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"

# Copy key if needed
if [ ! -f "$KEY_PATH" ]; then
    cp aws_files/chatmrpt-key.pem "$KEY_PATH"
    chmod 600 "$KEY_PATH"
fi

# Files to deploy
FILES=(
    "app/core/ollama_adapter.py"
    "app/core/arena_manager.py"
    "app/web/routes/arena_routes.py"
    "app/web/routes/analysis_routes.py"
)

echo ""
echo "📦 Files to deploy:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done

echo ""
echo "🎯 Target instances:"
echo "  - Instance 1: $INSTANCE_1"
echo "  - Instance 2: $INSTANCE_2"

# Deploy to both instances
for ip in "$INSTANCE_1" "$INSTANCE_2"; do
    echo ""
    echo "📍 Deploying to $ip..."
    
    # Copy files
    for file in "${FILES[@]}"; do
        filename=$(basename "$file")
        dirname=$(dirname "$file")
        echo "  Copying $filename..."
        
        # Create directory if needed
        ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" \
            "mkdir -p /home/ec2-user/ChatMRPT/$dirname" 2>/dev/null
        
        # Copy file
        scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$file" \
            "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            echo "    ✅ Success"
        else
            echo "    ❌ Failed"
        fi
    done
    
    # Restart service
    echo "  Restarting ChatMRPT service..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" "sudo systemctl restart chatmrpt" 2>/dev/null
    if [ $? -eq 0 ]; then
        echo "    ✅ Service restarted"
    else
        echo "    ❌ Failed to restart service"
    fi
done

echo ""
echo "========================================"
echo "✅ Code Deployment Complete!"
echo "========================================"
echo ""
echo "📋 Summary of changes:"
echo ""
echo "ARENA MODE EXPANSION (3 → 5 models):"
echo ""
echo "Previous models (3):"
echo "  1. llama3.1:8b (Meta)"
echo "  2. mistral:7b (Mistral AI)"
echo "  3. phi3:mini (Microsoft)"
echo ""
echo "New models added (2):"
echo "  4. gemma2:9b (Google)"
echo "  5. qwen2.5:7b (Alibaba)"
echo ""
echo "🔧 Files Updated:"
echo "  - ollama_adapter.py: Added model mappings"
echo "  - arena_manager.py: Added model configurations"
echo "  - arena_routes.py: Updated defaults to 5 models"
echo "  - analysis_routes.py: Added models to maps"
echo ""
echo "⚠️  IMPORTANT: Models must be installed on GPU instance!"
echo ""
echo "🚨 Next Step Required: Install the new models"
echo "   See install_arena_models.md for instructions"
echo ""
echo "⏱️  Wait 1-2 minutes for services to restart"
echo ""