#!/bin/bash
# Switch staging servers from Llama 3.1 to OpenAI GPT-4o

echo "🔄 Switching staging to OpenAI GPT-4o..."

# Staging server IPs (NEW as of Jan 7, 2025)
STAGING_IP1="3.21.167.170"
STAGING_IP2="18.220.103.20"

# Key path
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Check if key exists
if [ ! -f "$KEY_PATH" ]; then
    echo "❌ SSH key not found at $KEY_PATH"
    echo "Copying key..."
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
    chmod 600 /tmp/chatmrpt-key2.pem
fi

echo "📝 Creating configuration update script..."

# Create a script to update the configuration
cat > /tmp/switch_to_openai.sh << 'EOF'
#!/bin/bash

# Update .env to comment out VLLM and ensure OpenAI is active
cd /home/ec2-user/ChatMRPT

# Backup current .env
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# Comment out VLLM settings
sed -i 's/^VLLM_BASE_URL/#VLLM_BASE_URL/g' .env

# Ensure OpenAI key is not commented
sed -i 's/^#OPENAI_API_KEY/OPENAI_API_KEY/g' .env

# Add LLM backend setting if not present
if ! grep -q "^LLM_BACKEND=" .env; then
    echo "LLM_BACKEND=openai" >> .env
else
    sed -i 's/^LLM_BACKEND=.*/LLM_BACKEND=openai/g' .env
fi

# Update llm_manager.py to use gpt-4o by default
sed -i 's/model: str = "meta-llama\/Meta-Llama-3.1-8B-Instruct"/model: str = "gpt-4o"/g' app/core/llm_manager.py

# Update llm_adapter.py if it exists
if [ -f app/core/llm_adapter.py ]; then
    sed -i 's/backend = "vllm"/backend = "openai"/g' app/core/llm_adapter.py
    sed -i 's/default="vllm"/default="openai"/g' app/core/llm_adapter.py
fi

echo "✅ Configuration updated to use OpenAI GPT-4o"
EOF

# Deploy to both staging servers
for ip in $STAGING_IP1 $STAGING_IP2; do
    echo ""
    echo "🔧 Updating staging server: $ip"
    
    # Copy the script
    echo "  📋 Copying update script..."
    scp -i "$KEY_PATH" -o StrictHostKeyChecking=no /tmp/switch_to_openai.sh "ec2-user@$ip:/tmp/"
    
    # Execute the script
    echo "  🔄 Executing configuration update..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" "chmod +x /tmp/switch_to_openai.sh && /tmp/switch_to_openai.sh"
    
    # Restart service
    echo "  🔄 Restarting ChatMRPT service..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" "sudo systemctl restart chatmrpt"
    if [ $? -eq 0 ]; then
        echo "    ✅ Service restarted successfully"
    else
        echo "    ❌ Failed to restart service"
    fi
    
    # Verify the change
    echo "  📊 Verifying configuration..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" "grep -E 'LLM_BACKEND|VLLM_BASE_URL' /home/ec2-user/ChatMRPT/.env | head -5"
    
    # Check service logs
    echo "  📊 Checking service startup..."
    sleep 3
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" "sudo journalctl -u chatmrpt -n 20 --no-pager | grep -E '(LLM|model|gpt|openai)' | tail -5"
done

echo ""
echo "✅ Configuration switch complete!"
echo ""
echo "📝 Changes made:"
echo "1. Commented out VLLM_BASE_URL in .env"
echo "2. Set LLM_BACKEND=openai"
echo "3. Changed default model from Llama 3.1 to gpt-4o"
echo "4. Restarted ChatMRPT service on both servers"
echo ""
echo "🧪 Test at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "Expected behavior with GPT-4o:"
echo "1. Upload TPR file in Data Analysis tab"
echo "2. Complete TPR workflow"
echo "3. Say 'yes' to proceed"
echo "4. Ask 'Check data quality'"
echo "5. Should see ACTUAL tool execution with real data results"