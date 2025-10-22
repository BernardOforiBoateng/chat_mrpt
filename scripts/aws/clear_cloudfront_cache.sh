#!/bin/bash

echo "=== CloudFront Cache Invalidation ==="
echo "Attempting to clear CloudFront cache..."

# Try using AWS CLI if configured
if command -v aws &> /dev/null; then
    # Try to get distribution ID from CloudFront
    DIST_ID=$(aws cloudfront list-distributions --query "DistributionList.Items[?DomainName=='d225ar6c86586s.cloudfront.net'].Id" --output text 2>/dev/null)
    
    if [ -n "$DIST_ID" ]; then
        echo "Found distribution: $DIST_ID"
        aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*"
        echo "✅ Invalidation created"
    else
        echo "Could not find distribution ID"
    fi
else
    echo "AWS CLI not configured"
fi

echo ""
echo "=== Manual Cache Clear Instructions ==="
echo "1. Go to AWS Console > CloudFront"
echo "2. Find distribution: d225ar6c86586s.cloudfront.net"
echo "3. Go to 'Invalidations' tab"
echo "4. Create invalidation with path: /*"
echo ""
echo "OR use this direct link to test without CloudFront:"
echo "http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com"
echo ""
echo "=== Browser Cache Clear ==="
echo "Press Ctrl+Shift+R (Windows/Linux) or Cmd+Shift+R (Mac)"
echo "Or open in Incognito/Private mode"

