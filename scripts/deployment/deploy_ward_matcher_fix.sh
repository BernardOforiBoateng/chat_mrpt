#\!/bin/bash

echo "==========================================="
echo "   Deploying Enhanced Ward Matcher Fix    "
echo "==========================================="
echo ""
echo "This deployment adds:"
echo "1. Enhanced ward name matcher with pattern recognition"
echo "2. Dynamic matching rules (no hardcoding)"
echo "3. Support for all Nigerian states"
echo ""

# Files to deploy
FILES=(
    "app/tpr_module/services/enhanced_ward_matcher.py"
    "app/tpr_module/services/shapefile_extractor.py"
)

echo "Files to deploy:"
for file in "${FILES[@]}"; do
    echo "  - $file"
done
echo ""

# Copy key to temp location
if [ -f "aws_files/chatmrpt-key.pem" ]; then
    cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key-deploy.pem
    chmod 600 /tmp/chatmrpt-key-deploy.pem
    KEY="/tmp/chatmrpt-key-deploy.pem"
    echo "✓ SSH key prepared"
else
    echo "✗ SSH key not found at aws_files/chatmrpt-key.pem"
    exit 1
fi

# Staging server
STAGING_IP="18.117.115.217"
echo ""
echo "Deploying to staging server: $STAGING_IP"
echo "==========================================="

# Test connection
echo "Testing connection..."
if ssh -o ConnectTimeout=5 -o StrictHostKeyChecking=no -i "$KEY" ec2-user@$STAGING_IP "echo 'Connected'" > /dev/null 2>&1; then
    echo "✓ Connection successful"
else
    echo "✗ Cannot connect to staging server"
    echo "Please check if the server is running and accessible"
    exit 1
fi

# Deploy files
echo ""
echo "Deploying files..."
for file in "${FILES[@]}"; do
    echo -n "  Copying $file... "
    if scp -o StrictHostKeyChecking=no -i "$KEY" "$file" "ec2-user@$STAGING_IP:~/ChatMRPT/$file" 2>/dev/null; then
        echo "✓"
    else
        echo "✗"
        echo "Failed to copy $file"
        exit 1
    fi
done

# Restart service
echo ""
echo "Restarting ChatMRPT service..."
if ssh -o StrictHostKeyChecking=no -i "$KEY" ec2-user@$STAGING_IP "sudo systemctl restart chatmrpt" 2>/dev/null; then
    echo "✓ Service restarted"
else
    echo "✗ Failed to restart service"
    exit 1
fi

# Check service status
echo ""
echo "Checking service status..."
sleep 3
STATUS=$(ssh -o StrictHostKeyChecking=no -i "$KEY" ec2-user@$STAGING_IP "sudo systemctl is-active chatmrpt" 2>/dev/null)
if [ "$STATUS" = "active" ]; then
    echo "✓ Service is running"
else
    echo "✗ Service is not running properly"
    echo "Status: $STATUS"
    echo ""
    echo "Recent logs:"
    ssh -o StrictHostKeyChecking=no -i "$KEY" ec2-user@$STAGING_IP "sudo journalctl -u chatmrpt -n 20 --no-pager"
    exit 1
fi

# Clean up
rm -f "$KEY"

echo ""
echo "==========================================="
echo "✓ Deployment Complete\!"
echo "==========================================="
echo ""
echo "Enhanced ward matcher deployed successfully\!"
echo ""
echo "Test the fix at:"
echo "  http://18.117.115.217:5000"
echo ""
echo "What was fixed:"
echo "  - Ward name matching now handles slashes, hyphens, Roman numerals"
echo "  - Dynamic pattern recognition (no hardcoding)"
echo "  - Works for all Nigerian states"
echo "  - Should fix the 46 missing WardCodes in Adamawa"
echo ""
echo "To verify the fix:"
echo "  1. Upload Adamawa TPR data"
echo "  2. Run risk analysis"
echo "  3. Check if PCA test results appear in summary"
echo ""
