# Production Deployment Guide - Multi-Worker Fixes

## Overview
Deploy all successful fixes from staging (18.117.115.217) to production (3.137.158.17).

## Files to Update

### 1. /home/ec2-user/ChatMRPT/app/core/unified_data_state.py
**Change**: Remove the `_states` cache to ensure each worker gets fresh state
- Line ~28: Comment out or remove `_states = {}`
- Line ~39-42: Remove the caching logic in `get_state()`

### 2. /home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py
**Change**: Remove singleton pattern
- Line ~14-21: Remove `_instance` and `__new__` method
- Ensure each worker creates its own instance

### 3. /home/ec2-user/ChatMRPT/app/core/request_interpreter.py
**Critical Fix**: Add file-based detection in `_get_session_context()` method
- Around line 1536, after getting `analysis_complete` from session, add:

```python
# NEW: Check for unified dataset files on disk (works across workers)
if not analysis_complete and session_id:
    import os
    upload_path = os.path.join('instance/uploads', session_id)
    unified_files = ['unified_dataset.geoparquet', 'unified_dataset.csv', 
                    'analysis_vulnerability_rankings.csv', 'analysis_vulnerability_rankings_pca.csv']
    
    for filename in unified_files:
        filepath = os.path.join(upload_path, filename)
        if os.path.exists(filepath):
            analysis_complete = True
            logger.info(f"Session context: Found {filename}, marking analysis_complete=True for session {session_id}")
            break
```

### 4. /home/ec2-user/ChatMRPT/gunicorn.conf.py
**Change**: Update workers from 4 to 6
```python
workers = 6  # was 4
```

### 5. /home/ec2-user/ChatMRPT/.env (optional)
If exists, update:
```
GUNICORN_WORKERS=6
```

## Deployment Steps

### Option 1: Via AWS Systems Manager Session Manager

1. Go to AWS Console → Systems Manager → Session Manager
2. Start session with production instance
3. Execute the deployment:

```bash
# 1. Create backups
cd /home/ec2-user/ChatMRPT
sudo cp app/core/unified_data_state.py app/core/unified_data_state.py.backup_$(date +%Y%m%d_%H%M%S)
sudo cp app/core/analysis_state_handler.py app/core/analysis_state_handler.py.backup_$(date +%Y%m%d_%H%M%S)
sudo cp app/core/request_interpreter.py app/core/request_interpreter.py.backup_$(date +%Y%m%d_%H%M%S)
sudo cp gunicorn.conf.py gunicorn.conf.py.backup_$(date +%Y%m%d_%H%M%S)

# 2. Copy files from staging (if network allows)
# Otherwise, apply changes manually as documented above

# 3. Update worker count
sudo sed -i 's/workers = 4/workers = 6/' gunicorn.conf.py

# 4. Test syntax
python3 -m py_compile app/core/unified_data_state.py
python3 -m py_compile app/core/analysis_state_handler.py
python3 -m py_compile app/core/request_interpreter.py

# 5. Restart service
sudo systemctl restart chatmrpt

# 6. Verify
sleep 10
ps aux | grep gunicorn | grep -v grep | wc -l  # Should show 7 (1 master + 6 workers)
curl -s http://localhost:5000/ping
```

### Option 2: Via EC2 Instance Connect

1. Go to AWS Console → EC2 → Instances
2. Select production instance (3.137.158.17)
3. Click "Connect" → "EC2 Instance Connect"
4. Execute the deployment steps above

### Option 3: If Direct SSH Works from Another Location

```bash
# Get files from staging
scp -i chatmrpt-key.pem ec2-user@18.117.115.217:/home/ec2-user/ChatMRPT/app/core/*.py ./staging_files/

# Deploy to production
scp -i chatmrpt-key.pem ./staging_files/*.py ec2-user@3.137.158.17:/home/ec2-user/ChatMRPT/app/core/
```

## Verification Steps

1. **Check Worker Count**:
   ```bash
   ps aux | grep gunicorn | grep -v grep | wc -l
   ```
   Should show 7 processes (1 master + 6 workers)

2. **Test Complete Workflow**:
   - Upload data and run risk analysis
   - Verify ITN planning detects completed analysis
   - Check that maps and visualizations work

3. **Monitor Logs**:
   ```bash
   sudo journalctl -u chatmrpt -f
   ```

## Rollback Plan

If issues occur:
```bash
cd /home/ec2-user/ChatMRPT
# Restore backups
sudo cp app/core/unified_data_state.py.backup_* app/core/unified_data_state.py
sudo cp app/core/analysis_state_handler.py.backup_* app/core/analysis_state_handler.py
sudo cp app/core/request_interpreter.py.backup_* app/core/request_interpreter.py
sudo cp gunicorn.conf.py.backup_* gunicorn.conf.py
# Restart
sudo systemctl restart chatmrpt
```

## Summary

This deployment brings production to the same state as staging:
- ✅ Multi-worker session persistence fixed
- ✅ ITN planning correctly detects completed analysis
- ✅ 6 workers for 50-60 concurrent users
- ✅ All workflows functioning properly

Staging remains unchanged for future testing and improvements.