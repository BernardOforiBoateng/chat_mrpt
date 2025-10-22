#!/bin/bash
#==============================================================================
# Deploy Arena Tournament Fix to Production
# Deploys the tournament-style Arena implementation to both production instances
#==============================================================================

# Configuration
INSTANCE_1="3.21.167.170"  # Production instance 1
INSTANCE_2="18.220.103.20"  # Production instance 2
KEY_FILE="/tmp/chatmrpt-key2.pem"
APP_PATH="/home/ec2-user/ChatMRPT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Arena Tournament Fix Deployment${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# Prepare key file
echo -e "${YELLOW}Preparing SSH key...${NC}"
if [ ! -f "$KEY_FILE" ]; then
    cp aws_files/chatmrpt-key.pem $KEY_FILE
    chmod 600 $KEY_FILE
fi

# Files to deploy
BACKEND_FILES=(
    "app/web/routes/analysis_routes.py"
    "app/web/routes/arena_routes.py"
    "app/core/arena_manager.py"
    "app/core/llm_adapter.py"
)

FRONTEND_FILES=(
    "frontend/src/types/index.ts"
    "frontend/src/stores/chatStore.ts"
    "frontend/src/components/Chat/ArenaMessage.tsx"
    "frontend/src/hooks/useMessageStreaming.ts"
    "app/static/react"
)

# Function to deploy to an instance
deploy_to_instance() {
    local IP=$1
    echo ""
    echo -e "${YELLOW}Deploying to instance $IP...${NC}"
    
    # Copy backend files
    echo "Copying backend files..."
    for file in "${BACKEND_FILES[@]}"; do
        scp -o StrictHostKeyChecking=no -i $KEY_FILE "$file" "ec2-user@$IP:$APP_PATH/$file" 2>/dev/null
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ $file${NC}"
        else
            echo -e "${RED}✗ $file${NC}"
        fi
    done
    
    # Copy frontend files
    echo "Copying frontend files..."
    for file in "${FRONTEND_FILES[@]}"; do
        if [ -d "$file" ]; then
            # Directory - use rsync for React build
            rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no -i $KEY_FILE" \
                "$file/" "ec2-user@$IP:$APP_PATH/$file/" 2>/dev/null
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓ $file${NC}"
            else
                echo -e "${RED}✗ $file${NC}"
            fi
        else
            # Regular file
            scp -o StrictHostKeyChecking=no -i $KEY_FILE "$file" "ec2-user@$IP:$APP_PATH/$file" 2>/dev/null
            if [ $? -eq 0 ]; then
                echo -e "${GREEN}✓ $file${NC}"
            else
                echo -e "${RED}✗ $file${NC}"
            fi
        fi
    done
    
    # Restart the service
    echo "Restarting ChatMRPT service..."
    ssh -o StrictHostKeyChecking=no -i $KEY_FILE ec2-user@$IP "sudo systemctl restart chatmrpt"
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Service restarted${NC}"
    else
        echo -e "${RED}✗ Failed to restart service${NC}"
    fi
    
    # Check service status
    echo "Checking service status..."
    ssh -o StrictHostKeyChecking=no -i $KEY_FILE ec2-user@$IP "sudo systemctl is-active chatmrpt"
}

# Deploy to both instances
echo -e "${GREEN}Starting deployment to both production instances...${NC}"

# Optional: Build frontend and sync to Flask static
echo -e "${YELLOW}Building frontend...${NC}"
if [ -d "frontend" ]; then
  pushd frontend >/dev/null
  if [ -f package.json ]; then
    if command -v npm >/dev/null 2>&1; then
      npm ci && npm run build
      # Copy build output to Flask static directory
      if [ -d dist ]; then
        rsync -av --delete dist/ ../app/static/react/
      elif [ -d build ]; then
        rsync -av --delete build/ ../app/static/react/
      else
        echo -e "${YELLOW}No dist/build directory found; skipping static sync${NC}"
      fi
    else
      echo -e "${YELLOW}npm not found on this host; assuming app/static/react already contains latest build${NC}"
    fi
  fi
  popd >/dev/null
fi

deploy_to_instance $INSTANCE_1
deploy_to_instance $INSTANCE_2

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Test the Arena at:"
echo "  - CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "  - ALB: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "To test Arena mode:"
echo "1. Type 'arena' in the chat"
echo "2. Ask any question"
echo "3. Vote on model responses"
echo "4. Watch the tournament progress!"
