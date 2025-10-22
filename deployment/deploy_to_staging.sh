#!/bin/bash
# Deploy to staging environment (multiple instances behind ALB)
# This script ensures consistent deployment across all staging instances

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================="
echo "   ChatMRPT Staging Deployment Script   "
echo "========================================="
echo ""

# Configuration
STAGING_INSTANCES=(
    "3.21.167.170"   # Instance 1: i-0994615951d0b9563 (Public IP)
    "18.220.103.20"  # Instance 2: i-0f3b25b72f18a5037 (Public IP)
)
KEY_PATH="/tmp/chatmrpt-key2.pem"
APP_DIR="/home/ec2-user/ChatMRPT"
SERVICE_NAME="chatmrpt"

# Files to deploy (add or modify as needed)
FILES_TO_DEPLOY=(
    "app/"
    "run.py"
    "requirements.txt"
    "gunicorn_config.py"
    ".env"
)

# Function to check if instance is reachable
check_instance() {
    local ip=$1
    echo -e "${YELLOW}Checking connectivity to $ip...${NC}"
    
    if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$ip "echo 'Connected'" &>/dev/null; then
        echo -e "${GREEN}✓ Instance $ip is reachable${NC}"
        return 0
    else
        echo -e "${RED}✗ Cannot connect to instance $ip${NC}"
        return 1
    fi
}

# Function to deploy to a single instance
deploy_to_instance() {
    local ip=$1
    echo ""
    echo -e "${YELLOW}Deploying to instance: $ip${NC}"
    echo "----------------------------------------"
    
    # Create backup
    echo "Creating backup..."
    ssh -i $KEY_PATH ec2-user@$ip "cd $APP_DIR && tar -czf backup_$(date +%Y%m%d_%H%M%S).tar.gz app/ run.py requirements.txt gunicorn_config.py .env 2>/dev/null || true"
    
    # Copy files
    echo "Copying files..."
    for file in "${FILES_TO_DEPLOY[@]}"; do
        if [ -e "$file" ]; then
            echo "  - Copying $file"
            scp -r -i $KEY_PATH "$file" ec2-user@$ip:$APP_DIR/ 2>/dev/null
        fi
    done
    
    # Install dependencies if requirements.txt was updated
    if [[ " ${FILES_TO_DEPLOY[@]} " =~ " requirements.txt " ]]; then
        echo "Installing dependencies..."
        ssh -i $KEY_PATH ec2-user@$ip "cd $APP_DIR && source /home/ec2-user/chatmrpt_env/bin/activate && pip install -r requirements.txt"
    fi
    
    # Restart service
    echo "Restarting service..."
    ssh -i $KEY_PATH ec2-user@$ip "sudo systemctl restart $SERVICE_NAME"
    
    # Wait for service to start
    sleep 5
    
    # Check service status
    echo "Checking service status..."
    if ssh -i $KEY_PATH ec2-user@$ip "sudo systemctl is-active $SERVICE_NAME" &>/dev/null; then
        echo -e "${GREEN}✓ Service is running on $ip${NC}"
        
        # Test health endpoint
        if ssh -i $KEY_PATH ec2-user@$ip "curl -s http://localhost:8080/health | grep -q healthy"; then
            echo -e "${GREEN}✓ Health check passed on $ip${NC}"
            return 0
        else
            echo -e "${RED}✗ Health check failed on $ip${NC}"
            return 1
        fi
    else
        echo -e "${RED}✗ Service failed to start on $ip${NC}"
        return 1
    fi
}

# Function to check ALB target health
check_alb_health() {
    echo ""
    echo -e "${YELLOW}Checking ALB target health...${NC}"
    
    # Get target health from AWS
    aws elbv2 describe-target-health \
        --target-group-arn arn:aws:elasticloadbalancing:us-east-2:593543055880:targetgroup/chatmrpt-staging-targets/cfb375512f786bdb \
        --region us-east-2 \
        --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State]' \
        --output table
    
    # Test ALB endpoint
    echo ""
    echo "Testing ALB endpoint..."
    if curl -s http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/health | grep -q healthy; then
        echo -e "${GREEN}✓ ALB health check passed${NC}"
        return 0
    else
        echo -e "${RED}✗ ALB health check failed${NC}"
        return 1
    fi
}

# Main deployment process
main() {
    echo "Starting deployment to staging environment..."
    echo "Target instances: ${#STAGING_INSTANCES[@]}"
    echo ""
    
    # Check all instances are reachable
    all_reachable=true
    for ip in "${STAGING_INSTANCES[@]}"; do
        if ! check_instance "$ip"; then
            all_reachable=false
        fi
    done
    
    if [ "$all_reachable" = false ]; then
        echo -e "${RED}Error: Not all instances are reachable${NC}"
        echo "Please check instance status and try again"
        exit 1
    fi
    
    # Deploy to each instance
    failed_instances=()
    successful_instances=()
    
    for ip in "${STAGING_INSTANCES[@]}"; do
        if deploy_to_instance "$ip"; then
            successful_instances+=("$ip")
        else
            failed_instances+=("$ip")
        fi
    done
    
    # Summary
    echo ""
    echo "========================================="
    echo "         Deployment Summary              "
    echo "========================================="
    
    if [ ${#successful_instances[@]} -gt 0 ]; then
        echo -e "${GREEN}Successful deployments: ${#successful_instances[@]}${NC}"
        for ip in "${successful_instances[@]}"; do
            echo "  ✓ $ip"
        done
    fi
    
    if [ ${#failed_instances[@]} -gt 0 ]; then
        echo -e "${RED}Failed deployments: ${#failed_instances[@]}${NC}"
        for ip in "${failed_instances[@]}"; do
            echo "  ✗ $ip"
        done
    fi
    
    # Check ALB health
    echo ""
    check_alb_health
    
    # Final status
    echo ""
    if [ ${#failed_instances[@]} -eq 0 ]; then
        echo -e "${GREEN}✓ Deployment completed successfully!${NC}"
        echo "Staging URL: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
        exit 0
    else
        echo -e "${RED}✗ Deployment completed with errors${NC}"
        echo "Please check failed instances and retry"
        exit 1
    fi
}

# Run main function
main "$@"