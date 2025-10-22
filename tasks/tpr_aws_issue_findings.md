# TPR Workflow AWS Issue - Root Cause Analysis & Solution

## Problem Summary
The TPR (Test Positivity Rate) analysis workflow works correctly on localhost but exhibits inconsistent behavior on AWS behind the load balancer. Specifically:
- State selection is not recognized (e.g., "Adamawa State" gets generic response)  
- Health facility type selection fails (e.g., "Use Primary Health Facilities only")
- Age group selection is not processed correctly
- Generic response: "I understand you're asking about: 'X'. Let me help you with the current step first..."

## Root Cause Analysis

### 1. Missing Redis on AWS
**Finding**: Redis is not installed or running on the AWS EC2 instance
```bash
# Redis server not found
$ which redis-server
/usr/bin/which: no redis-server in PATH

# No Redis process running
$ ps aux | grep redis
# Only shows the grep command itself
```

### 2. Filesystem Session Fallback
**Finding**: Without Redis, the application falls back to filesystem sessions
```python
# app/config/base.py
SESSION_TYPE = 'filesystem'

# app/__init__.py (lines 94-99)
redis_initialized = RedisConfig.init_redis_session(app)
if not redis_initialized:
    # Fall back to filesystem sessions
```

### 3. Multi-Worker Session Inconsistency
**Finding**: Multiple Gunicorn workers behind AWS ALB cannot share filesystem sessions
- Worker A handles initial TPR upload and sets `tpr_workflow_active = True` in session
- Worker B handles next request but has no access to Worker A's session data
- TPR workflow state is lost, causing routing to fail

### 4. Intent Classification Failure
**Finding**: When TPR state is lost, the workflow router's intent classification defaults to generic handling
```python
# app/tpr_module/integration/tpr_workflow_router.py
def _handle_general_query(self, user_input: str, intent_data: Dict) -> Dict[str, Any]:
    return {
        'status': 'info',
        'message': f"I understand you're asking about: '{user_input}'. Let me help you with the current step first...",
        'stage': self.current_stage.value
    }
```

## Solution Recommendations

### Option 1: Install and Configure Redis (Recommended)
This is the proper solution for production multi-worker environments.

```bash
# Install Redis on Amazon Linux 2
sudo amazon-linux-extras install redis6
sudo systemctl start redis
sudo systemctl enable redis

# Configure Redis for ChatMRPT
sudo nano /etc/redis/redis.conf
# Set: bind 127.0.0.1
# Set: maxmemory 256mb
# Set: maxmemory-policy allkeys-lru

# Add to .env file
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Restart application
sudo systemctl restart chatmrpt
```

### Option 2: Use Single Worker (Quick Fix)
Temporary workaround - reduces concurrency but ensures session consistency.

```bash
# Edit gunicorn.conf.py
workers = 1  # Change from 4 to 1

# Restart
sudo systemctl restart chatmrpt
```

### Option 3: Implement Sticky Sessions on ALB
Configure AWS Application Load Balancer to use sticky sessions (session affinity).

```bash
# AWS CLI command
aws elbv2 modify-target-group-attributes \
  --target-group-arn <your-target-group-arn> \
  --attributes Key=stickiness.enabled,Value=true \
               Key=stickiness.type,Value=app_cookie \
               Key=stickiness.app_cookie.cookie_name,Value=AWSALB \
               Key=stickiness.app_cookie.duration_seconds,Value=3600
```

### Option 4: Use Database Sessions
Modify configuration to use database-backed sessions instead of filesystem.

```python
# app/config/production.py
SESSION_TYPE = 'sqlalchemy'
SESSION_SQLALCHEMY = db
SESSION_SQLALCHEMY_TABLE = 'sessions'
```

## Additional Issues Found

### 1. Browser Console Error
```javascript
// crypto.randomUUID is not a function
content.js:63 Uncaught TypeError: crypto.randomUUID is not a function
```
This suggests older browser compatibility issues but doesn't affect core functionality.

### 2. Session State Synchronization
The code correctly marks session as modified in several places:
```python
# Force session update for multi-worker environment
session.modified = True
```
However, this only works if the session backend supports it (Redis/Database).

## Recommended Implementation Steps

1. **Immediate Fix**: Reduce to single worker
2. **Install Redis**: Follow installation steps above
3. **Test Thoroughly**: Verify TPR workflow with Redis active
4. **Monitor Sessions**: Check Redis session keys with `redis-cli`
5. **Load Test**: Ensure performance is acceptable

## Verification Commands

```bash
# Check Redis is working
redis-cli ping
# Should return: PONG

# Monitor Redis keys
redis-cli --scan --pattern "chatmrpt:*"

# Check application logs
tail -f /home/ec2-user/ChatMRPT/instance/app.log | grep -E "Redis|session"

# Test TPR workflow
# Upload file, select state, facility, age group
# Should complete without generic responses
```

## Expected Outcome
With Redis properly configured:
- Session data persists across all workers
- TPR workflow state is maintained throughout the conversation
- State/facility/age selections are properly recognized
- No more generic "I understand you're asking about..." responses