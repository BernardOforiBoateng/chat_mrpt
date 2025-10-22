#!/bin/bash

# Deploy Redis State Manager Integration to Production
# This ensures proper multi-worker state synchronization

echo "==================================="
echo "Deploying Redis Integration Fix"
echo "==================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Files to deploy
FILES=(
    "app/tools/complete_analysis_tools.py"
    "app/tools/itn_planning_tools.py"
    "app/core/redis_state_manager.py"
)

echo -e "${YELLOW}Files to deploy:${NC}"
for file in "${FILES[@]}"; do
    echo "  - $file"
done
echo ""

# Production instances (both behind ALB)
PRODUCTION_IPS=(
    "172.31.44.52"   # Instance 1
    "172.31.43.200"  # Instance 2
)

# SSH key location
KEY_FILE="/tmp/chatmrpt-key2.pem"

# Check if key exists
if [ ! -f "$KEY_FILE" ]; then
    # Try alternate location
    if [ -f "aws_files/chatmrpt-key.pem" ]; then
        cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
        chmod 600 /tmp/chatmrpt-key2.pem
        KEY_FILE="/tmp/chatmrpt-key2.pem"
    else
        echo -e "${RED}Error: SSH key not found${NC}"
        echo "Please ensure the key file exists at aws_files/chatmrpt-key.pem"
        exit 1
    fi
fi

echo -e "${GREEN}Using SSH key: $KEY_FILE${NC}"
echo ""

# Deploy to staging first for testing
echo -e "${YELLOW}Deploying to STAGING first for testing...${NC}"
STAGING_IPS=(
    "3.21.167.170"   # Staging Instance 1 (NEW IP as of Jan 7, 2025)
    "18.220.103.20"  # Staging Instance 2
)

for ip in "${STAGING_IPS[@]}"; do
    echo -e "${YELLOW}Deploying to staging instance: $ip${NC}"
    
    # Copy files
    for file in "${FILES[@]}"; do
        echo "  Copying $file..."
        scp -i "$KEY_FILE" "$file" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file"
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to copy $file to $ip${NC}"
            exit 1
        fi
    done
    
    # Restart service
    echo "  Restarting service..."
    ssh -i "$KEY_FILE" "ec2-user@$ip" "sudo systemctl restart chatmrpt"
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to restart service on $ip${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✓ Successfully deployed to staging: $ip${NC}"
done

echo ""
echo -e "${GREEN}Staging deployment complete!${NC}"
echo ""

# Test staging
echo -e "${YELLOW}Testing staging deployment...${NC}"
STAGING_ALB="http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
curl -s -o /dev/null -w "%{http_code}" "$STAGING_ALB/ping" | grep -q "200"
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Staging health check passed${NC}"
else
    echo -e "${YELLOW}⚠ Staging health check failed (may need a moment to restart)${NC}"
fi

echo ""
read -p "Deploy to PRODUCTION? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Production deployment cancelled."
    exit 0
fi

echo ""
echo -e "${YELLOW}Deploying to PRODUCTION...${NC}"

# Deploy to production through staging jump host
STAGING_JUMP="3.21.167.170"

for prod_ip in "${PRODUCTION_IPS[@]}"; do
    echo -e "${YELLOW}Deploying to production instance: $prod_ip (via staging)${NC}"
    
    # First, copy files to staging
    for file in "${FILES[@]}"; do
        echo "  Stage 1: Copying $file to staging..."
        scp -i "$KEY_FILE" "$file" "ec2-user@$STAGING_JUMP:/tmp/$(basename $file)"
        if [ $? -ne 0 ]; then
            echo -e "${RED}Failed to stage $file${NC}"
            exit 1
        fi
    done
    
    # Then copy from staging to production
    echo "  Stage 2: Copying files from staging to production..."
    ssh -i "$KEY_FILE" "ec2-user@$STAGING_JUMP" "
        for file in ${FILES[@]}; do
            filename=\$(basename \$file)
            scp -i ~/.ssh/chatmrpt-key.pem /tmp/\$filename ec2-user@$prod_ip:/home/ec2-user/ChatMRPT/\$file
        done
        ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$prod_ip 'sudo systemctl restart chatmrpt'
    "
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Successfully deployed to production: $prod_ip${NC}"
    else
        echo -e "${RED}Failed to deploy to production: $prod_ip${NC}"
        exit 1
    fi
done

echo ""
echo -e "${GREEN}==================================="
echo "Deployment Complete!"
echo "===================================${NC}"
echo ""
echo "Redis integration has been deployed to:"
echo "  - Staging: 2 instances"
echo "  - Production: 2 instances"
echo ""
echo -e "${YELLOW}What this fixes:${NC}"
echo "  ✓ Analysis no longer re-runs when requesting ITN planning"
echo "  ✓ Workers now share state through Redis"
echo "  ✓ Consistent behavior across all instances"
echo ""
echo -e "${GREEN}Testing the fix:${NC}"
echo "1. Upload data and run analysis"
echo "2. Ask for bed net planning"
echo "3. Verify analysis doesn't re-run"
echo ""
echo -e "${YELLOW}Production URL:${NC} https://d225ar6c86586s.cloudfront.net"