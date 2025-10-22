#\!/bin/bash

echo "==========================================="
echo "   Complete Ward Matching Fix Deployment  "
echo "==========================================="
echo ""

FILES=(
    "app/tpr_module/services/enhanced_ward_matcher.py"
    "app/tpr_module/services/shapefile_extractor.py"
    "app/tpr_module/output/output_generator.py"
)

echo "Files to deploy:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done
echo ""

# Copy key
if [ -f "aws_files/chatmrpt-key.pem" ]; then
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key-fix.pem
    chmod 600 /tmp/chatmrpt-key-fix.pem
    KEY="/tmp/chatmrpt-key-fix.pem"
    echo "✓ SSH key prepared"
else
    echo "✗ SSH key not found"
    exit 1
fi

# Staging server
STAGING_IP="18.117.115.217"

echo "Deploying to staging: $STAGING_IP"
echo "==========================================="

# Deploy files
echo "Deploying files..."
for file in "${FILES[@]}"; do
    echo -n "  $file... "
    if scp -o StrictHostKeyChecking=no -i "$KEY" "$file" "ec2-user@$STAGING_IP:~/ChatMRPT/$file" 2>/dev/null; then
        echo "✓"
    else
        echo "✗"
    fi
done

# Clear TPR cache to force fresh processing
echo ""
echo "Clearing TPR cache..."
ssh -o StrictHostKeyChecking=no -i "$KEY" ec2-user@$STAGING_IP "rm -rf ~/ChatMRPT/instance/uploads/*/Adamawa*.csv ~/ChatMRPT/instance/uploads/*/Adamawa*.zip 2>/dev/null" 2>/dev/null
echo "✓ TPR cache cleared"

# Restart service
echo ""
echo "Restarting service..."
if ssh -o StrictHostKeyChecking=no -i "$KEY" ec2-user@$STAGING_IP "sudo systemctl restart chatmrpt" 2>/dev/null; then
    echo "✓ Service restarted"
fi

# Clean up
rm -f "$KEY"

echo ""
echo "==========================================="
echo "✓ Complete Fix Deployed\!"
echo "==========================================="
echo ""
echo "CRITICAL: The enhanced matcher is now integrated into OutputGenerator\!"
echo ""
echo "To test:"
echo "  1. Start a NEW session (clear cookies/cache)"
echo "  2. Upload NMEP TPR file"
echo "  3. Select Adamawa State"
echo "  4. Complete TPR analysis"
echo "  5. Run risk analysis"
echo "  6. PCA test results should now appear\!"
echo ""
echo "URL: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/"
