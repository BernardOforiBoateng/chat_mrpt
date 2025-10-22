# Production Deployment Guide - AWS Console Method

## Important: Production Architecture Update
Production is now using Auto Scaling Group (ASG) with instances behind an Application Load Balancer.
- Direct SSH to 3.137.158.17 is no longer available
- Current ASG Instance: i-06d3edfcc85a1f1c7
- Access via AWS Systems Manager or EC2 Instance Connect

## Deployment Steps

### Step 1: Access Production Instance via AWS Console

1. Go to AWS Console → EC2 → Instances
2. Find instance ID: `i-06d3edfcc85a1f1c7` (ASG instance)
3. Select the instance and click "Connect"
4. Choose "Session Manager" (recommended) or "EC2 Instance Connect"

### Step 2: Create Backups
Once connected, run:
```bash
cd /home/ec2-user/ChatMRPT
sudo cp app/core/unified_data_state.py app/core/unified_data_state.py.backup_$(date +%Y%m%d_%H%M%S)
sudo cp app/core/analysis_state_handler.py app/core/analysis_state_handler.py.backup_$(date +%Y%m%d_%H%M%S)
sudo cp app/core/request_interpreter.py app/core/request_interpreter.py.backup_$(date +%Y%m%d_%H%M%S)
sudo cp gunicorn.conf.py gunicorn.conf.py.backup_$(date +%Y%m%d_%H%M%S)
```

### Step 3: Apply the Fixes

#### Fix 1: unified_data_state.py
Edit `/home/ec2-user/ChatMRPT/app/core/unified_data_state.py`:
- Around line 28: Comment out or remove `_states = {}`
- Around line 39-42: Remove the caching logic in `get_state()`

#### Fix 2: analysis_state_handler.py
Edit `/home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py`:
- Remove the singleton pattern (lines 14-21)
- Remove `_instance` and `__new__` method

#### Fix 3: request_interpreter.py (CRITICAL)
Edit `/home/ec2-user/ChatMRPT/app/core/request_interpreter.py`:
- Find the `_get_session_context()` method (around line 1536)
- After getting `analysis_complete` from session, add:

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

#### Fix 4: Update Workers
Edit `/home/ec2-user/ChatMRPT/gunicorn.conf.py`:
```python
workers = 6  # was 4
```

### Step 4: Restart Service
```bash
# Test syntax
python3 -m py_compile app/core/unified_data_state.py
python3 -m py_compile app/core/analysis_state_handler.py
python3 -m py_compile app/core/request_interpreter.py

# Restart service
sudo systemctl restart chatmrpt

# Verify
sleep 10
ps aux | grep gunicorn | grep -v grep | wc -l  # Should show 7 (1 master + 6 workers)
```

### Alternative: Copy from Staging

If you can SSH between instances within AWS:
```bash
# From production instance, copy from staging
scp ec2-user@18.117.115.217:/home/ec2-user/ChatMRPT/app/core/unified_data_state.py /tmp/
scp ec2-user@18.117.115.217:/home/ec2-user/ChatMRPT/app/core/analysis_state_handler.py /tmp/
scp ec2-user@18.117.115.217:/home/ec2-user/ChatMRPT/app/core/request_interpreter.py /tmp/
scp ec2-user@18.117.115.217:/home/ec2-user/ChatMRPT/gunicorn.conf.py /tmp/

# Copy to correct locations
sudo cp /tmp/*.py /home/ec2-user/ChatMRPT/app/core/
sudo cp /tmp/gunicorn.conf.py /home/ec2-user/ChatMRPT/
```

## Verification
Test at: http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com

1. Upload data and run risk analysis
2. Verify ITN planning detects completed analysis
3. Check maps and visualizations work

## Important Notes
- ASG will maintain this configuration across instance replacements
- Consider updating the AMI after successful deployment
- CloudFront URL also available: https://d225ar6c86586s.cloudfront.net