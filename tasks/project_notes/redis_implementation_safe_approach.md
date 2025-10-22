# Redis Implementation - Safe Approach

## Date: July 29, 2025

### Our Safety-First Approach

#### What We're NOT Touching:
- ❌ Production instances (both keep running)
- ❌ Current session management
- ❌ Working application code
- ❌ Current Gunicorn configuration

#### What We ARE Doing:
- ✅ Creating NEW ElastiCache Redis cluster
- ✅ Testing ONLY on staging (18.117.115.217)
- ✅ Creating NEW configuration files
- ✅ Full testing before any production changes

### Phase 1: Infrastructure Setup (No App Impact)
1. **Create ElastiCache Redis**
   - Separate from current infrastructure
   - Won't affect running applications

2. **Security Group Setup**
   - New rule for Redis port 6379
   - Only allows connections from our instances

3. **Test Connection from Staging**
   - Verify Redis is accessible
   - No changes to application yet

### Phase 2: Staging Testing
1. **Copy current code to test directory**
   ```bash
   cp -r /home/ec2-user/ChatMRPT /home/ec2-user/ChatMRPT-redis-test
   ```

2. **Modify test version only**
   - Update Flask-Session configuration
   - Fix DataFrame serialization
   - Increase worker count

3. **Run side-by-side**
   - Original app on port 8080
   - Test app on port 8081
   - Compare performance

### Phase 3: Worker Configuration Testing
1. **Test different worker counts**
   - Start with 2 workers
   - Gradually increase to 4
   - Monitor memory and CPU

2. **Load testing on staging**
   - Simulate 50 concurrent users
   - Verify no crashes
   - Check session persistence

### Phase 4: Production Deployment (Only When Ready)
1. **Create new deployment package**
2. **Deploy to one instance first**
3. **Monitor for 24 hours**
4. **Then deploy to second instance**

### Rollback Plan
At ANY point if issues occur:
1. Simply don't deploy to production
2. Delete test directory
3. Redis cluster can be deleted
4. Zero impact to running system

### Testing Checklist
- [ ] Redis cluster created
- [ ] Can connect from staging
- [ ] Sessions persist across workers
- [ ] DataFrames serialize correctly
- [ ] 50 concurrent users handled
- [ ] No memory leaks
- [ ] No performance degradation

### Current Status: WAITING FOR PERMISSIONS
Need to add `AmazonElastiCacheFullAccess` to IAM role before proceeding.