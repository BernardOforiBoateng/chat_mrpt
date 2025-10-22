#!/bin/bash

# =====================================================
# Deploy Transition Configuration to Staging
# =====================================================
# Purpose: Deploy production-ready configuration to staging servers
# Date: August 27, 2025
# =====================================================

set -e

# Configuration
KEY_PATH="/tmp/chatmrpt-key2.pem"
INSTANCE1_IP="3.21.167.170"
INSTANCE2_IP="18.220.103.20"
CONFIG_FILE="app/config/production_transition.py"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "======================================================"
echo "   DEPLOYING TRANSITION CONFIGURATION"
echo "   $(date)"
echo "======================================================"
echo ""

# Function to deploy to instance
deploy_to_instance() {
    local ip=$1
    local name=$2
    
    echo -e "${YELLOW}Deploying to $name ($ip)...${NC}"
    
    # Copy configuration file
    echo "  Copying configuration file..."
    scp -i $KEY_PATH $CONFIG_FILE ec2-user@$ip:/home/ec2-user/ChatMRPT/app/config/ 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✅ Configuration file copied${NC}"
    else
        echo -e "  ${RED}❌ Failed to copy configuration${NC}"
        return 1
    fi
    
    # Update environment to use new config
    echo "  Updating environment configuration..."
    ssh -i $KEY_PATH ec2-user@$ip << 'EOF' 2>/dev/null
        cd /home/ec2-user/ChatMRPT
        
        # Backup current .env
        cp .env .env.backup_$(date +%Y%m%d_%H%M%S)
        
        # Check if FLASK_CONFIG is set to use transition config
        if ! grep -q "FLASK_CONFIG=production_transition" .env; then
            # Update or add FLASK_CONFIG
            if grep -q "^FLASK_CONFIG=" .env; then
                sed -i 's/^FLASK_CONFIG=.*/FLASK_CONFIG=production_transition/' .env
            else
                echo "FLASK_CONFIG=production_transition" >> .env
            fi
        fi
        
        # Ensure Redis URL is set
        if ! grep -q "^REDIS_URL=" .env; then
            echo "REDIS_URL=redis://chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com:6379/0" >> .env
        fi
        
        # Set production environment variables
        if ! grep -q "^FLASK_ENV=" .env; then
            echo "FLASK_ENV=production" >> .env
        else
            sed -i 's/^FLASK_ENV=.*/FLASK_ENV=production/' .env
        fi
        
        echo "Environment updated"
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✅ Environment configuration updated${NC}"
    else
        echo -e "  ${YELLOW}⚠️  Environment update had warnings${NC}"
    fi
    
    # Restart service
    echo "  Restarting ChatMRPT service..."
    ssh -i $KEY_PATH ec2-user@$ip 'sudo systemctl restart chatmrpt' 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "  ${GREEN}✅ Service restarted${NC}"
    else
        echo -e "  ${RED}❌ Failed to restart service${NC}"
        return 1
    fi
    
    # Wait for service to stabilize
    echo "  Waiting for service to stabilize..."
    sleep 5
    
    # Verify service is running
    SERVICE_STATUS=$(ssh -i $KEY_PATH ec2-user@$ip 'sudo systemctl is-active chatmrpt' 2>/dev/null || echo "inactive")
    
    if [ "$SERVICE_STATUS" = "active" ]; then
        echo -e "  ${GREEN}✅ Service is active${NC}"
    else
        echo -e "  ${RED}❌ Service is not active: $SERVICE_STATUS${NC}"
        return 1
    fi
    
    echo ""
    return 0
}

# Deploy to both instances
SUCCESS_COUNT=0

deploy_to_instance $INSTANCE1_IP "Instance 1"
if [ $? -eq 0 ]; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
fi

deploy_to_instance $INSTANCE2_IP "Instance 2"
if [ $? -eq 0 ]; then
    SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
fi

# Verify deployment
echo "======================================================"
echo "   DEPLOYMENT VERIFICATION"
echo "======================================================"

# Test health endpoints
echo "Testing health endpoints..."

HTTP1=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://$INSTANCE1_IP:5000/ping" 2>/dev/null || echo "000")
HTTP2=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://$INSTANCE2_IP:5000/ping" 2>/dev/null || echo "000")
ALB=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/ping" 2>/dev/null || echo "000")

echo ""
if [ "$HTTP1" = "200" ]; then
    echo -e "Instance 1 Health: ${GREEN}✅ OK${NC}"
else
    echo -e "Instance 1 Health: ${RED}❌ Failed (HTTP $HTTP1)${NC}"
fi

if [ "$HTTP2" = "200" ]; then
    echo -e "Instance 2 Health: ${GREEN}✅ OK${NC}"
else
    echo -e "Instance 2 Health: ${RED}❌ Failed (HTTP $HTTP2)${NC}"
fi

if [ "$ALB" = "200" ]; then
    echo -e "ALB Health:        ${GREEN}✅ OK${NC}"
else
    echo -e "ALB Health:        ${RED}❌ Failed (HTTP $ALB)${NC}"
fi

echo ""
echo "======================================================"

# Summary
if [ $SUCCESS_COUNT -eq 2 ]; then
    echo -e "${GREEN}✅ DEPLOYMENT SUCCESSFUL${NC}"
    echo "   Configuration deployed to both instances"
    echo "   Services are running with production settings"
    echo ""
    echo "Next steps:"
    echo "1. Monitor services using: ./monitor_transition.sh"
    echo "2. Set up CloudWatch alarms"
    echo "3. Test application functionality"
else
    echo -e "${YELLOW}⚠️  PARTIAL DEPLOYMENT${NC}"
    echo "   Only $SUCCESS_COUNT of 2 instances updated successfully"
    echo "   Review logs and retry failed instances"
fi

echo "======================================================"
echo "Deployment completed at $(date)"