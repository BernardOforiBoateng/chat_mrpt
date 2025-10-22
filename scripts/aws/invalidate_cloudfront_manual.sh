#!/bin/bash

# Manual CloudFront invalidation script
echo "CloudFront Cache Invalidation"
echo "============================"
echo ""
echo "To invalidate the CloudFront cache, run this command with proper AWS credentials:"
echo ""
echo "aws cloudfront create-invalidation --distribution-id E3RH5SBJN1Z9L4 --paths '/*'"
echo ""
echo "Or go to AWS Console:"
echo "1. Navigate to CloudFront"
echo "2. Select distribution E3RH5SBJN1Z9L4"
echo "3. Go to Invalidations tab"
echo "4. Create invalidation with path: /*"
echo ""
echo "The invalidation will take a few minutes to complete."