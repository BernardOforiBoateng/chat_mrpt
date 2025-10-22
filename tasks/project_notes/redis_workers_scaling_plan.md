# Redis & Worker Scaling Plan for 50+ Concurrent Users

## Date: July 29, 2025

### Current Limitations
1. **Single-threaded Gunicorn**: Each instance runs 1 worker
2. **Local sessions**: Not shared between instances
3. **DataFrame serialization**: Causes session storage issues
4. **Limited concurrency**: ~10-15 users per instance

### Target Architecture
```
                    [CloudFront CDN]
                           |
                    [Load Balancer]
                     /     |     \
            [Instance 1] [Instance 2] [Instance 3]
             (4 workers)  (4 workers)  (4 workers)
                  \         |         /
                   \        |        /
                    [ElastiCache Redis]
                     (Shared Sessions)
```

### Implementation Plan

#### Phase 1: ElastiCache Redis Setup
1. **Create Redis Cluster**
   - Node type: cache.t3.micro (for testing)
   - Production: cache.t3.small
   - Enable automatic backups
   - Multi-AZ for high availability

2. **Security Group Configuration**
   - Allow port 6379 from EC2 instances
   - Restrict to VPC only

3. **Application Changes**
   - Configure Flask-Session for Redis
   - Fix DataFrame serialization issue
   - Test session sharing between instances

#### Phase 2: Gunicorn Worker Optimization
1. **Current**: 1 worker per instance
2. **Target**: 4-8 workers per instance
3. **Formula**: (2 × CPU cores) + 1 = 5 workers for t3.medium

**Capacity Calculation**:
- Each worker: ~10-15 concurrent requests
- 4 workers × 2 instances = 8 workers
- Total capacity: 80-120 concurrent users

#### Phase 3: Auto Scaling Tuning
1. **Scale based on**:
   - Target CPU: 60% (lower threshold)
   - Request count per target
   - Active connections

2. **Scaling policy**:
   - Scale up: Add instance when CPU > 60% for 2 minutes
   - Scale down: Remove instance when CPU < 30% for 10 minutes

### Performance Targets
- **Response time**: <2 seconds under load
- **Concurrent users**: 50-100
- **Requests/second**: 100-200
- **Availability**: 99.9%

### Cost Analysis
| Component | Monthly Cost |
|-----------|-------------|
| ElastiCache Redis (t3.small) | $25 |
| Additional EC2 (during peaks) | $50 |
| Current infrastructure | $189 |
| **Total (peak)** | **$264** |
| **Total (normal)** | **$214** |

### Session Management Strategy

#### Problem: DataFrame in Sessions
Current code stores pandas DataFrames in session, which Redis can't serialize.

#### Solutions:
1. **Option A**: Store DataFrame as JSON
   ```python
   # Store
   session['data'] = df.to_json()
   # Retrieve
   df = pd.read_json(session['data'])
   ```

2. **Option B**: Store in temporary files
   ```python
   # Store DataFrame to file
   filepath = f"/tmp/{session_id}_data.pkl"
   df.to_pickle(filepath)
   session['data_path'] = filepath
   ```

3. **Option C**: Use Redis directly for DataFrames
   ```python
   # Store large data in Redis separately
   redis_client.set(f"df_{session_id}", df.to_pickle())
   ```

### Implementation Steps

#### Step 1: Create ElastiCache Redis
```bash
aws elasticache create-cache-cluster \
  --cache-cluster-id chatmrpt-redis \
  --cache-node-type cache.t3.small \
  --engine redis \
  --num-cache-nodes 1 \
  --security-group-ids sg-XXX
```

#### Step 2: Update Gunicorn Configuration
```python
# gunicorn_config.py
import multiprocessing

bind = "0.0.0.0:8080"
workers = multiprocessing.cpu_count() * 2 + 1  # 5 for t3.medium
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
```

#### Step 3: Configure Flask-Session
```python
# config.py
REDIS_URL = os.environ.get('ELASTICACHE_ENDPOINT')
SESSION_TYPE = 'redis'
SESSION_REDIS = redis.from_url(REDIS_URL)
SESSION_PERMANENT = False
SESSION_USE_SIGNER = True
SESSION_KEY_PREFIX = 'chatmrpt:'
```

#### Step 4: Fix DataFrame Serialization
```python
# Instead of storing DataFrame in session
# session['nmep_data'] = df  # BAD

# Store as JSON
session['nmep_data'] = df.to_json()  # GOOD

# Or store reference to file
import uuid
file_id = str(uuid.uuid4())
df.to_pickle(f'/tmp/{file_id}.pkl')
session['nmep_data_id'] = file_id
```

### Monitoring Additions
1. **Redis Metrics**:
   - Connection count
   - Memory usage
   - Cache hit/miss ratio

2. **Worker Metrics**:
   - Active workers
   - Request queue depth
   - Worker restart count

### Testing Plan
1. **Load Testing**: Use Apache Bench or JMeter
2. **Test Scenarios**:
   - 50 concurrent users uploading files
   - 100 concurrent users viewing maps
   - Session failover between instances

### Rollback Plan
If issues occur:
1. Disable Redis in environment variables
2. Reduce workers back to 1
3. Fall back to file-based sessions

### Success Criteria
- ✅ Handle 50+ concurrent users
- ✅ No session data loss
- ✅ Response time under 2 seconds
- ✅ Auto-scaling works smoothly
- ✅ No DataFrame serialization errors

### Next Steps
1. Review and approve plan
2. Create ElastiCache Redis cluster
3. Test on staging first
4. Update application code
5. Deploy to production