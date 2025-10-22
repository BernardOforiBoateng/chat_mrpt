#!/bin/bash
# Deploy Dynamic Data Summary implementation to staging

set -e

echo "========================================="
echo "   Deploying Dynamic Summary to Staging "
echo "========================================="
echo ""

# Staging instances
STAGING_IPS=(
    "3.21.167.170"    # Instance 1
    "18.220.103.20"   # Instance 2
)

KEY_PATH="/tmp/chatmrpt-key.pem"

# Files to deploy
FILES=(
    "app/data_analysis_v3/core/data_profiler.py"
    "app/data_analysis_v3/core/agent.py"
    "app/data_analysis_v3/prompts/system_prompt.py"
)

echo "Deploying to staging instances..."

for ip in "${STAGING_IPS[@]}"; do
    echo ""
    echo "Deploying to $ip..."
    
    # Copy files
    for file in "${FILES[@]}"; do
        echo "  - Copying $file"
        scp -i $KEY_PATH "$file" ec2-user@$ip:/home/ec2-user/ChatMRPT/$file
    done
    
    # Restart service
    echo "  - Restarting service..."
    ssh -i $KEY_PATH ec2-user@$ip "sudo systemctl restart chatmrpt"
    
    echo "✓ Deployment to $ip completed"
done

echo ""
echo "========================================="
echo "✅ Dynamic Summary Deployed Successfully!"
echo "========================================="
echo ""
echo "What's New:"
echo "• Industry-standard data profiling"
echo "• No hardcoded column detection"
echo "• User-choice driven interface"
echo "• Works with ANY data type"
echo ""
echo "Test at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
