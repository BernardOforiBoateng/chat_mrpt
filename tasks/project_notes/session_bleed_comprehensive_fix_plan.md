# Session Bleed - Comprehensive Fix Plan

## Date: 2025-09-23
## Priority: CRITICAL - PRODUCTION BLOCKER

## Additional AWS Infrastructure Findings

### CloudFront CDN Layer
- **URL**: https://d225ar6c86586s.cloudfront.net
- **Issue**: CloudFront adds another layer where session routing can fail
- **Caching**: CloudFront may cache responses that include session-specific data

### Application Load Balancer (ALB) Configuration
- **Production ALB**: chatmrpt-staging-alb-752380251.us-east-2.elb.amazonaws.com
- **Cookie**: AWSALB (for sticky sessions)
- **Issue**: Sticky sessions were enabled AFTER the problem, duration set to 3600 seconds
- **Critical**: Even with sticky sessions, the in-memory singleton pattern still causes issues

### Multi-Instance Architecture
- **Instance 1**: 3.21.167.170 (i-0994615951d0b9563)
- **Instance 2**: 18.220.103.20 (i-0f3b25b72f18a5037)
- **Each instance runs**: 6 Gunicorn workers (12 total worker processes)
- **Result**: 12 different memory spaces that don't share state

## The Complete Session Bleed Scenario

### How Session Bleed Happens:

1. **User A** uploads data
   - Request goes through CloudFront → ALB → Instance1/Worker2
   - Worker2 stores User A's data in its singleton dictionary with key "session_123"
   - File saved to `instance/uploads/session_123/`

2. **User B** starts a session
   - Gets assigned session_id "session_456"
   - Request goes through CloudFront → ALB → Instance1/Worker2 (same worker)

3. **Critical Bug**: Session ID extraction/handling fails
   - Could be race condition in session dict access
   - Could be session_id variable overwrite
   - Could be global state pollution

4. **User B** sees User A's data because:
   - Worker2's singleton has cached data
   - Session ID mismatch causes wrong data retrieval
   - No validation that User B owns session_456

### Why ALB Sticky Sessions Don't Fix This:

Even with AWSALB cookie ensuring same instance:
- Still have 6 workers on that instance
- Each worker has its own memory/singletons
- No guarantee of same worker within instance
- Singletons don't sync between workers

## Comprehensive Fix Plan

### Priority 1: Emergency Patches (Do First - 2 hours)

#### 1.1 Disable All Singletons
```python
# app/core/unified_data_state.py
class UnifiedDataStateManager:
    def __init__(self):
        # DO NOT STORE STATE IN MEMORY
        # self._states = {}  # REMOVE THIS
        pass

    def get_state(self, session_id: str) -> UnifiedDataState:
        # Always create fresh instance, never cache
        return UnifiedDataState(session_id, self.base_upload_folder)
```

#### 1.2 Add Session Validation
```python
# Add to all data access points
def validate_session_ownership(session_id_requested, session_id_from_cookie):
    if session_id_requested != session_id_from_cookie:
        raise SecurityError("Session ID mismatch - potential session hijack")
    return True
```

#### 1.3 Remove Global Variables
- Remove ALL global state managers
- Convert singletons to per-request instances
- Pass session_id explicitly everywhere

### Priority 2: Proper Session Management (4 hours)

#### 2.1 Implement Redis-Only Sessions
```python
# app/config/redis_config.py
class RedisConfig:
    # MUST use Redis, no fallback to filesystem
    @classmethod
    def init_redis_session(cls, app):
        redis_client = redis.StrictRedis(...)
        if not redis_client.ping():
            raise RuntimeError("Redis required for production")
        # NO FALLBACK
```

#### 2.2 Session-Scoped Data Access
```python
# Every data access must be session-scoped
def get_user_data(session_id: str):
    # Validate session exists in Redis
    if not redis_client.exists(f"session:{session_id}"):
        raise InvalidSessionError()

    # Load data from disk, never from memory
    data_path = f"instance/uploads/{session_id}/raw_data.csv"
    return pd.read_csv(data_path)
```

### Priority 3: Worker Isolation (6 hours)

#### 3.1 Remove preload_app
```python
# gunicorn.conf.py
preload_app = False  # Each worker loads fresh
workers = 6
worker_class = "sync"
```

#### 3.2 Use Redis for All Shared State
```python
# All shared state goes through Redis
def store_analysis_state(session_id, state):
    redis_client.setex(
        f"analysis_state:{session_id}",
        3600,  # 1 hour TTL
        json.dumps(state)
    )
```

