#!/bin/bash
# ==============================================================================
# ChatMRPT: Deploy Arena + OpenAI Streaming Upgrade (Backend + Frontend)
# - Builds the React frontend to app/static/react
# - Copies backend route/manager changes
# - Rsyncs React build to both production instances
# - Restarts the chatmrpt service on both instances
# ==============================================================================

set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Instances (from CLAUDE.md)
INSTANCE_1="3.21.167.170"
INSTANCE_2="18.220.103.20"

# Paths
KEY_FILE="/tmp/chatmrpt-key2.pem"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_PATH="/home/ec2-user/ChatMRPT"

# Backend files to deploy
BACKEND_FILES=(
  "app/core/arena_manager.py"
  "app/web/routes/analysis_routes.py"
  "app/web/routes/arena_routes.py"
)

echo -e "${GREEN}=== ChatMRPT Arena + OpenAI Streaming Deploy ===${NC}"

# Prepare SSH key
if [ ! -f "$KEY_FILE" ]; then
  echo -e "${YELLOW}Preparing SSH key...${NC}"
  cp "$REPO_ROOT/aws_files/chatmrpt-key.pem" "$KEY_FILE"
  chmod 600 "$KEY_FILE"
fi

# Build frontend (outputs to app/static/react)
echo -e "${YELLOW}Building React frontend (vite) into app/static/react...${NC}"
pushd "$REPO_ROOT/frontend" >/dev/null
if command -v npm >/dev/null 2>&1; then
  # Install deps only if node_modules missing (speed up idempotent runs)
  if [ ! -d node_modules ]; then
    echo -e "${YELLOW}Installing npm dependencies...${NC}"
    npm ci || npm install
  fi
  npm run build
else
  echo -e "${RED}npm not found. Skipping build. Ensure app/static/react is up-to-date.${NC}"
fi
popd >/dev/null

# Function to deploy to an instance
deploy_to_instance() {
  local IP="$1"
  echo -e "${YELLOW}Deploying to ${IP}...${NC}"

  # Ensure directories exist on remote
  ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ec2-user@"$IP" "mkdir -p \"$APP_PATH/app/static/react\""

  # Copy backend files
  echo -e "${YELLOW}Copying backend files...${NC}"
  for f in "${BACKEND_FILES[@]}"; do
    scp -o StrictHostKeyChecking=no -i "$KEY_FILE" "$REPO_ROOT/$f" "ec2-user@$IP:$APP_PATH/$f"
  done

  # Rsync frontend build
  echo -e "${YELLOW}Syncing frontend build (app/static/react)...${NC}"
  rsync -avz --delete -e "ssh -o StrictHostKeyChecking=no -i $KEY_FILE" \
    "$REPO_ROOT/app/static/react/" \
    "ec2-user@$IP:$APP_PATH/app/static/react/"

  # Restart service
  echo -e "${YELLOW}Restarting chatmrpt service...${NC}"
  ssh -o StrictHostKeyChecking=no -i "$KEY_FILE" ec2-user@"$IP" "sudo systemctl restart chatmrpt && sudo systemctl is-active chatmrpt"
}

echo -e "${GREEN}Starting deployment to both production instances...${NC}"
deploy_to_instance "$INSTANCE_1"
deploy_to_instance "$INSTANCE_2"

echo -e "${GREEN}Deployment complete!${NC}"
echo "Validate via CloudFront and test Arena streaming across rounds."
echo "- CloudFront: https://d225ar6c86586s.cloudfront.net"
echo "- ALB:        http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"

