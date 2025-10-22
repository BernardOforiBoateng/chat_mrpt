#!/bin/bash
# Deploy Critical TPR Fixes to Staging Servers

echo "=================================================="
echo "Deploying Critical TPR Fixes to Staging"
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
echo "Critical Fixes Included:"
echo "1. ✅ Removed 'All Age Groups Combined' option"
echo "2. ✅ Fixed percentage calculation (no more >100%)"
echo "3. ✅ Ensured 'Over 5 Years' is detected"
echo "4. ✅ Added RDT vs Microscopy test stats"
echo "5. ✅ Fixed formatting with proper line breaks"

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
echo "✅ Critical TPR Fixes Deployed Successfully!"
echo "=================================================="
echo ""
echo "Changes deployed:"
echo "• Age groups: Now shows only 3 options (Under 5, Over 5, Pregnant Women)"
echo "• Percentages: Removed to avoid >100% confusion"
echo "• Test stats: Added RDT and Microscopy breakdown for all selections"
echo "• Formatting: Proper line breaks between all bullet points"
echo ""
echo "Test the fixes at:"
echo "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""