# Production Instance Synchronization Solution

## Problem Summary
The production environment had two EC2 instances behind an Application Load Balancer (ALB) that had diverged significantly:
- **Instance 1 (3.21.167.170)**: 215 packages, including critical `aiohttp`
- **Instance 2 (18.220.103.20)**: 136 packages, missing `aiohttp` and 78 other packages
- **No ALB sticky sessions**: Requests randomly distributed between instances
- **Result**: ~50% failure rate as half the requests went to the broken instance

## Root Causes
1. **Package Divergence**: Instance 2's virtual environment was missing critical packages
2. **No Deployment Synchronization**: No process to keep instances identical
3. **No Sticky Sessions**: ALB randomly distributed requests without session affinity
4. **Virtual Environment Issues**: Services run in `/home/ec2-user/chatmrpt_env` but packages were installed in system Python

## Solution Implemented

### 1. Environment Synchronization
- Exported complete package list from working Instance 1 (210 packages)
- Installed all missing packages in Instance 2's virtual environment
- Verified `aiohttp 3.12.15` and `openai 1.90.0` installed correctly

### 2. File Synchronization
- Synchronized critical application files:
  - `app/services/` - Service container and dependencies
  - `app/core/` - Core functionality including LLM adapter
  - `app/config/` - Configuration files
  - `.env` - Environment variables
  - `gunicorn_config.py` - Server configuration

### 3. ALB Sticky Sessions
- Enabled sticky sessions on target group `chatmrpt-staging-targets`
- Cookie-based session affinity (24-hour duration)
- Ensures users stay on the same instance throughout their session

### 4. Verification
- Both instances now have:
  - 215 packages each
  - Working LLM adapter
  - Identical application code
- **100% success rate** on test requests

## Prevention Measures

### Deployment Synchronization Script
Created `/deployment/sync_production_instances.sh` that:
- Automatically syncs packages between instances
- Synchronizes application files
- Restarts services
- Verifies both instances work identically

### Usage:
```bash
cd /mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT
./deployment/sync_production_instances.sh
```

## Key Learnings

### Critical Files to Monitor
- `/home/ec2-user/chatmrpt_env/` - Virtual environment (NOT system Python)
- `/home/ec2-user/ChatMRPT/app/` - Application code
- `/etc/systemd/system/chatmrpt.service` - Service configuration

### Testing Commands
```bash
# Test LLM manager on an instance
ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@<IP> "
  cd /home/ec2-user/ChatMRPT
  /home/ec2-user/chatmrpt_env/bin/python -c '
    import sys
    sys.path.insert(0, \".\" )
    from app.core.llm_adapter import LLMAdapter
    adapter = LLMAdapter(backend=\"openai\")
    print(\"✓ Working\")
  '
"

# Check package count
/home/ec2-user/chatmrpt_env/bin/pip list | wc -l

# Check for critical packages
/home/ec2-user/chatmrpt_env/bin/pip list | grep -E "aiohttp|openai"
```

## Deployment Best Practices

### Always Deploy to Both Instances
```bash
# Deploy to both production instances
for ip in 3.21.167.170 18.220.103.20; do
    scp -i ~/.ssh/chatmrpt-key.pem file.py ec2-user@$ip:/home/ec2-user/ChatMRPT/
    ssh -i ~/.ssh/chatmrpt-key.pem ec2-user@$ip "sudo systemctl restart chatmrpt"
done
```

### After Package Updates
1. Update requirements.txt on Instance 1
2. Run the synchronization script
3. Verify both instances have the same package count
4. Test critical functionality on both instances

### Regular Health Checks
- Monitor package divergence weekly
- Check ALB sticky session configuration
- Verify both instances respond correctly
- Review error logs for package import failures

## Emergency Recovery

If one instance fails:
1. Take it out of the target group temporarily
2. Run the synchronization script to fix it
3. Test thoroughly
4. Add it back to the target group

## Configuration Details

### ALB Sticky Sessions
- Type: Application cookie (lb_cookie)
- Duration: 86400 seconds (24 hours)
- Cookie Name: AWSALB
- Target Group: chatmrpt-staging-targets

### Instance Details
- **Instance 1**: i-0994615951d0b9563 (IP: 3.21.167.170)
- **Instance 2**: i-0f3b25b72f18a5037 (IP: 18.220.103.20)
- **Virtual Env**: /home/ec2-user/chatmrpt_env
- **Python Version**: 3.11.13
- **Service**: chatmrpt.service (systemd)

## Success Metrics
- **Before Fix**: ~50% failure rate (random distribution)
- **After Fix**: 100% success rate (both instances working)
- **Package Sync**: Both instances have 215 packages
- **Sticky Sessions**: Users stay on same instance for 24 hours