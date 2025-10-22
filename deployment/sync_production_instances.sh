#!/bin/bash
#==============================================================================
# Production Instance Synchronization Script
# Ensures both production instances have identical environments
#==============================================================================

# Configuration
INSTANCE_1="3.21.167.170"  # Primary instance
INSTANCE_2="18.220.103.20"  # Secondary instance
KEY_PATH="~/.ssh/chatmrpt-key.pem"
VENV_PATH="/home/ec2-user/chatmrpt_env"
APP_PATH="/home/ec2-user/ChatMRPT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Production Instance Synchronization${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Function to check instance health
check_instance() {
    local ip=$1
    echo -e "${YELLOW}Checking instance $ip...${NC}"
    
    if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$ip "echo 'Connected'" &>/dev/null; then
        echo -e "${GREEN}✓ Instance $ip is accessible${NC}"
        return 0
    else
        echo -e "${RED}✗ Cannot connect to instance $ip${NC}"
        return 1
    fi
}

# Function to sync Python packages
sync_packages() {
    echo ""
    echo -e "${YELLOW}Synchronizing Python packages...${NC}"
    
    # Export packages from primary instance
    echo "Exporting package list from $INSTANCE_1..."
    ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$INSTANCE_1 \
        "$VENV_PATH/bin/pip freeze > /tmp/requirements_sync.txt"
    
    # Copy to secondary instance
    scp -o StrictHostKeyChecking=no -i $KEY_PATH \
        ec2-user@$INSTANCE_1:/tmp/requirements_sync.txt \
        ec2-user@$INSTANCE_2:/tmp/requirements_sync.txt
    
    # Install on secondary instance
    echo "Installing packages on $INSTANCE_2..."
    ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$INSTANCE_2 "
        $VENV_PATH/bin/pip install -r /tmp/requirements_sync.txt --quiet
    "
    
    echo -e "${GREEN}✓ Package synchronization complete${NC}"
}

# Function to sync application files
sync_files() {
    echo ""
    echo -e "${YELLOW}Synchronizing application files...${NC}"
    
    # Create tar of application files
    ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$INSTANCE_1 "
        cd $APP_PATH
        tar czf /tmp/app_sync.tar.gz \
            app/ \
            requirements.txt \
            gunicorn_config.py \
            run.py \
            .env \
            --exclude='*.pyc' \
            --exclude='__pycache__' \
            --exclude='instance/*'
    "
    
    # Transfer to secondary instance
    scp -o StrictHostKeyChecking=no -i $KEY_PATH \
        ec2-user@$INSTANCE_1:/tmp/app_sync.tar.gz \
        ec2-user@$INSTANCE_2:/tmp/app_sync.tar.gz
    
    # Extract on secondary instance
    ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$INSTANCE_2 "
        cd $APP_PATH
        # Backup current files
        mkdir -p backups
        cp -r app backups/app_\$(date +%Y%m%d_%H%M%S)
        
        # Extract new files
        tar xzf /tmp/app_sync.tar.gz
    "
    
    echo -e "${GREEN}✓ File synchronization complete${NC}"
}

# Function to restart services
restart_services() {
    echo ""
    echo -e "${YELLOW}Restarting services...${NC}"
    
    for ip in $INSTANCE_1 $INSTANCE_2; do
        echo "Restarting service on $ip..."
        ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$ip \
            "sudo systemctl restart chatmrpt"
    done
    
    echo -e "${GREEN}✓ Services restarted${NC}"
}

# Function to verify synchronization
verify_sync() {
    echo ""
    echo -e "${YELLOW}Verifying synchronization...${NC}"
    
    # Compare package counts
    count1=$(ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$INSTANCE_1 \
        "$VENV_PATH/bin/pip list | wc -l")
    count2=$(ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$INSTANCE_2 \
        "$VENV_PATH/bin/pip list | wc -l")
    
    echo "Instance $INSTANCE_1: $count1 packages"
    echo "Instance $INSTANCE_2: $count2 packages"
    
    if [ "$count1" -eq "$count2" ]; then
        echo -e "${GREEN}✓ Package counts match${NC}"
    else
        echo -e "${RED}✗ Package count mismatch!${NC}"
        return 1
    fi
    
    # Test LLM manager on both instances
    for ip in $INSTANCE_1 $INSTANCE_2; do
        echo ""
        echo "Testing LLM manager on $ip..."
        result=$(ssh -o StrictHostKeyChecking=no -i $KEY_PATH ec2-user@$ip "
            cd $APP_PATH
            $VENV_PATH/bin/python -c \"
import sys
sys.path.insert(0, '.')
try:
    from app.core.llm_adapter import LLMAdapter
    adapter = LLMAdapter(backend='openai')
    print('SUCCESS')
except Exception as e:
    print('FAILED')
\" 2>/dev/null
        ")
        
        if [ "$result" == "SUCCESS" ]; then
            echo -e "${GREEN}✓ LLM manager works on $ip${NC}"
        else
            echo -e "${RED}✗ LLM manager failed on $ip${NC}"
            return 1
        fi
    done
    
    echo ""
    echo -e "${GREEN}✓ All verification checks passed${NC}"
    return 0
}

# Main execution
main() {
    echo "Starting synchronization process..."
    echo ""
    
    # Check both instances are accessible
    if ! check_instance $INSTANCE_1 || ! check_instance $INSTANCE_2; then
        echo -e "${RED}Cannot proceed - instances not accessible${NC}"
        exit 1
    fi
    
    # Ask for confirmation
    echo ""
    echo -e "${YELLOW}This will sync Instance 2 ($INSTANCE_2) with Instance 1 ($INSTANCE_1)${NC}"
    read -p "Continue? (y/n) " -n 1 -r
    echo ""
    
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 1
    fi
    
    # Perform synchronization
    sync_packages
    sync_files
    restart_services
    
    # Wait for services to start
    echo ""
    echo "Waiting 10 seconds for services to start..."
    sleep 10
    
    # Verify synchronization
    if verify_sync; then
        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}✅ SYNCHRONIZATION SUCCESSFUL!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo "Both production instances are now synchronized and working identically."
    else
        echo ""
        echo -e "${RED}========================================${NC}"
        echo -e "${RED}⚠️ SYNCHRONIZATION COMPLETED WITH WARNINGS${NC}"
        echo -e "${RED}========================================${NC}"
        echo ""
        echo "Please check the errors above and run verification manually."
    fi
}

# Run main function
main