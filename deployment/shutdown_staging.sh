#!/bin/bash

# Shutdown Staging Instances to Save Costs
# This script stops (not terminates) staging instances so they can be restarted if needed

set -e

echo "=== Shutting Down Staging Instances ==="
echo "This will STOP (not terminate) the staging instances to save costs"
echo "Instances can be restarted later if needed"

# Staging instance IDs
INSTANCE_1="i-0994615951d0b9563"  # ChatMRPT-Staging
INSTANCE_2="i-0f3b25b72f18a5037"  # chatmrpt-staging-2

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Confirm with user
echo -e "${YELLOW}This will stop the following staging instances:${NC}"
echo "  - Instance 1: $INSTANCE_1 (3.21.167.170)"
echo "  - Instance 2: $INSTANCE_2 (18.220.103.20)"
echo ""
read -p "Are you sure you want to stop staging instances? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo -e "${RED}Cancelled${NC}"
    exit 0
fi

# Stop instances using AWS CLI
echo -e "${YELLOW}Stopping staging instances...${NC}"

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo -e "${RED}AWS CLI is not installed. Please install it first.${NC}"
    echo "Install with: pip install awscli"
    exit 1
fi

# Stop Instance 1
echo "Stopping Instance 1 ($INSTANCE_1)..."
aws ec2 stop-instances --instance-ids $INSTANCE_1 --region us-east-2

# Stop Instance 2  
echo "Stopping Instance 2 ($INSTANCE_2)..."
aws ec2 stop-instances --instance-ids $INSTANCE_2 --region us-east-2

echo -e "${GREEN}✓ Staging instances are being stopped${NC}"
echo ""
echo "Cost savings:"
echo "  - 2 t3.medium instances: ~$60/month saved"
echo "  - Instances remain in 'stopped' state (no charges except EBS storage)"
echo ""
echo "To restart staging later, run:"
echo "  aws ec2 start-instances --instance-ids $INSTANCE_1 $INSTANCE_2 --region us-east-2"
echo ""
echo -e "${GREEN}=== Staging Shutdown Complete ===${NC}"