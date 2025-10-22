#!/bin/bash

echo "=== Complete Staging to Production Sync ==="
echo "Syncing ALL files from staging to production instances..."

# Production instances (private IPs from within VPC)
PROD_INSTANCES=("172.31.44.52" "172.31.43.200")

# Staging instance
STAGING_IP="3.21.167.170"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Starting complete sync from staging to production...${NC}"

# First, create a full backup on staging
echo -e "${YELLOW}Creating backup on staging...${NC}"
ssh -i /tmp/chatmrpt-key2.pem ec2-user@${STAGING_IP} "cd /home/ec2-user && tar -czf ChatMRPT_backup_$(date +%Y%m%d_%H%M%S).tar.gz ChatMRPT/"

# For each production instance
for PROD_IP in "${PROD_INSTANCES[@]}"; do
    echo -e "${YELLOW}Syncing to production instance: ${PROD_IP}${NC}"
    
    # SSH through staging to reach production (they're in same VPC)
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@${STAGING_IP} << INNER_EOF
        echo "Connecting to production ${PROD_IP}..."
        
        # Use rsync to sync entire ChatMRPT directory
        rsync -avz --delete \
            --exclude='instance/uploads/*' \
            --exclude='instance/*.db' \
            --exclude='instance/app.log' \
            --exclude='__pycache__' \
            --exclude='*.pyc' \
            --exclude='.git' \
            --exclude='venv/' \
            --exclude='.env' \
            /home/ec2-user/ChatMRPT/ \
            ec2-user@${PROD_IP}:/home/ec2-user/ChatMRPT/
        
        if [ \$? -eq 0 ]; then
            echo "✅ Sync completed for ${PROD_IP}"
            
            # Copy .env file separately (without overwriting existing settings)
            echo "Updating environment variables..."
            ssh ec2-user@${PROD_IP} "cd /home/ec2-user/ChatMRPT && cp .env .env.backup_$(date +%Y%m%d_%H%M%S)"
            
            # Restart the service
            echo "Restarting ChatMRPT service..."
            ssh ec2-user@${PROD_IP} "sudo systemctl restart chatmrpt"
            
            # Check service status
            sleep 5
            ssh ec2-user@${PROD_IP} "sudo systemctl status chatmrpt --no-pager | head -10"
        else
            echo "❌ Sync failed for ${PROD_IP}"
        fi
INNER_EOF
    
    echo -e "${GREEN}Completed sync for ${PROD_IP}${NC}"
    echo "---"
done

echo -e "${GREEN}=== Complete Sync Finished ===${NC}"
echo "Testing production endpoints..."

# Test the load balancer
echo "Testing production ALB..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/ping

echo -e "${GREEN}Sync complete! Both production instances updated.${NC}"
