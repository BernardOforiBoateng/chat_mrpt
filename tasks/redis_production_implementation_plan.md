# Production Redis Implementation Plan

## Current State Documentation

### Staging Environment (WORKING ✅)
- **Server**: 18.117.115.217
- **Redis**: `chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com:6379`
- **Status**: Working correctly

### Production Environment (ISSUE ❌)
- **Server**: 172.31.44.52 (via ALB: chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com)
- **Redis**: Using STAGING's Redis (incorrect!)
- **Workers**: 6 Gunicorn workers
- **Problem**: Session state confusion between environments

## Implementation Plan

### Phase 1: Preparation (Before Making Changes)

1. **Document Current State**
   - [ ] Take screenshot of current .env on production
   - [ ] Note current worker count and service status
   - [ ] Test and document current issues (TPR downloads, ITN export)

2. **Create Backup**
   ```bash
   # On production server
   sudo cp /home/ec2-user/ChatMRPT/.env /home/ec2-user/ChatMRPT/.env.backup_20250801_redis
   ```

### Phase 2: Create Production Redis Instance

1. **AWS ElastiCache Configuration**
   - **Name**: `chatmrpt-redis-production`
   - **Engine**: Redis 7.x
   - **Node Type**: `cache.t3.micro` (can scale up later)
   - **Number of Replicas**: 0 (single node for cost efficiency)
   - **Subnet Group**: Same as production EC2 instances
   - **Parameter Group**: default.redis7
   - **Security Group**: 
     - Allow inbound port 6379 from production EC2 security group
     - Name: `chatmrpt-redis-production-sg`

2. **Important Settings**
   - **Automatic Backups**: Enable with 1-day retention
   - **Maintenance Window**: Choose low-traffic time
   - **Multi-AZ**: No (for cost savings initially)

### Phase 3: Update Production Configuration

1. **Get New Redis Endpoint**
   - Wait for Redis cluster to be "available" status
   - Copy endpoint: `chatmrpt-redis-production.xxxxx.use2.cache.amazonaws.com:6379`

2. **Test Connection First**
   ```python
   # Test script to verify Redis connectivity
   import redis
   
   redis_url = "redis://chatmrpt-redis-production.xxxxx.use2.cache.amazonaws.com:6379/0"
   r = redis.from_url(redis_url)
   r.ping()  # Should return True
   ```

3. **Update Production .env**
   ```bash
   # Old (WRONG)
   REDIS_URL=redis://chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com:6379/0
   
   # New (CORRECT)
   REDIS_URL=redis://chatmrpt-redis-production.xxxxx.use2.cache.amazonaws.com:6379/0
   ENABLE_REDIS_SESSIONS=true
   ```

### Phase 4: Deployment Steps

1. **Announce Maintenance** (if needed)
   - Brief 5-minute window for service restart

2. **Execute Update**
   ```bash
   # 1. Update .env file with new Redis URL
   sudo nano /home/ec2-user/ChatMRPT/.env
   
   # 2. Verify change
   grep REDIS_URL /home/ec2-user/ChatMRPT/.env
   
   # 3. Restart service
   sudo systemctl restart chatmrpt
   
   # 4. Verify service is running
   sudo systemctl status chatmrpt
   ps aux | grep gunicorn | grep -v grep | wc -l  # Should show 7
   ```

### Phase 5: Testing & Verification

1. **Immediate Tests**
   - [ ] Service is running with correct worker count
   - [ ] No errors in logs: `sudo journalctl -u chatmrpt -f`
   - [ ] Redis connection successful

2. **Functional Tests**
   - [ ] Upload TPR file
   - [ ] Complete TPR analysis
   - [ ] Verify download links appear in "Download Processed Data" tab
   - [ ] Run ITN distribution planning
   - [ ] Export ITN package
   - [ ] Verify dashboard HTML is included

3. **Cross-Environment Check**
   - [ ] Test staging - should still work independently
   - [ ] Test production - should work with its own Redis

### Phase 6: Monitoring

1. **Monitor for 24 hours**
   - Redis memory usage
   - Connection count
   - Error logs
   - User reports

2. **Success Metrics**
   - TPR download links persist correctly
   - ITN exports include dashboard HTML
   - No session state confusion
   - Both environments work independently

## Rollback Plan

If issues occur:

1. **Quick Rollback**
   ```bash
   # Restore original .env
   sudo cp /home/ec2-user/ChatMRPT/.env.backup_20250801_redis /home/ec2-user/ChatMRPT/.env
   
   # Restart service
   sudo systemctl restart chatmrpt
   ```

2. **Alternative: Disable Redis**
   ```bash
   # As last resort, disable Redis sessions
   sudo sed -i 's/ENABLE_REDIS_SESSIONS=true/ENABLE_REDIS_SESSIONS=false/' .env
   sudo systemctl restart chatmrpt
   ```

## Cost Considerations

- **cache.t3.micro**: ~$0.017/hour = ~$12/month
- **Data transfer**: Minimal (same AZ)
- **Backup storage**: Minimal

## Timeline

1. **Preparation**: 15 minutes
2. **Redis Creation**: 15-20 minutes (AWS provisioning)
3. **Configuration Update**: 5 minutes
4. **Testing**: 30 minutes
5. **Total**: ~1 hour

## Notes

- Keep staging and production Redis completely separate
- Consider implementing Redis password authentication later
- Monitor Redis memory usage and scale if needed
- Document the new Redis endpoint in team wiki/docs