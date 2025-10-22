#!/bin/bash

# CloudFront Invalidation Script for ChatMRPT
# This will clear the CloudFront cache to serve updated files

echo "=========================================="
echo "CloudFront Cache Invalidation"
echo "=========================================="

# CloudFront Distribution ID (you need to find this in AWS Console)
# Go to CloudFront -> Distributions -> Look for d225ar6c86586s.cloudfront.net
DISTRIBUTION_ID="YOUR_DISTRIBUTION_ID_HERE"

# Create invalidation for all files
echo "Creating invalidation for all files..."
aws cloudfront create-invalidation \
    --distribution-id "$DISTRIBUTION_ID" \
    --paths "/*" \
    --query 'Invalidation.Id' \
    --output text

if [ $? -eq 0 ]; then
    echo "✅ Invalidation created successfully!"
    echo "It may take a few minutes for the cache to clear."
else
    echo "❌ Failed to create invalidation"
    echo "Make sure you have AWS CLI configured with proper credentials"
fi

echo ""
echo "To find your Distribution ID:"
echo "1. Go to AWS Console -> CloudFront"
echo "2. Find the distribution for d225ar6c86586s.cloudfront.net"
echo "3. Copy the Distribution ID"
echo "4. Replace YOUR_DISTRIBUTION_ID_HERE in this script"