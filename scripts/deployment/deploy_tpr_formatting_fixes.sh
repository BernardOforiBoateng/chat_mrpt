#!/bin/bash
# Deploy TPR Formatting Fixes to Staging Servers

echo "=================================================="
echo "Deploying TPR Formatting Fixes to Staging"
echo "=================================================="

# Files to deploy
FILES=(
    "app/data_analysis_v3/core/tpr_data_analyzer.py"
    "app/data_analysis_v3/core/formatters.py"
)

# Staging server IPs (NEW as of Jan 7, 2025)
STAGING_IPS=("3.21.167.170" "18.220.103.20")

# Key path
KEY_PATH="/tmp/chatmrpt-key2.pem"

# Check if key exists
if [ ! -f "$KEY_PATH" ]; then
    echo "Copying key to /tmp..."
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
    chmod 600 /tmp/chatmrpt-key2.pem
fi

echo ""
echo "Files to deploy:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done

echo ""
echo "Deploying to staging servers..."

for ip in "${STAGING_IPS[@]}"; do
    echo ""
    echo "Deploying to $ip..."
    
    # Copy files
    for file in "${FILES[@]}"; do
        echo "  Copying $file..."
        scp -i "$KEY_PATH" -o StrictHostKeyChecking=no "$file" "ec2-user@$ip:/home/ec2-user/ChatMRPT/$file"
    done
    
    # Restart service
    echo "  Restarting service..."
    ssh -i "$KEY_PATH" -o StrictHostKeyChecking=no "ec2-user@$ip" "sudo systemctl restart chatmrpt"
    
    echo "✅ Deployed to $ip"
done

echo ""
echo "=================================================="
echo "✅ TPR Formatting Fixes Deployed Successfully!"
echo "=================================================="
echo ""
echo "Fixed issues:"
echo "1. ✅ Age group detection now handles sanitized column names"
echo "2. ✅ Message formatting with proper line breaks"
echo "3. ✅ Accurate positivity rate calculation"
echo "4. ✅ Dynamic prompt text matching available options"
echo "5. ✅ Better pattern matching for all 4 age groups"
echo ""
echo "Test the fixes at:"
echo "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""