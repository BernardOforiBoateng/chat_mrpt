# CloudFront Cache Invalidation Instructions

## The Issue
CloudFront is serving the OLD cached version of survey_button.js
The ALB URL works correctly because it bypasses CloudFront

## Solution 1: Manual CloudFront Invalidation (Immediate)

1. Go to AWS Console: https://console.aws.amazon.com/cloudfront/
2. Find distribution for: d225ar6c86586s.cloudfront.net
3. Click on the distribution ID
4. Go to "Invalidations" tab
5. Click "Create Invalidation"
6. Enter these paths:
   - /static/js/survey_button.js
   - /*
7. Click "Create Invalidation"
8. Wait 2-3 minutes for invalidation to complete

## Solution 2: Cache-Busting URL (Temporary Workaround)
Access the site with a cache-busting parameter:
https://d225ar6c86586s.cloudfront.net/?v=$(date +%s)

## Solution 3: Wait for TTL
CloudFront cache typically expires in 24 hours

## Current Status
- ALB URL: ✅ FIXED (http://chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com)
- CloudFront: ❌ CACHED (needs manual invalidation)

