# Worker Scaling Issue Found
## Date: July 29, 2025

### Critical Issue Discovered ⚠️

**Problem**: Session data not shared between workers
- User completed TPR workflow on Worker 1
- User typed "yes" to continue to risk analysis
- Request went to Worker 2 which doesn't have the session data
- Application stuck "thinking" for 5+ minutes (timeout = 300s)

### Root Cause
Flask file-based sessions are stored in each worker's memory, not shared between processes. When we have multiple workers:
1. Worker 1 processes TPR upload and stores session data
2. Load balancer sends next request to Worker 2
3. Worker 2 has no idea about the previous session
4. Application hangs trying to find non-existent data

### Immediate Fix
Rolled back to 1 worker at 17:37 UTC

### Long-term Solutions

#### Option 1: Sticky Sessions (Quick Fix)
Configure load balancer to always send a user to the same worker
- Pros: No code changes needed
- Cons: Uneven load distribution, worker death loses sessions

#### Option 2: Shared File Storage (Medium Fix)
Store session files in shared directory all workers can access
- Pros: Simple implementation
- Cons: File locking issues, slower than memory

#### Option 3: Redis Sessions (Best Fix)
Use Redis for centralized session storage
- Pros: Fast, scalable, handles 1000+ users
- Cons: Requires code changes, more complex

### Recommendation
For 50 users, implement Option 2 (Shared File Storage) first:
1. Configure Flask-Session to use filesystem
2. Point all workers to same session directory
3. Test thoroughly before increasing workers

### Lesson Learned
This is EXACTLY why the user was cautious about worker scaling! Their experience with workflow communication issues was spot-on. We need to fix session sharing before attempting multiple workers.