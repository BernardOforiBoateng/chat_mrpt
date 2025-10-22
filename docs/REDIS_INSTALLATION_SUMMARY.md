# Redis Installation Summary for ChatMRPT on AWS

## Problem Solved
The TPR (Test Positivity Rate) workflow was experiencing inconsistent behavior on AWS where:
- State selections (e.g., "Adamawa State") returned generic "I understand you're asking about..." messages
- Session data was lost between requests in multi-worker Gunicorn environment
- Worked perfectly on localhost but failed on AWS production

## Root Cause
- **No Redis installed on AWS**: The application was using filesystem sessions
- **Multi-worker issue**: 4 Gunicorn workers couldn't share filesystem-based sessions
- **Session data loss**: Worker A sets `tpr_workflow_active=True`, Worker B doesn't see it

## Solution Implemented

### 1. Redis Installation
- Installed Redis 6 on Amazon Linux 2023 using `dnf install redis6`
- Configured Redis with proper memory limits (256MB) for session storage
- Enabled Redis service to start on boot

### 2. Application Configuration
- Updated `app/config/base.py` to dynamically use Redis when available:
```python
if os.environ.get('REDIS_HOST'):
    SESSION_TYPE = 'redis'
    SESSION_REDIS = redis.StrictRedis(...)
else:
    SESSION_TYPE = 'filesystem'
```

### 3. Environment Setup
- Added Redis configuration to `.env`:
  - REDIS_HOST=localhost
  - REDIS_PORT=6379
  - REDIS_DB=0
- Updated systemd service with Redis environment variables

### 4. Verification Tools
- Created `/home/ec2-user/monitor_redis.sh` for health monitoring
- Script shows session keys, memory usage, and connection status

## Current Status
✅ Redis is running and healthy
✅ Flask sessions are being stored in Redis (confirmed by presence of session:* keys)
✅ Application logs show "Redis session store configured"
✅ Multi-worker session sharing is now possible

## Next Steps
1. Test the TPR workflow through the web interface:
   - Visit http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/
   - Upload NMEP TPR file
   - Select state (e.g., "Adamawa State")
   - Verify proper workflow continuation without generic responses

2. Monitor Redis during testing:
   ```bash
   ssh -i aws_files/chatmrpt-key.pem ec2-user@3.137.158.17 'redis6-cli monitor'
   ```

3. Check session creation:
   ```bash
   ssh -i aws_files/chatmrpt-key.pem ec2-user@3.137.158.17 './monitor_redis.sh'
   ```

## Important Notes
- Redis is configured for localhost only (security best practice)
- No password required (localhost access only)
- 256MB memory limit is sufficient for session storage
- Sessions expire after 1 day (as configured)

## Files Modified
1. `/home/ec2-user/ChatMRPT/app/config/base.py` - Added dynamic Redis configuration
2. `/home/ec2-user/ChatMRPT/.env` - Added Redis connection settings
3. `/home/ec2-user/monitor_redis.sh` - Created for monitoring

## Troubleshooting
If issues persist:
1. Check Redis status: `sudo systemctl status redis6`
2. View app logs: `sudo journalctl -u chatmrpt -n 100`
3. Monitor Redis: `redis6-cli monitor`
4. Check session keys: `redis6-cli --scan --pattern "*"`