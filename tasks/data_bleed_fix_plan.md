# Data Bleed Fix Implementation Plan

## Phase 1: Emergency Patches (Day 1-2)
**Goal:** Stop active data bleeding immediately

### 1.1 Remove Global Singletons (Critical)
- **Files to patch:**
  - `app/core/unified_data_state.py` - Remove global `_data_state_manager`
  - `app/core/analysis_state_handler.py` - Remove global `_analysis_state_handler`
  - `app/core/redis_state_manager.py` - Remove global `_redis_state_manager`
  - `app/core/arena_context_manager.py` - Remove singleton pattern
  - `app/core/request_interpreter.py` - Remove shared dictionaries

- **Implementation:** Factory functions that create new instances per request

### 1.2 Fix Session Validation Holes
- **Files to patch:**
  - `app/web/routes/itn_routes.py` - Reject client-provided session_id
  - `app/web/routes/export_routes.py` - Block cross-session downloads
  - All routes accepting session_id from request body

- **Implementation:** Always use `session.get('session_id')`, never from request data

### 1.3 Service Container Non-Singleton Mode
- **File:** `app/services/container.py`
- **Change:** Set `singleton=False` for all stateful services
- **Focus:** `request_interpreter`, `data_service`, `analysis_service`

## Phase 2: AWS Redis Stabilization (Day 3-4)
**Goal:** Ensure reliable session management

### 2.1 Configure AWS ElastiCache Redis
- **Service:** AWS ElastiCache for Redis
- **Configuration:**
  - Instance type: `cache.t3.micro` (start small)
  - Multi-AZ: Enabled for failover
  - Encryption: In-transit and at-rest
  - Connection: Via Security Group in VPC

### 2.2 Update Redis Connection
- **Files:**
  - `app/config/redis_config.py` - Point to ElastiCache endpoint
  - `app/__init__.py` - Remove filesystem session fallback

- **Implementation:**
  ```python
  REDIS_HOST = 'chatmrpt-redis.abc123.cache.amazonaws.com'
  # No fallback - fail if Redis unavailable
  ```

### 2.3 Session State in Redis (Not Memory)
- **Pattern inspired by template:** Each request gets fresh state from Redis
- **Implementation:** Store all session data in Redis, never in worker memory

## Phase 3: Stateless Architecture (Week 1-2)
**Goal:** Complete isolation between requests

### 3.1 Request-Scoped Pattern (Inspired by Template)
Following the Next.js template's pattern where every action validates against current user:

- **Create request context wrapper:**
  ```python
  class RequestContext:
      def __init__(self, session_id: str):
          self.session_id = session_id
          self.redis = get_redis_client()

      def get_data(self):
          # Always fetch fresh from Redis/S3
          return self.redis.get(f"data:{self.session_id}")
  ```

### 3.2 AWS S3 for Data Storage
- **Service:** AWS S3
- **Structure:**
  ```
  s3://chatmrpt-user-data/
    ├── sessions/{session_id}/
    │   ├── raw_data.csv
    │   ├── shapefile.zip
    │   └── analysis_results.json
  ```
- **Benefits:** Infinite scalability, no file system dependencies

### 3.3 Data Access Pattern
- **Never cache in memory**
- **Always validate session ownership**
- **Use presigned URLs for direct S3 access**

## Phase 4: Authentication Enhancement (Week 2)
**Goal:** Centralized auth like the template's Clerk integration

### 4.1 AWS Cognito Integration (Optional)
- **Service:** AWS Cognito
- **Purpose:** Managed authentication like Clerk in template
- **Benefits:** User pools, MFA, session management

### 4.2 Session Token Pattern
- **Generate secure tokens on login**
- **Store in httpOnly cookies**
- **Validate on every request**
- **Never trust client-provided IDs**

## Phase 5: Containerization (Week 2-3)
**Goal:** Complete process isolation

### 5.1 AWS ECS with Fargate
- **Service:** AWS ECS/Fargate
- **Container structure:**
  ```
  ├── Task Definition
  │   ├── CPU: 0.5 vCPU
  │   ├── Memory: 1 GB
  │   └── Image: ECR repository
  ```

### 5.2 Auto-scaling Configuration
- **Target:** CPU utilization 70%
- **Min tasks:** 2
- **Max tasks:** 10

## Phase 6: Monitoring & Validation (Ongoing)

### 6.1 AWS CloudWatch Metrics
- **Custom metrics:**
  - Session isolation violations
  - Cross-session access attempts
  - Redis connection health
  - S3 access patterns

### 6.2 Testing Suite
- **Concurrent user tests**
- **Session isolation tests**
- **Load testing with 100+ users**

## Implementation Order & Priority

### Week 1 (Critical)
1. **Day 1-2:** Emergency patches (Phase 1)
   - Remove all singletons
   - Fix validation holes
   - Deploy to all instances

2. **Day 3-4:** Redis stabilization (Phase 2)
   - Configure ElastiCache
   - Remove memory fallback
   - Test session persistence

### Week 2 (High Priority)
3. **Day 5-7:** Stateless architecture (Phase 3.1-3.2)
   - Request context pattern
   - S3 data storage setup

4. **Day 8-10:** Continue stateless (Phase 3.3)
   - Data access patterns
   - Validation everywhere

### Week 3 (Medium Priority)
5. **Day 11-14:** Authentication (Phase 4)
   - Consider Cognito
   - Implement token pattern

### Week 4+ (Long-term)
6. **Containerization** (Phase 5)
   - ECS/Fargate setup
   - Auto-scaling

## Success Criteria
- ✅ No data bleed in 100-user concurrent test
- ✅ All session data in Redis/S3, not memory
- ✅ No singletons with mutable state
- ✅ Session validation on every data access
- ✅ CloudWatch shows zero isolation violations

## Risk Mitigation
- **Rollback plan:** Keep backup of current code
- **Testing:** Stage each phase in dev before production
- **Monitoring:** Alert on any session violations
- **Documentation:** Track all changes for review

This plan addresses every finding from the investigation and leverages AWS services for a robust, scalable solution.