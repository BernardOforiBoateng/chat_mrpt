# Production Redis Configuration Issue - August 1, 2025

## Root Cause Found

Production is configured to use the **staging Redis instance** instead of a production Redis instance:

```
REDIS_URL=redis://chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com:6379/0
```

## Why This Causes Issues

1. **Session State Confusion**: Production and staging are sharing the same Redis instance
2. **Cross-Environment Pollution**: Production sessions might be overwriting staging data
3. **Multi-Worker State**: While Redis is enabled, the shared instance causes unpredictable behavior

## The Problems This Explains

1. **TPR Download Links Not Appearing**:
   - TPR completes and stores download_links in Redis
   - But the key might be overwritten by staging activity
   - Or the session ID mapping gets confused between environments

2. **Dashboard HTML Not in Export**:
   - ITN export checks session state for analysis completion
   - Gets confused state from shared Redis instance

## Solution

Production needs its own Redis instance:
1. Create a production ElastiCache Redis cluster
2. Update production .env with the production Redis URL
3. Keep staging and production completely separate

## Temporary Workaround

Could disable Redis sessions temporarily:
```
ENABLE_REDIS_SESSIONS=false
```

But this would bring back the multi-worker issues where requests hit different workers.