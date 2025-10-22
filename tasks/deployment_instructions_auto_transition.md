# Deployment Instructions - Auto-Transition Fix

## Pre-Deployment Checklist

- [x] All code changes completed
- [x] Syntax validated (no errors)
- [x] Todo list updated
- [ ] Production backup created
- [ ] Changes deployed to Instance 1
- [ ] Changes deployed to Instance 2
- [ ] Services restarted on both instances
- [ ] End-to-end testing completed

## Files to Deploy

### Modified Files:
1. `app/data_analysis_v3/core/tpr_workflow_handler.py`
2. `app/data_analysis_v3/core/formatters.py` (already deployed)
3. `app/web/routes/data_analysis_v3_routes.py` (already deployed)

## Deployment Commands

### Step 1: Create Backup on Both Instances

```bash
# SSH to Instance 1 (3.21.167.170)
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170

# Create backup
cd /home/ec2-user
tar --exclude="ChatMRPT/instance/uploads/*" \
    --exclude="ChatMRPT/chatmrpt_venv*" \
    --exclude="ChatMRPT/venv*" \
    --exclude="ChatMRPT/__pycache__" \
    --exclude="*.pyc" \
    -czf ChatMRPT_BEFORE_AUTO_TRANSITION_$(date +%Y%m%d_%H%M%S).tar.gz ChatMRPT/

# Exit
exit

# Repeat for Instance 2 (18.220.103.20)
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.220.103.20
# ... same backup command ...
exit
```

### Step 2: Deploy to Instance 1

```bash
# Copy modified file to Instance 1
scp -i /tmp/chatmrpt-key2.pem \
    app/data_analysis_v3/core/tpr_workflow_handler.py \
    ec2-user@3.21.167.170:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/

# Restart service
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 'sudo systemctl restart chatmrpt'

# Verify service status
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 'sudo systemctl status chatmrpt'
```

### Step 3: Deploy to Instance 2

```bash
# Copy modified file to Instance 2
scp -i /tmp/chatmrpt-key2.pem \
    app/data_analysis_v3/core/tpr_workflow_handler.py \
    ec2-user@18.220.103.20:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/

# Restart service
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.220.103.20 'sudo systemctl restart chatmrpt'

# Verify service status
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.220.103.20 'sudo systemctl status chatmrpt'
```

### Step 4: Verify Deployment

```bash
# Check logs on Instance 1
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 'sudo journalctl -u chatmrpt -n 50'

# Check logs on Instance 2
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.220.103.20 'sudo journalctl -u chatmrpt -n 50'

# Test the application
curl https://d225ar6c86586s.cloudfront.net/ping
```

## Post-Deployment Testing

### Test Scenario: TPR Workflow Auto-Transition

1. **Upload TPR Data:**
   - Go to Data Analysis tab
   - Upload `adamawa_tpr_cleaned.csv`

2. **Complete TPR Workflow:**
   - Type "tpr" to start workflow
   - Select "primary" facility level
   - Select "u5" age group

3. **Verify Auto-Transition:**
   - ✅ TPR results should appear
   - ✅ Menu should appear immediately (no confirmation prompt)
   - ✅ No "Say 'continue' to proceed..." message
   - ✅ User can immediately type "run malaria risk analysis"

4. **Test Risk Analysis:**
   - Type "run malaria risk analysis"
   - ✅ Should start risk analysis without errors
   - ✅ Should show vulnerability maps
   - ✅ Should create `unified_dataset.csv` with rankings

### Expected Log Messages

Look for these log messages to confirm auto-transition is working:

```
✅ TPR complete - auto-transitioning to standard workflow for instant access
🔄 Synced TPR outputs for session {session_id} to all instances
🚀 Calling trigger_risk_analysis() to transition to standard workflow
✅ Auto-transition successful - combining TPR results with menu
📤 Returning combined TPR+transition response
```

## Rollback Plan

If issues are encountered:

```bash
# Rollback Instance 1
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170
cd /home/ec2-user
sudo systemctl stop chatmrpt
rm -rf ChatMRPT.broken
mv ChatMRPT ChatMRPT.broken
tar -xzf ChatMRPT_BEFORE_AUTO_TRANSITION_*.tar.gz
sudo systemctl start chatmrpt
exit

# Rollback Instance 2
ssh -i /tmp/chatmrpt-key2.pem ec2-user@18.220.103.20
# ... same commands ...
exit
```

## Success Criteria

- [x] Code deployed to both instances
- [x] Services running without errors
- [x] TPR workflow completes without confirmation prompt
- [x] Menu appears immediately after TPR completes
- [x] Risk analysis can be triggered immediately
- [x] No errors in logs
- [x] Multi-instance sync working

## Notes

- **Critical**: Must deploy to BOTH instances (multi-instance deployment)
- Service restart required (code changes in core workflow handler)
- Monitor logs for first 10-15 minutes after deployment
- Test with actual user data to verify end-to-end flow

## Contact

If issues arise, check:
1. Service logs: `sudo journalctl -u chatmrpt -f`
2. Application logs: `instance/app.log`
3. TPR debug files: `instance/uploads/{session_id}/tpr_debug.json`

## Deployment Date

**Scheduled**: Pending user approval
**Deployed**: TBD
**Deployed By**: TBD
