# Simple Scaling Plan for 50 Concurrent Users
## Date: July 29, 2025

### Current Setup vs Final Setup

#### Current (Temporary):
- 2 EC2 instances (manual + ASG)
- 1 worker per instance
- ~15 users per instance max
- Total capacity: ~30 users

#### Final Production (Your Goal):
- 1 EC2 instance (from ASG)
- 4 workers
- Target: 50 concurrent users
- NO Redis needed!

### The Simple Plan

#### Step 1: Test Worker Increase on Staging
```bash
# Current: 1 worker
workers = 1

# Test: 4 workers
workers = 4
worker_class = "sync"
preload_app = True
```

#### Step 2: What We're Testing
1. File uploads work across workers
2. Session data persists properly
3. No "file not found" errors
4. Memory usage stays reasonable

#### Step 3: Implementation Timeline

**Day 1 (Today)**: Test on staging
- SSH to staging: 18.117.115.217
- Modify gunicorn config
- Test with 2 workers first
- If stable for 2 hours, increase to 4

**Day 2**: Production deployment
- If staging tests pass
- Update production gunicorn config
- Monitor closely for 24 hours

**Day 3**: Consolidate to single instance
- Terminate manual instance
- Keep only ASG instance
- Verify 50 user capacity

### Configuration Changes Needed

1. **Gunicorn Config** (`/home/ec2-user/ChatMRPT/gunicorn.conf.py`):
```python
import multiprocessing

# Change from:
workers = 1

# To:
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
preload_app = True
```

2. **Instance Size**:
- Current: t2.large (2 vCPU, 8GB RAM)
- Should handle 4 workers fine
- Each worker ~1.5GB RAM = 6GB total

3. **No Other Changes Needed**:
- ✅ Keep file-based sessions
- ✅ Keep current architecture
- ✅ No Redis complexity
- ✅ No code changes

### Risk Assessment

**Low Risk**:
- Simple configuration change
- Easy to rollback (just change workers back to 1)
- Testing on staging first

**Potential Issues**:
- Session data might not share perfectly
- File uploads could fail if session switches workers

**Mitigation**:
- Test thoroughly on staging
- Monitor error logs
- Have rollback ready

### Cost Analysis

**Current (2 instances)**: ~$120/month
**Final (1 instance)**: ~$60/month
**Savings**: $60/month

### Success Metrics
- ✅ 50 concurrent users handled
- ✅ No session errors
- ✅ Response time <3 seconds
- ✅ No file upload failures
- ✅ CPU usage <80%

### Simple Testing Script
```bash
# On staging
cd /home/ec2-user/ChatMRPT

# Backup current config
cp gunicorn.conf.py gunicorn.conf.py.backup

# Edit config to 2 workers
nano gunicorn.conf.py

# Restart service
sudo systemctl restart chatmrpt

# Test functionality
# - Upload a file
# - Run analysis
# - Generate map
# - Download results

# If good, increase to 4 workers
# Repeat tests
```

### Final Architecture (Simple & Effective)
```
Internet → CloudFront CDN → ALB → Single EC2 (4 workers) → RDS
                                    ↓
                                 S3 Backups
```

### Why This Works for 50 Users
- 4 workers × 12-15 users per worker = 48-60 capacity
- File sessions are fine for this scale
- No complex Redis needed
- Easy to maintain
- Cost effective

### Next Steps
1. Test 2 workers on staging NOW
2. If stable, test 4 workers
3. Deploy to production tomorrow
4. Consolidate to single instance day after

This approach gives you exactly what you need without overengineering!