#!/bin/bash
# Deploy proper environment configuration to AWS servers

echo "=== Deploying Environment Configuration ==="

KEY_PATH="/tmp/chatmrpt-key2.pem"

# Create .env file for production servers
cat > /tmp/production.env << 'EOF'
# Model Server Configuration - AWS Internal Communication
# GPU Instance Private DNS (auto-discovered by AWS)
OLLAMA_HOST=ip-172-31-45-157.us-east-2.compute.internal
OLLAMA_PORT=11434

# Fallback to private IP if DNS fails
# OLLAMA_HOST=172.31.45.157
EOF

# Deploy to both production instances
for ip in 3.21.167.170 18.220.103.20; do
    echo "Deploying to $ip..."
    
    # Copy environment config
    scp -i $KEY_PATH /tmp/production.env ec2-user@$ip:/tmp/
    
    # Append to existing .env file
    ssh -i $KEY_PATH ec2-user@$ip << 'REMOTE_EOF'
        # Backup existing .env
        cp /home/ec2-user/ChatMRPT/.env /home/ec2-user/ChatMRPT/.env.backup
        
        # Add model server config if not present
        if ! grep -q "OLLAMA_HOST" /home/ec2-user/ChatMRPT/.env; then
            echo "" >> /home/ec2-user/ChatMRPT/.env
            cat /tmp/production.env >> /home/ec2-user/ChatMRPT/.env
            echo "✅ Added Ollama configuration"
        else
            echo "⚠️ Ollama config already exists"
        fi
        
        # Restart service
        sudo systemctl restart chatmrpt
REMOTE_EOF
    
    echo "Done with $ip"
done

echo ""
echo "=== Configuration for GPU Instance ==="
echo "On the GPU instance (18.118.171.148), Ollama should be started with:"
echo "  OLLAMA_HOST=0.0.0.0 ollama serve"
echo ""
echo "This allows internal AWS communication without hardcoded IPs!"