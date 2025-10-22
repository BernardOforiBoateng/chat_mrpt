# AWS Infrastructure Setup and Multi-Worker Session Fix
## Date: July 30, 2025

## Overview
This document details the complete AWS infrastructure setup for ChatMRPT, including the critical fix for multi-worker session state issues that were preventing TPR uploads from working correctly.

## AWS Services Architecture

### 1. EC2 Instances
- **Staging Server**: 
  - Public IP: 18.117.115.217
  - Direct access on port 8080
  - Single instance for testing
  
- **Production Servers**:
  - Instance 1: i-06d3edfcc85a1f1c7
  - Instance 2: i-0183aaf795bf8f24e
  - Private IPs: 172.31.44.52, etc.
  - Behind ALB for load balancing

### 2. Application Load Balancer (ALB)
- **URL**: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com
- **Target Group**: chatmrpt-targets
- **ARN**: arn:aws:elasticloadbalancing:us-east-2:593543055880:targetgroup/chatmrpt-targets/80780274e6640a25
- **Key Configuration**:
  - Sticky Sessions: ENABLED (24 hours)
  - Cookie Name: AWSALB
  - Load Balancing Algorithm: Round Robin
  - Health Check: /ping endpoint

### 3. CloudFront CDN
- **URL**: https://d225ar6c86586s.cloudfront.net
- **Origin**: ALB (chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com)
- **Benefits**:
  - Global content delivery
  - HTTPS termination
  - Caching static assets
  - DDoS protection

### 4. ElastiCache Redis
- **Endpoint**: chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com:6379
- **Purpose**: Session storage for multi-worker environment
- **Configuration**: 
  - Single node
  - Used by both staging and production
  - Stores Flask sessions

### 5. S3 Buckets (Future Implementation)
- **Planned Usage**:
  - Static asset storage
  - User upload storage
  - Analysis result archives
  - Backup storage

## The Multi-Worker Session Problem

### Problem Description
When we scaled from 1 worker to 6 workers for better performance:
1. TPR uploads would trigger a page refresh instead of continuing the workflow
2. Session state was lost between requests
3. The issue only occurred on production (through ALB), not staging (direct access)

### Root Cause Analysis
1. **Initial Hypothesis**: Code issue with session persistence
   - Added `session.modified = True` 
   - Added Redis session storage
   - Added JavaScript delays
   - None of these fixed the issue

2. **Actual Root Cause**: ALB configuration
   - ALB was distributing requests across workers WITHOUT session affinity
   - User uploads TPR on Worker 1, but verification request goes to Worker 3
   - Worker 3 doesn't know about the session, causes page refresh

### The Solution
Enabled ALB Sticky Sessions (Session Affinity):
```bash
aws elbv2 modify-target-group-attributes \
    --target-group-arn arn:aws:elasticloadbalancing:us-east-2:593543055880:targetgroup/chatmrpt-targets/80780274e6640a25 \
    --attributes Key=stickiness.enabled,Value=true \
                 Key=stickiness.type,Value=lb_cookie \
                 Key=stickiness.lb_cookie.duration_seconds,Value=86400
```

## Application Configuration

### Gunicorn Configuration
```python
# gunicorn_config.py
bind = "0.0.0.0:8080"
workers = 6
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
```

### Flask Session Configuration
```python
# app/config/production.py
SESSION_TYPE = 'redis'
SESSION_REDIS = redis.from_url(REDIS_URL)
SESSION_PERMANENT = False
SESSION_USE_SIGNER = True
SESSION_KEY_PREFIX = 'chatmrpt_session:'
SESSION_COOKIE_SECURE = False  # For HTTP ALB
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
```

### Worker Capacity
- **Total Workers**: 6
- **Memory per Worker**: ~260MB
- **Total Memory Used**: ~1.6GB
- **Concurrent Users**: 48-60
- **Requests per Worker**: 8-10 concurrent

## Deployment Process

### 1. Staging to Production Sync
Created `sync_staging_to_production.sh` script that:
- Backs up production
- Copies all application files from staging
- Preserves instance-specific data
- Restarts services

### 2. Key Files Modified
- `app/web/routes/upload_routes.py` - Added session.modified = True
- `app/core/unified_data_state.py` - Removed singleton pattern
- `app/core/request_interpreter.py` - Added file-based session detection
- `app/static/js/modules/upload/file-uploader.js` - Added verification delay

### 3. Infrastructure Changes
- Increased workers from 4 to 6
- Enabled Redis sessions
- Configured ALB sticky sessions
- Set up CloudFront distribution

## Monitoring and Health Checks

### Health Check Endpoints
- `/ping` - Basic health check
- `/system-health` - Detailed system status
- `/api/session/status` - Session state check
- `/api/session/redis-status` - Redis connectivity

### Key Metrics to Monitor
1. Worker memory usage
2. Redis connection status
3. ALB target health
4. Session persistence across requests
5. Response times

## Lessons Learned

1. **Architecture Matters**: The same code behaved differently due to infrastructure differences
2. **ALB Configuration is Critical**: Sticky sessions are essential for stateful applications
3. **Direct vs. Load Balanced**: Always test both access patterns
4. **Session Management**: Redis alone isn't enough without proper load balancer configuration
5. **Debugging Approach**: Start with infrastructure before assuming code issues

## Future Improvements

1. **PostgreSQL Migration**: Move from SQLite to PostgreSQL for production
2. **S3 Integration**: Store large files and analysis results in S3
3. **Auto-scaling**: Implement auto-scaling based on load
4. **Monitoring**: Set up CloudWatch alarms and dashboards
5. **Backup Strategy**: Automated backups to S3

## Access URLs

- **Production ALB**: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com
- **Production CloudFront**: https://d225ar6c86586s.cloudfront.net
- **Staging Direct**: http://18.117.115.217:8080

## Critical Configuration Notes

1. **NEVER disable ALB sticky sessions** - The application requires session affinity
2. **Redis must be accessible** from all EC2 instances
3. **Cookie configuration** must match between Flask and ALB
4. **Health checks** must pass before instances receive traffic
5. **Session timeout** should align with ALB stickiness duration

## Troubleshooting Commands

```bash
# Check worker status
ps aux | grep gunicorn

# Check Redis connectivity
redis-cli -h chatmrpt-redis-staging.1b3pmt.0001.use2.cache.amazonaws.com ping

# View application logs
sudo journalctl -u chatmrpt -f

# Check ALB target health
aws elbv2 describe-target-health --target-group-arn [ARN]

# Test session persistence
curl -c cookies.txt http://[ALB-URL]/api/session/status
curl -b cookies.txt http://[ALB-URL]/api/session/verify-tpr
```

---
*This document represents the current state of ChatMRPT AWS infrastructure as of July 30, 2025*