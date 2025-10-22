# TPR Workflow Fixes Summary

## Issues Identified and Fixed

### 1. Redis Not Installed (Primary Issue)
**Problem**: Multi-worker Gunicorn environment couldn't share filesystem sessions
**Solution**: 
- Installed Redis 6 on AWS
- Configured Flask to use Redis for session storage
- Sessions now shared across all 4 workers

### 2. Stage Map Bug in TPR Handler
**Problem**: The restore mechanism had a bug in the stage_map:
```python
# BEFORE (incorrect):
'age_selection': ConversationStage.AGE_GROUP_SELECTION

# AFTER (correct):
'age_group_selection': ConversationStage.AGE_GROUP_SELECTION
```
**Impact**: When restoring session state, the conversation manager's stage wasn't being set correctly, causing it to fall through to `_handle_general_query`
**Solution**: Fixed the stage_map to use correct key names

### 3. Enhanced Debug Logging
Added logging to track stage restoration:
- Logs when conversation stage is successfully restored
- Warns when unknown workflow stage is encountered
- Helps diagnose future issues

## How These Issues Caused the Problem

1. User uploads TPR file → Worker A processes it
2. User types "Adamawa State" → Load balancer routes to Worker B
3. Worker B creates new TPR handler and conversation manager
4. Without Redis: Worker B can't see session data from Worker A
5. With Redis but stage_map bug: Conversation stage not restored correctly
6. Result: Falls through to `_handle_general_query` → "I understand you're asking about..."

## Current Status
✅ Redis installed and working
✅ Flask sessions stored in Redis
✅ Stage map bug fixed
✅ Debug logging added
✅ Service restarted with all fixes

## Testing Instructions
1. Visit http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/
2. Upload NMEP TPR file
3. When prompted, type "Adamawa State"
4. Should proceed to facility selection (not generic message)

## Monitoring Commands
```bash
# Watch Redis activity
ssh -i aws_files/chatmrpt-key.pem ec2-user@3.137.158.17 'redis6-cli monitor'

# Check TPR logs
ssh -i aws_files/chatmrpt-key.pem ec2-user@3.137.158.17 'sudo journalctl -u chatmrpt -f | grep -i tpr'

# Check session restoration logs
ssh -i aws_files/chatmrpt-key.pem ec2-user@3.137.158.17 'sudo journalctl -u chatmrpt -f | grep "Restored conversation stage"'
```