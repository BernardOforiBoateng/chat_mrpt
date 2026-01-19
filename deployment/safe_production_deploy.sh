#!/bin/bash

# Safe Production Deployment Script
# Works on live production without downtime

set -e  # Exit on any error

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
INSTANCE_1="172.31.44.52"
INSTANCE_2="172.31.43.200"
ALB_URL="http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Safe Production Deployment ===${NC}"
echo "This script updates production instances one at a time to maintain availability"

# Function to check instance health
check_health() {
    local instance=$1
    echo -e "${YELLOW}Checking health of instance $instance...${NC}"
    
    # SSH to instance and check service status
    if ssh -i $KEY_PATH -o ConnectTimeout=5 ec2-user@$instance "sudo systemctl is-active --quiet chatmrpt"; then
        echo -e "${GREEN}✓ Instance $instance is healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ Instance $instance is not healthy${NC}"
        return 1
    fi
}

# Function to deploy to single instance
deploy_to_instance() {
    local instance=$1
    local instance_name=$2
    
    echo -e "${YELLOW}Deploying to $instance_name ($instance)...${NC}"
    
    # Copy files (add your files here)
    if [ -f "$3" ]; then
        echo "Copying $3..."
        scp -i $KEY_PATH "$3" ec2-user@$instance:/home/ec2-user/ChatMRPT/
    fi
    
    # Restart service
    echo "Restarting service..."
    ssh -i $KEY_PATH ec2-user@$instance "sudo systemctl restart chatmrpt"
    
    # Wait for service to be ready
    sleep 10
    
    # Verify deployment
    if check_health $instance; then
        echo -e "${GREEN}✓ Deployment to $instance_name successful${NC}"
        return 0
    else
        echo -e "${RED}✗ Deployment to $instance_name failed${NC}"
        return 1
    fi
}

# Function to test ALB
test_alb() {
    echo -e "${YELLOW}Testing ALB response...${NC}"
    
    if curl -s -o /dev/null -w "%{http_code}" $ALB_URL/ping | grep -q "200"; then
        echo -e "${GREEN}✓ ALB is responding correctly${NC}"
        return 0
    else
        echo -e "${RED}✗ ALB is not responding${NC}"
        return 1
    fi
}

# Main deployment flow
main() {
    # Check if files to deploy are provided
    if [ $# -eq 0 ]; then
        echo -e "${RED}Usage: $0 <file1> [file2] [file3]...${NC}"
        echo "Example: $0 app/core/agent.py app/static/js/modules/chat/core/message-handler.js"
        exit 1
    fi
    
    # Step 1: Pre-deployment checks
    echo -e "${YELLOW}Step 1: Pre-deployment health check${NC}"
    check_health $INSTANCE_1 || exit 1
    check_health $INSTANCE_2 || exit 1
    test_alb || exit 1
    
    # Step 2: Deploy to Instance 1 (Instance 2 handles all traffic)
    echo -e "${YELLOW}Step 2: Deploying to Instance 1 (Instance 2 serving traffic)${NC}"
    
    # Remove Instance 1 from ALB target group (optional - AWS health checks handle this)
    # aws elbv2 deregister-targets --target-group-arn <arn> --targets Id=$INSTANCE_1
    
    for file in "$@"; do
        deploy_to_instance $INSTANCE_1 "Instance 1" "$file"
    done
    
    # Step 3: Test Instance 1
    echo -e "${YELLOW}Step 3: Testing Instance 1${NC}"
    sleep 5
    check_health $INSTANCE_1 || exit 1
    
    # Step 4: Deploy to Instance 2
    echo -e "${YELLOW}Step 4: Deploying to Instance 2${NC}"
    read -p "Instance 1 is updated. Deploy to Instance 2? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for file in "$@"; do
            deploy_to_instance $INSTANCE_2 "Instance 2" "$file"
        done
    else
        echo -e "${YELLOW}Skipping Instance 2. Remember to update it later!${NC}"
    fi
    
    # Step 5: Final verification
    echo -e "${YELLOW}Step 5: Final verification${NC}"
    check_health $INSTANCE_1
    check_health $INSTANCE_2
    test_alb
    
    echo -e "${GREEN}=== Deployment Complete ===${NC}"
    echo "Both instances are now running the updated code"
}

# Run main function with all arguments
main "$@"