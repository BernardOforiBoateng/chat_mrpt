#!/bin/bash
# Deploy debug logging to AWS production instances

echo "========================================"
echo "DEPLOYING DEBUG LOGGING TO PRODUCTION"
echo "========================================"

# Production IPs
PROD_IP1="3.21.167.170"
PROD_IP2="18.220.103.20"

# Files to deploy
FILES=(
    "app/core/request_interpreter.py"
    "app/tools/complete_analysis_tools.py"
    "app/tools/visualization_maps_tools.py"
    "app/tools/variable_distribution.py"
)

echo "Deploying to Production Instance 1 ($PROD_IP1)..."
for file in "${FILES[@]}"; do
    echo "  Copying $file..."
    scp -i ~/.ssh/chatmrpt-key.pem "$file" ec2-user@$PROD_IP1:/home/ec2-user/ChatMRPT/$file
done

echo "Deploying to Production Instance 2 ($PROD_IP2)..."
for file in "${FILES[@]}"; do
    echo "  Copying $file..."
    scp -i ~/.ssh/chatmrpt-key.pem "$file" ec2-user@$PROD_IP2:/home/ec2-user/ChatMRPT/$file
done

echo ""
echo "Restarting services..."
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP1 'sudo systemctl restart chatmrpt'
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$PROD_IP2 'sudo systemctl restart chatmrpt'

echo ""
echo "✅ Debug logging deployed successfully!"
echo ""
echo "Now you can:"
echo "1. Test the risk analysis flow"
echo "2. Try visualization commands"
echo "3. Check logs with: sudo journalctl -u chatmrpt -f"
echo ""
echo "Look for lines starting with '🔍 DEBUG:' in the logs"
