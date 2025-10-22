#!/bin/bash

# AWS Cleanup Script - Clean up legacy code on production instances
# Production IPs: 3.21.167.170, 18.220.103.20

echo "=========================================="
echo "AWS Production Cleanup Script"
echo "=========================================="

# Copy key to temp location
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Function to clean up an instance
cleanup_instance() {
    local IP=$1
    local INSTANCE_NAME=$2
    
    echo ""
    echo "Cleaning up $INSTANCE_NAME ($IP)..."
    echo "=========================================="
    
    # Create cleanup commands
    cat << 'EOF' > /tmp/aws_cleanup_commands.sh
#!/bin/bash
cd /home/ec2-user/ChatMRPT

echo "=== Starting cleanup on $(hostname) ==="

# Create backup first
echo "Creating backup..."
mkdir -p backups
tar -czf backups/pre_cleanup_$(date +%Y%m%d_%H%M%S).tar.gz \
    --exclude=node_modules \
    --exclude=chatmrpt_venv* \
    --exclude=.git \
    --exclude=backups \
    . 2>/dev/null || echo "Backup in progress..."

# Create organized directories
echo "Creating organized structure..."
mkdir -p scripts/deployment scripts/checks scripts/fixes scripts/setup scripts/tests
mkdir -p legacy/vllm legacy/old_frontend legacy/arena legacy/misc

# Move vLLM files (no longer used - using Ollama)
echo "Moving vLLM files..."
find . -maxdepth 1 -name "*vllm*" -type f -exec mv {} legacy/vllm/ \; 2>/dev/null

# Move old Flask frontend
echo "Moving old Flask frontend..."
[ -d app/templates ] && mv app/templates legacy/old_frontend/ 2>/dev/null
[ -d app/static/archived_old_frontend ] && mv app/static/archived_old_frontend legacy/old_frontend/ 2>/dev/null
[ -d app/static/css ] && mv app/static/css legacy/old_frontend/ 2>/dev/null
[ -d app/static/js ] && mv app/static/js legacy/old_frontend/ 2>/dev/null

# Move duplicate arena implementations
echo "Moving duplicate arena files..."
[ -f app/core/arena_manager_memory_backup.py ] && mv app/core/arena_manager_memory_backup.py legacy/arena/ 2>/dev/null
[ -f app/core/arena_manager_redis.py ] && mv app/core/arena_manager_redis.py legacy/arena/ 2>/dev/null
[ -f app/core/arena_manager_redis_fixed.py ] && mv app/core/arena_manager_redis_fixed.py legacy/arena/ 2>/dev/null
[ -f arena_manager_update.py ] && mv arena_manager_update.py legacy/arena/ 2>/dev/null

# Organize scripts
echo "Organizing scripts..."
mv deploy_*.sh scripts/deployment/ 2>/dev/null
mv check_*.sh scripts/checks/ 2>/dev/null
mv fix_*.sh scripts/fixes/ 2>/dev/null
mv setup_*.sh scripts/setup/ 2>/dev/null
mv test_*.py test_*.sh test_*.html scripts/tests/ 2>/dev/null

# Move misc files
echo "Moving misc files..."
mv *.html *.mhtml Procfile render.yaml docker-compose.yml apt-packages legacy/misc/ 2>/dev/null

# Update .env to remove vLLM references
echo "Updating .env configuration..."
if [ -f .env ]; then
    # Remove vLLM lines
    sed -i '/VLLM_HOST=/d' .env
    sed -i '/VLLM_PORT=/d' .env
    sed -i '/VLLM_BASE_URL=/d' .env
    sed -i '/VLLM_SECONDARY_URL=/d' .env
    
    # Update arena models to Ollama models
    sed -i 's/ARENA_MODELS=.*/ARENA_MODELS=llama3.1:8b,mistral:7b,phi3:mini/' .env
fi

# Count cleanup results
echo ""
echo "=== Cleanup Results ==="
echo "Scripts in root before: $(find . -maxdepth 1 -name "*.sh" -o -name "*.py" 2>/dev/null | wc -l)"
echo "Scripts organized to: scripts/*"
echo "Legacy files moved to: legacy/*"
echo ""
echo "Directories in legacy:"
ls -la legacy/ 2>/dev/null || echo "No legacy directory created"
echo ""
echo "Current root directory (first 20 items):"
ls -1 | head -20

echo "=== Cleanup complete on $(hostname) ==="
EOF

    # Copy and execute cleanup script
    scp -i /tmp/chatmrpt-key2.pem /tmp/aws_cleanup_commands.sh ec2-user@$IP:/tmp/
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP 'bash /tmp/aws_cleanup_commands.sh'
    
    # Restart service
    echo "Restarting ChatMRPT service..."
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$IP 'sudo systemctl restart chatmrpt'
    
    echo "✅ Cleanup complete for $INSTANCE_NAME"
}

# Clean up both production instances
cleanup_instance "3.21.167.170" "Production Instance 1"
cleanup_instance "18.220.103.20" "Production Instance 2"

echo ""
echo "=========================================="
echo "✅ AWS Cleanup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify services are running: curl http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/ping"
echo "2. Check CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "3. Test arena functionality with Ollama"

# Clean up temp files
rm -f /tmp/chatmrpt-key2.pem /tmp/aws_cleanup_commands.sh