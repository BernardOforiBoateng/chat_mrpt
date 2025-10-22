#!/bin/bash

# Deploy TPR Download Fix to AWS
# This script fixes the HTML report not showing in download links

echo "=== Deploying TPR Download Fix to AWS ==="
echo "Starting at: $(date)"

# SSH into AWS and apply the fix
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.137.158.17 << 'EOF'
cd /home/ec2-user/ChatMRPT
source /home/ec2-user/chatmrpt_env/bin/activate

echo "Current directory: $(pwd)"

# Backup the current file
echo "Creating backup..."
cp app/static/js/modules/data/tpr-download-manager.js app/static/js/modules/data/tpr-download-manager.js.backup

# Apply the fix - add the missing type mapping
echo "Applying the fix..."
sed -i "/\'Summary Report\': \'summary\'/a\\            'TPR Analysis Report': 'summary'  // Added mapping for HTML report" app/static/js/modules/data/tpr-download-manager.js

# Verify the change was applied
echo "Verifying the change..."
if grep -q "TPR Analysis Report" app/static/js/modules/data/tpr-download-manager.js; then
    echo "✓ Fix successfully applied!"
    grep -n "TPR Analysis Report" app/static/js/modules/data/tpr-download-manager.js
else
    echo "✗ Fix failed to apply!"
    exit 1
fi

# Restart the application
echo ""
echo "Restarting ChatMRPT service..."
sudo systemctl restart chatmrpt

# Wait for service to start
sleep 3

# Check service status
echo ""
echo "Checking service status..."
sudo systemctl status chatmrpt | head -20

echo ""
echo "=== Deployment Complete ==="
echo "The HTML report should now appear in the download links!"
echo "Test by running a TPR analysis and checking if all 4 files are available."
EOF

echo ""
echo "Local deployment script execution complete at: $(date)"