#!/bin/bash
# Deploy TPR Integration to AWS Staging
# Date: 2025-08-12

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   TPR Integration Deployment to AWS    ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Configuration - Updated IPs as of Jan 7, 2025
STAGING_IPS=(
    "3.21.167.170"   # Instance 1 (was 18.117.115.217)
    "18.220.103.20"  # Instance 2
)

KEY_PATH="/tmp/chatmrpt-key-deploy.pem"
REMOTE_DIR="/home/ec2-user/ChatMRPT"

# Files to deploy for TPR integration
echo -e "${YELLOW}📦 Preparing files for deployment...${NC}"

# Create a deployment package
DEPLOY_DIR="/tmp/tpr_deploy_$(date +%s)"
mkdir -p $DEPLOY_DIR

# Copy TPR-specific files
echo "Copying TPR integration files..."

# Core TPR files
cp -r app/core/tpr_utils.py $DEPLOY_DIR/ 2>/dev/null || echo "tpr_utils.py"
mkdir -p $DEPLOY_DIR/app/core
cp app/core/tpr_utils.py $DEPLOY_DIR/app/core/

# Data Analysis V3 TPR tool
mkdir -p $DEPLOY_DIR/app/data_analysis_v3/tools
cp app/data_analysis_v3/tools/tpr_analysis_tool.py $DEPLOY_DIR/app/data_analysis_v3/tools/

# Updated agent with transition logic
mkdir -p $DEPLOY_DIR/app/data_analysis_v3/core
cp app/data_analysis_v3/core/agent.py $DEPLOY_DIR/app/data_analysis_v3/core/

# Updated prompts
mkdir -p $DEPLOY_DIR/app/data_analysis_v3/prompts
cp app/data_analysis_v3/prompts/system_prompt.py $DEPLOY_DIR/app/data_analysis_v3/prompts/

# Services updates
mkdir -p $DEPLOY_DIR/app/services
cp app/services/variable_extractor.py $DEPLOY_DIR/app/services/
cp app/services/shapefile_fetcher.py $DEPLOY_DIR/app/services/

# Config for AWS paths
mkdir -p $DEPLOY_DIR/app/config
cp app/config/data_paths.py $DEPLOY_DIR/app/config/

# Analysis updates for zone-specific variables
mkdir -p $DEPLOY_DIR/app/analysis
cp app/analysis/region_aware_selection.py $DEPLOY_DIR/app/analysis/ 2>/dev/null || true

echo -e "${GREEN}✅ Files prepared for deployment${NC}"

# Function to deploy to a single instance
deploy_to_instance() {
    local IP=$1
    local INSTANCE_NUM=$2
    
    echo -e "\n${YELLOW}🚀 Deploying to Instance $INSTANCE_NUM ($IP)...${NC}"
    
    # Test connection
    echo "Testing connection..."
    if ! ssh -o ConnectTimeout=10 -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$IP "echo 'Connected to $IP'" 2>/dev/null; then
        echo -e "${RED}❌ Cannot connect to $IP${NC}"
        return 1
    fi
    
    echo -e "${GREEN}✅ Connected to $IP${NC}"
    
    # Create backup
    echo "Creating backup on remote..."
    ssh -i $KEY_PATH ec2-user@$IP "cd $REMOTE_DIR && tar -czf backup_tpr_$(date +%Y%m%d_%H%M%S).tar.gz app/core/tpr_utils.py app/data_analysis_v3/tools/tpr_analysis_tool.py 2>/dev/null || true"
    
    # Copy files
    echo "Copying TPR integration files..."
    scp -r -i $KEY_PATH $DEPLOY_DIR/* ec2-user@$IP:$REMOTE_DIR/ 2>/dev/null
    
    # Set permissions
    echo "Setting permissions..."
    ssh -i $KEY_PATH ec2-user@$IP "cd $REMOTE_DIR && chmod -R 755 app/"
    
    # Restart service
    echo "Restarting ChatMRPT service..."
    ssh -i $KEY_PATH ec2-user@$IP "sudo systemctl restart chatmrpt"
    
    # Wait for service to start
    sleep 5
    
    # Check service status
    echo "Checking service status..."
    if ssh -i $KEY_PATH ec2-user@$IP "sudo systemctl is-active chatmrpt" | grep -q "active"; then
        echo -e "${GREEN}✅ Service running on Instance $INSTANCE_NUM${NC}"
        
        # Check for errors in logs
        echo "Checking recent logs..."
        ssh -i $KEY_PATH ec2-user@$IP "sudo journalctl -u chatmrpt -n 20 --no-pager | grep -i error || echo 'No errors in recent logs'"
    else
        echo -e "${RED}❌ Service failed on Instance $INSTANCE_NUM${NC}"
        ssh -i $KEY_PATH ec2-user@$IP "sudo journalctl -u chatmrpt -n 50 --no-pager"
        return 1
    fi
    
    return 0
}

# Deploy to all instances
FAILED_INSTANCES=()
SUCCESS_COUNT=0

for i in "${!STAGING_IPS[@]}"; do
    IP=${STAGING_IPS[$i]}
    INSTANCE_NUM=$((i + 1))
    
    if deploy_to_instance $IP $INSTANCE_NUM; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        FAILED_INSTANCES+=($IP)
    fi
done

# Clean up temp files
echo -e "\n${YELLOW}🧹 Cleaning up temporary files...${NC}"
rm -rf $DEPLOY_DIR

# Summary
echo -e "\n${BLUE}=========================================${NC}"
echo -e "${BLUE}         DEPLOYMENT SUMMARY              ${NC}"
echo -e "${BLUE}=========================================${NC}"

if [ ${#FAILED_INSTANCES[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ SUCCESS: Deployed to all ${#STAGING_IPS[@]} instances!${NC}"
    echo -e "\n${GREEN}TPR Integration Features Deployed:${NC}"
    echo "  ✅ TPR data detection"
    echo "  ✅ Interactive TPR calculation"
    echo "  ✅ Zone-specific variable extraction"
    echo "  ✅ Seamless transition to risk analysis"
    echo "  ✅ AWS-ready path configuration"
    
    echo -e "\n${YELLOW}📍 Access Points:${NC}"
    echo "  ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
    echo "  Instance 1: http://${STAGING_IPS[0]}"
    echo "  Instance 2: http://${STAGING_IPS[1]}"
    
    echo -e "\n${GREEN}🎯 Next Steps:${NC}"
    echo "  1. Test TPR upload through Data Analysis tab"
    echo "  2. Verify zone-specific variables are selected"
    echo "  3. Test transition from TPR to risk analysis"
    echo "  4. Monitor logs: ssh -i aws_files/chatmrpt-key.pem ec2-user@${STAGING_IPS[0]} 'sudo journalctl -u chatmrpt -f'"
else
    echo -e "${RED}⚠️ PARTIAL SUCCESS: Deployed to $SUCCESS_COUNT/${#STAGING_IPS[@]} instances${NC}"
    echo -e "${RED}Failed instances: ${FAILED_INSTANCES[@]}${NC}"
    echo -e "\n${YELLOW}Please check the failed instances manually${NC}"
fi

echo -e "\n${BLUE}=========================================${NC}"
echo -e "${GREEN}Deployment completed at $(date)${NC}"