#!/bin/bash

echo "=========================================="
echo "   Fix for Double Disambiguation Issue    "
echo "=========================================="
echo ""
echo "Issue: System showing 234 wards instead of 226 for Adamawa"
echo "Cause: Double application of ward name disambiguation"
echo "Fix: Check if ward names already contain disambiguation pattern"
echo ""

# Files to deploy
FILES_TO_DEPLOY=(
    "app/data/unified_dataset_builder.py"
    "app/analysis/pipeline_stages/data_preparation.py"
)

# Staging IPs (both instances)
STAGING_IPS=(
    "172.31.46.84"
    "172.31.24.195"
)

echo "Files to deploy:"
for file in "${FILES_TO_DEPLOY[@]}"; do
    echo "  - $file"
done
echo ""

# Check if files exist
for file in "${FILES_TO_DEPLOY[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Error: File not found: $file"
        exit 1
    fi
done

# Deploy to staging instances
echo "Deploying to staging instances..."
echo ""

for ip in "${STAGING_IPS[@]}"; do
    echo "📤 Deploying to staging instance: $ip"
    
    # Copy files
    for file in "${FILES_TO_DEPLOY[@]}"; do
        echo "  Copying $file..."
        scp -i ~/.ssh/chatmrpt-key.pem "$file" ec2-user@$ip:/home/ec2-user/ChatMRPT/$file
    done
    
    # Restart service
    echo "  Restarting service..."
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$ip 'sudo systemctl restart chatmrpt'
    
    echo "  ✅ Deployed to $ip"
    echo ""
done

echo "=========================================="
echo "         Deployment Complete!              "
echo "=========================================="
echo ""
echo "What was fixed:"
echo "  ✓ UnifiedDatasetBuilder now checks for existing disambiguation"
echo "  ✓ data_preparation.py now checks for existing disambiguation"
echo "  ✓ Prevents double application of (WardCode) suffix"
echo "  ✓ Should maintain correct 226 ward count for Adamawa"
echo ""
echo "Test at: http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com/"
echo ""
echo "Testing steps:"
echo "  1. Upload Adamawa TPR data"
echo "  2. Complete TPR analysis (should show 226 wards)"
echo "  3. Proceed to risk analysis"
echo "  4. Verify it still shows 226 wards (not 234)"
echo "  5. Check if PCA test results appear in summary"
echo ""