# Deploy 2-Route Architecture Refactor

## Date: 2025-10-12

## Changes Being Deployed:
1. **tpr_language_interface.py** - Simplified from 7-intent classification to command extraction
2. **data_analysis_v3_routes.py** - Implemented 2-route logic (commands vs queries)
3. **workflow_manager.py** - Removed 298 lines of intent logic, added execute methods

## Production Instances:
- Instance 1: 3.21.167.170
- Instance 2: 18.220.103.20

## Quick Deployment (Automated):

```bash
# Option 1: Use the deployment script
cd /mnt/c/Users/bbofo/OneDrive/Desktop/ChatMRPT
./deployment/deploy_2route_refactor.sh
```

## Manual Deployment:

### Step 1: Set up SSH key
```bash
# Copy your SSH key to /tmp (adjust path if needed)
cp <path-to-your-chatmrpt-key.pem> /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem
```

### Step 2: Deploy to Instance 1 (3.21.167.170)
```bash
KEY="/tmp/chatmrpt-key2.pem"
INSTANCE1="3.21.167.170"

# Copy files
scp -i "$KEY" app/data_analysis_v3/core/tpr_language_interface.py \
    ec2-user@$INSTANCE1:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/

scp -i "$KEY" app/web/routes/data_analysis_v3_routes.py \
    ec2-user@$INSTANCE1:/home/ec2-user/ChatMRPT/app/web/routes/

scp -i "$KEY" app/data_analysis_v3/tpr/workflow_manager.py \
    ec2-user@$INSTANCE1:/home/ec2-user/ChatMRPT/app/data_analysis_v3/tpr/

# Restart service
ssh -i "$KEY" ec2-user@$INSTANCE1 'sudo systemctl restart chatmrpt'

# Check status
ssh -i "$KEY" ec2-user@$INSTANCE1 'sudo systemctl status chatmrpt --no-pager'
```

### Step 3: Deploy to Instance 2 (18.220.103.20)
```bash
INSTANCE2="18.220.103.20"

# Copy files
scp -i "$KEY" app/data_analysis_v3/core/tpr_language_interface.py \
    ec2-user@$INSTANCE2:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/

scp -i "$KEY" app/web/routes/data_analysis_v3_routes.py \
    ec2-user@$INSTANCE2:/home/ec2-user/ChatMRPT/app/web/routes/

scp -i "$KEY" app/data_analysis_v3/tpr/workflow_manager.py \
    ec2-user@$INSTANCE2:/home/ec2-user/ChatMRPT/app/data_analysis_v3/tpr/

# Restart service
ssh -i "$KEY" ec2-user@$INSTANCE2 'sudo systemctl restart chatmrpt'

# Check status
ssh -i "$KEY" ec2-user@$INSTANCE2 'sudo systemctl status chatmrpt --no-pager'
```

## Verify Deployment:

```bash
# Check logs on both instances
ssh -i "$KEY" ec2-user@3.21.167.170 'sudo journalctl -u chatmrpt -f'
ssh -i "$KEY" ec2-user@18.220.103.20 'sudo journalctl -u chatmrpt -f'
```

## Test Cases:

After deployment, test these scenarios:

### 1. Command Extraction (Natural Language)
- Input: "primary"
- Expected: Executes facility selection
- Input: "Let's go with primary"
- Expected: Extracts 'primary' and executes
- Input: "over five years"
- Expected: Extracts 'o5' and executes (Issue #3 fixed)

### 2. Agent Queries (Issue #1 & #2)
- Input: "explain the differences"
- Expected: Agent provides rich explanation, not shallow hardcoded response
- Input: "tell me about variables"
- Expected: Agent accesses data and lists actual column names
- Input: "what variables do I have?"
- Expected: Agent returns actual columns from uploaded data

### 3. End-to-End Workflow
- Upload TPR data → Start TPR workflow → Select state → Select facility → Select age
- Expected: Smooth progression, correct response format, TPR calculation completes

## Rollback Plan:

If issues occur, restore from latest backup:

```bash
# Restore Instance 1
ssh -i "$KEY" ec2-user@3.21.167.170 'cd /home/ec2-user && sudo systemctl stop chatmrpt && rm -rf ChatMRPT.broken && mv ChatMRPT ChatMRPT.broken && tar -xzf ChatMRPT_BEFORE_ARENA_FIX_20251006.tar.gz && sudo systemctl start chatmrpt'

# Restore Instance 2
ssh -i "$KEY" ec2-user@18.220.103.20 'cd /home/ec2-user && sudo systemctl stop chatmrpt && rm -rf ChatMRPT.broken && mv ChatMRPT ChatMRPT.broken && tar -xzf ChatMRPT_BEFORE_ARENA_FIX_20251006.tar.gz && sudo systemctl start chatmrpt'
```

## Access Points:
- CloudFront HTTPS: https://d225ar6c86586s.cloudfront.net
- Instance 1 Direct: http://3.21.167.170
- Instance 2 Direct: http://18.220.103.20

## Summary of Fixes:
✅ Issue #1: "explain differences" now routes to agent (rich responses)
✅ Issue #2: "tell me about variables" routes to agent (data access)
✅ Issue #3: "over five years" now returns correct response format
✅ Preserved natural language support via LLM command extraction
