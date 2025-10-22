# ChatMRPT Staging Server Scaling Analysis

## Current Staging Instance Specs:
- **Instance Type**: t3.medium (or similar)
- **CPUs**: 2 cores
- **RAM**: 3.7GB total (1.8GB available)
- **Current Workers**: 2 (artificially limited by .env)

## Optimal Configuration for This Instance:

### Worker Calculation:
- **Formula**: (2 × CPU cores) + 1 = 5 workers
- **With async workers**: Could go up to 10-15 workers

### Memory Per Worker:
- Each worker uses approximately 300-400MB
- 5 workers = 1.5-2GB RAM
- Leaves 1.5-2GB for OS and caching

## Concurrent User Capacity:

### With Sync Workers (Current):
- **5 workers** = 5 concurrent requests
- **User behavior**: Users spend time between requests (reading, thinking)
- **Multiplier**: 8-10x (users aren't constantly hitting the server)
- **Capacity**: 40-50 concurrent users

### With Async Workers (Recommended):
- **10 workers** with gevent/eventlet
- **Each worker**: Can handle 50-100 concurrent connections
- **Capacity**: 500-1000 concurrent connections
- **Real users**: 100-200 concurrent users

## To Match Production (40-60 users):
The staging server can easily handle this with:
1. **5 sync workers** (current approach)
2. Or switch to **async workers** for even more capacity

## Recommended Next Steps:
1. Update GUNICORN_WORKERS=5 in .env
2. Or remove it to use the calculated default
3. Consider async workers if expecting >50 concurrent users