### Priority 4: Add Security Layers (8 hours)

#### 4.1 User Authentication Binding
```python
@login_required
def upload_files():
    user_id = current_user.id
    session_id = session['session_id']

    # Bind session to user
    redis_client.hset(f"session:{session_id}", "user_id", user_id)

    # Validate on every access
    stored_user = redis_client.hget(f"session:{session_id}", "user_id")
    if stored_user != user_id:
        abort(403)
```

#### 4.2 Session Namespace Isolation
```python
# Use composite keys to prevent collision
def get_session_key(user_id, session_id):
    return f"user:{user_id}:session:{session_id}"
```

### Priority 5: Infrastructure Hardening (12 hours)

#### 5.1 Enable ALB Session Affinity
- Already done but verify:
  - Cookie: AWSALB
  - Duration: 3600 seconds
  - Type: application-controlled

#### 5.2 Configure CloudFront Headers
```yaml
# Pass session info through CloudFront
CloudFront:
  Behaviors:
    - ForwardedValues:
        Headers:
          - CloudFront-Viewer-Session-Id
          - CloudFront-Is-Desktop-Viewer
        Cookies:
          Forward: all  # Forward all cookies including AWSALB
```

#### 5.3 Add Request ID Tracking
```python
# Add to every request for debugging
import uuid
from flask import g

@app.before_request
def add_request_id():
    g.request_id = str(uuid.uuid4())
    g.worker_id = os.getpid()
    logger.info(f"Request {g.request_id} on worker {g.worker_id}")
```

## Testing Plan

### 1. Local Testing (Multi-Worker)
```bash
# Run with multiple workers locally
gunicorn --workers 4 --bind 0.0.0.0:5000 run:app

# Test with multiple users simultaneously
# User 1: Upload data
# User 2: Upload different data
# Verify no data bleed
```

### 2. Staging Testing
- Deploy to staging with fixes
- Run automated session isolation tests
- Use different browsers/incognito for each user
- Monitor Redis for session keys

### 3. Load Testing
```python
# Concurrent session test
import concurrent.futures
import requests

def test_session(user_id):
    session = requests.Session()
    # Upload unique file
    # Verify only sees own data

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    futures = [executor.submit(test_session, i) for i in range(10)]
```

## Monitoring & Alerting

### Add Session Bleed Detection
```python
# Add to every data retrieval
def get_data_with_monitoring(session_id):
    data = load_data(session_id)

    # Check for session bleed indicators
    if 'expected_user_id' in session:
        actual_user = data.get('uploaded_by')
        if actual_user != session['expected_user_id']:
            # CRITICAL ALERT
            alert_security_team("SESSION BLEED DETECTED", {
                'session_id': session_id,
                'expected_user': session['expected_user_id'],
                'actual_user': actual_user
            })

    return data
```

## Rollback Plan

If issues persist after fixes:

1. **Immediate**: Switch to single worker mode
   ```bash
   # gunicorn.conf.py
   workers = 1  # Temporary until fixed
   ```

2. **Disable problematic features**:
   - Disable multi-file upload
   - Force sequential processing
   - Add request queuing

3. **Emergency session reset**:
   ```bash
   # Clear all Redis sessions
   redis-cli FLUSHDB
   # Clear all upload folders
   rm -rf instance/uploads/*
   ```

## Success Criteria

- [ ] Zero session bleed in 100 concurrent user test
- [ ] Each user only sees their own data
- [ ] Session IDs are unique and bound to users
- [ ] No global state in workers
- [ ] All state in Redis or on disk
- [ ] Proper error handling for session mismatches
- [ ] Monitoring alerts for any violations

## Timeline

- **Hour 0-2**: Emergency patches (Priority 1)
- **Hour 2-6**: Proper session management (Priority 2)
- **Hour 6-12**: Worker isolation (Priority 3)
- **Hour 12-20**: Security layers (Priority 4)
- **Hour 20-32**: Infrastructure hardening (Priority 5)
- **Hour 32-40**: Testing and validation
- **Hour 40-48**: Monitoring and documentation

## Team Communication

**MUST INFORM TEAM IMMEDIATELY**:
- Application has critical security vulnerability
- All testing must stop until fixed
- No demos or external access
- Audit logs for any production data exposure

This is a STOP-THE-WORLD issue that requires immediate attention.