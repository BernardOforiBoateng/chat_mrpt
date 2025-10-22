#!/bin/bash

# Deploy TPR One-Tool Pattern to Staging
# Staging has 2 instances behind ALB that need updates

echo "========================================"
echo "Deploying TPR One-Tool Pattern to Staging"
echo "========================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
STAGING_IPS=("172.31.46.84" "172.31.24.195")
USER="ec2-user"
REMOTE_PATH="/home/ec2-user/ChatMRPT"

# Files to deploy
TPR_FILES=(
    "app/tpr_module/conversation.py"
    "app/tpr_module/integration/llm_tpr_handler.py"
    "app/tpr_module/prompts.py"
    "app/tpr_module/sandbox.py"
    "tasks/todo.md"
)

# Copy key file if not exists
if [ ! -f "$KEY_PATH" ]; then
    echo -e "${YELLOW}Copying SSH key...${NC}"
    cp aws_files/chatmrpt-key.pem $KEY_PATH
    chmod 600 $KEY_PATH
fi

# Function to deploy to a single instance
deploy_to_instance() {
    local ip=$1
    local instance_num=$2
    
    echo -e "\n${YELLOW}Deploying to Staging Instance $instance_num ($ip)...${NC}"
    
    # Copy files
    echo "Copying TPR module files..."
    for file in "${TPR_FILES[@]}"; do
        echo "  - Copying $file"
        scp -i $KEY_PATH -o StrictHostKeyChecking=no \
            "$file" \
            "$USER@$ip:$REMOTE_PATH/$file" || {
                echo -e "${RED}Failed to copy $file to $ip${NC}"
                return 1
            }
    done
    
    # Restart service
    echo "Restarting ChatMRPT service..."
    ssh -i $KEY_PATH -o StrictHostKeyChecking=no $USER@$ip << 'EOF'
        # Restart the service
        sudo systemctl restart chatmrpt
        
        # Check if service is running
        sleep 3
        if sudo systemctl is-active --quiet chatmrpt; then
            echo "✅ Service restarted successfully"
            
            # Show worker count
            WORKERS=$(ps aux | grep gunicorn | grep -v grep | wc -l)
            echo "Workers running: $WORKERS"
        else
            echo "❌ Service failed to start"
            sudo journalctl -u chatmrpt -n 20 --no-pager
            exit 1
        fi
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Instance $instance_num deployed successfully${NC}"
        return 0
    else
        echo -e "${RED}❌ Instance $instance_num deployment failed${NC}"
        return 1
    fi
}

# Deploy to all staging instances
echo -e "\n${YELLOW}Starting deployment to all staging instances...${NC}"

SUCCESS_COUNT=0
FAIL_COUNT=0

for i in "${!STAGING_IPS[@]}"; do
    deploy_to_instance "${STAGING_IPS[$i]}" $((i+1))
    if [ $? -eq 0 ]; then
        ((SUCCESS_COUNT++))
    else
        ((FAIL_COUNT++))
    fi
done

# Summary
echo -e "\n========================================"
echo -e "${YELLOW}Deployment Summary:${NC}"
echo -e "${GREEN}✅ Successful: $SUCCESS_COUNT instances${NC}"
if [ $FAIL_COUNT -gt 0 ]; then
    echo -e "${RED}❌ Failed: $FAIL_COUNT instances${NC}"
fi
echo "========================================"

# Test endpoints
if [ $SUCCESS_COUNT -gt 0 ]; then
    echo -e "\n${YELLOW}Testing staging endpoints...${NC}"
    
    # Test ALB endpoint
    ALB_URL="http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
    
    echo "Testing ALB health check..."
    response=$(curl -s -o /dev/null -w "%{http_code}" "$ALB_URL/ping")
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ ALB health check passed${NC}"
    else
        echo -e "${RED}❌ ALB health check failed (HTTP $response)${NC}"
    fi
    
    echo -e "\n${GREEN}Deployment complete!${NC}"
    echo "Access staging at: $ALB_URL"
    echo ""
    echo "To test TPR with local model:"
    echo "1. Upload a TPR file (Excel/CSV)"
    echo "2. System will use Ollama for processing"
    echo "3. Test the one-tool pattern interactions"
else
    echo -e "\n${RED}Deployment failed on all instances!${NC}"
    exit 1
fi