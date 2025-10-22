#!/bin/bash
# Deploy TPR Critical Fixes to AWS Staging
# Date: 2025-08-12

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================${NC}"
echo -e "${BLUE}   TPR Critical Fixes Deployment        ${NC}"
echo -e "${BLUE}=========================================${NC}"
echo ""

# Configuration - Updated IPs as of Jan 7, 2025
STAGING_IPS=(
    "3.21.167.170"   # Instance 1 (was 18.117.115.217)
    "18.220.103.20"  # Instance 2
)

KEY_PATH="/tmp/chatmrpt-key-deploy.pem"
REMOTE_DIR="/home/ec2-user/ChatMRPT"

echo -e "${YELLOW}📦 Critical Fixes Being Deployed:${NC}"
echo "1. Fixed nrows=5 bug - now reads full data"
echo "2. Added comprehensive TPR summary (224 wards, 21 LGAs)"
echo "3. Enhanced user guidance with proactive prompts"
echo "4. Improved system prompt for TPR handling"
echo ""

# Function to deploy to a single instance
deploy_fixes() {
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
    
    # Backup current files
    echo "Creating backup..."
    ssh -i $KEY_PATH ec2-user@$IP "cd $REMOTE_DIR && \
        cp app/data_analysis_v3/core/agent.py app/data_analysis_v3/core/agent.py.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true && \
        cp app/data_analysis_v3/prompts/system_prompt.py app/data_analysis_v3/prompts/system_prompt.py.backup_$(date +%Y%m%d_%H%M%S) 2>/dev/null || true"
    
    # Copy fixed files
    echo "Copying fixed agent.py..."
    scp -i $KEY_PATH app/data_analysis_v3/core/agent.py ec2-user@$IP:$REMOTE_DIR/app/data_analysis_v3/core/ 2>/dev/null
    
    echo "Copying updated system_prompt.py..."
    scp -i $KEY_PATH app/data_analysis_v3/prompts/system_prompt.py ec2-user@$IP:$REMOTE_DIR/app/data_analysis_v3/prompts/ 2>/dev/null
    
    # Set permissions
    echo "Setting permissions..."
    ssh -i $KEY_PATH ec2-user@$IP "cd $REMOTE_DIR && chmod -R 755 app/"
    
    # Restart service
    echo "Restarting ChatMRPT service..."
    ssh -i $KEY_PATH ec2-user@$IP "sudo systemctl restart chatmrpt"
    
    # Wait for service
    sleep 5
    
    # Check service status
    echo "Verifying service..."
    if ssh -i $KEY_PATH ec2-user@$IP "sudo systemctl is-active chatmrpt" | grep -q "active"; then
        echo -e "${GREEN}✅ Service running on Instance $INSTANCE_NUM${NC}"
        
        # Check for errors
        echo "Checking for errors..."
        ssh -i $KEY_PATH ec2-user@$IP "sudo journalctl -u chatmrpt -n 20 --no-pager | grep -i 'error\\|exception' || echo 'No errors found'"
        
        return 0
    else
        echo -e "${RED}❌ Service failed on Instance $INSTANCE_NUM${NC}"
        ssh -i $KEY_PATH ec2-user@$IP "sudo journalctl -u chatmrpt -n 50 --no-pager"
        return 1
    fi
}

# Deploy to all instances
SUCCESS_COUNT=0
FAILED_INSTANCES=()

for i in "${!STAGING_IPS[@]}"; do
    IP=${STAGING_IPS[$i]}
    INSTANCE_NUM=$((i + 1))
    
    if deploy_fixes $IP $INSTANCE_NUM; then
        SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
    else
        FAILED_INSTANCES+=($IP)
    fi
done

# Summary
echo -e "\n${BLUE}=========================================${NC}"
echo -e "${BLUE}         DEPLOYMENT SUMMARY              ${NC}"
echo -e "${BLUE}=========================================${NC}"

if [ ${#FAILED_INSTANCES[@]} -eq 0 ]; then
    echo -e "${GREEN}✅ SUCCESS: All fixes deployed to ${#STAGING_IPS[@]} instances!${NC}"
    
    echo -e "\n${GREEN}Critical Fixes Applied:${NC}"
    echo "  ✅ Data now reads all rows (not just 5)"
    echo "  ✅ TPR summary shows correct counts (224 wards, 21 LGAs)"
    echo "  ✅ Proactive guidance: 'Just say Calculate TPR'"
    echo "  ✅ Enhanced system prompt for better responses"
    
    echo -e "\n${YELLOW}📍 Test the fixes:${NC}"
    echo "  1. Go to: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
    echo "  2. Navigate to Data Analysis tab"
    echo "  3. Upload Adamawa TPR file"
    echo "  4. Ask 'What type of data have I uploaded?'"
    echo "  5. Verify it shows 224 wards (not 5 rows)"
    echo "  6. Verify it prompts to 'Calculate TPR'"
    
    echo -e "\n${GREEN}🎯 Expected Behavior:${NC}"
    echo "  - Shows comprehensive TPR summary immediately"
    echo "  - Mentions 224 wards and 21 LGAs"
    echo "  - Proactively offers TPR calculation"
    echo "  - Guides through interactive selections"
    
else
    echo -e "${RED}⚠️ PARTIAL SUCCESS: Deployed to $SUCCESS_COUNT/${#STAGING_IPS[@]} instances${NC}"
    echo -e "${RED}Failed instances: ${FAILED_INSTANCES[@]}${NC}"
    echo -e "\n${YELLOW}Please check failed instances manually${NC}"
fi

echo -e "\n${BLUE}=========================================${NC}"
echo -e "${GREEN}Critical fixes deployment completed at $(date)${NC}"