# TPR Workflow Test Checklist

## What Was Fixed
1. ✅ Added serialization methods to TPRStateManager
2. ✅ Implemented file-based storage for parsed Excel data
3. ✅ Integrated session loading/saving in TPRHandler
4. ✅ Removed in-memory handler caching
5. ✅ All state now persists via Redis-backed sessions

## Test URL
http://chatmrpt-alb-319454030.us-east-2.elb.amazonaws.com/

## Test Steps

### 1. File Upload Test
- [ ] Upload NMEP TPR Excel file
- [ ] Should see "NMEP TPR file uploaded successfully!"
- [ ] Should see analysis summary with states

### 2. State Selection Test
- [ ] Type state name (e.g., "Adamawa State" or "Kwara State")
- [ ] Should proceed to state overview (NOT generic message)
- [ ] Should show facility distribution and data quality

### 3. Facility Confirmation Test
- [ ] Type "yes" or "proceed with TPR calculation"
- [ ] Should proceed to facility type selection
- [ ] Should NOT get generic "I understand..." message

### 4. Facility Type Selection Test
- [ ] Type "Primary" or "Use Primary Health Facilities only"
- [ ] Should proceed to age group selection
- [ ] Should show data availability for each age group

### 5. Age Group Selection Test
- [ ] Type "Under 5" or "Under 5 years"
- [ ] Should start TPR calculation
- [ ] Should complete and show download options

### 6. Multi-Worker Test
- [ ] Refresh browser mid-workflow
- [ ] Workflow should continue from where it left off
- [ ] State should be preserved

### 7. Concurrent User Test
- [ ] Open in different browser/incognito
- [ ] Run separate TPR analysis
- [ ] Should not interfere with each other

## Monitoring Commands

### Watch Session Storage
```bash
ssh -i aws_files/chatmrpt-key.pem ec2-user@3.137.158.17 'sudo journalctl -u chatmrpt -f | grep -E "Saved state to session|Loaded existing state|Saved TPR state"'
```

### Monitor Redis Activity
```bash
ssh -i aws_files/chatmrpt-key.pem ec2-user@3.137.158.17 'redis6-cli monitor | grep tpr_states'
```

### Check for Errors
```bash
ssh -i aws_files/chatmrpt-key.pem ec2-user@3.137.158.17 'sudo journalctl -u chatmrpt -f | grep -i error'
```

## Expected Results
- ✅ No "I understand you're asking about..." messages at any stage
- ✅ Workflow completes successfully
- ✅ State persists across page refreshes
- ✅ Multiple users can use TPR simultaneously

## If Issues Occur
1. Check logs for error messages
2. Verify Redis is storing session data
3. Check if parsed data files are being created in instance/uploads/{session_id}/