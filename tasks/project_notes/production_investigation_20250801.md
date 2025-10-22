# Production Investigation - August 1, 2025

## Summary
User reports that TPR download links and vulnerability maps are not working on production, despite all fixes being deployed.

## Investigation Results

### 1. Code Verification ✅
All fixes ARE deployed on production:
- ✅ `analysis_routes.py` line 591 has `download_links` in streaming response  
- ✅ `unified_dataset_builder.py` has `median_score` → `composite_score` mapping
- ✅ JavaScript files have `[v2.1]` markers
- ✅ Service was restarted 20 minutes ago (20:13 UTC)

### 2. Browser Console Analysis
From context.md:
- Shows newer JavaScript version: `app.js?v=20250709692673`
- Shows `[v2.1]` console messages in message-handler.js
- BUT still shows "No download links available"
- Error when plotting vulnerability map: "I encountered an issue: 'composite_score'"

### 3. Potential Root Causes

#### A. CloudFront CDN Caching
- Production uses CloudFront CDN: https://d225ar6c86586s.cloudfront.net
- CDN might be serving cached JavaScript despite version parameter
- Need to invalidate CloudFront cache

#### B. Browser LocalStorage/SessionStorage
- Old session data might be persisted
- JavaScript might be reading stale state

#### C. ALB Sticky Sessions
- User might be hitting a specific instance with issues
- Session affinity keeping them on problematic worker

#### D. Race Condition
- TPR completion event might fire before download manager initializes
- Timing issue between backend response and frontend handling

### 4. Diagnostic Steps Needed
1. Clear CloudFront cache invalidation
2. Test in incognito/private browsing mode
3. Check actual network requests in browser DevTools
4. Verify streaming response includes download_links

### 5. Immediate Actions
Rather than deploying more code changes, we need to:
1. Invalidate CloudFront cache
2. Have user test in incognito mode
3. Check browser network tab for actual API responses