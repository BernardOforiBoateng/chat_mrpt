# Debug Logging Guide for ChatMRPT

## Overview
Comprehensive debug logging has been added throughout the ChatMRPT workflow to help identify and resolve issues.

## How to View Logs

### Frontend (Browser Console)
Open browser DevTools (F12) and look for logs with these prefixes:
- `🎯 FRONTEND:` - User actions and UI events
- `📝 Message:` - User messages being sent
- `🔍 Data Analysis Mode:` - Current mode state
- `🆔 Session ID:` - Current session identifier
- `🌐 Using endpoint:` - Which backend endpoint is being called

### Backend (Server Logs)
SSH into AWS instances and run:
```bash
sudo journalctl -u chatmrpt -f
```

Look for these log prefixes:
- `🔧 BACKEND:` - Route hits and API endpoints
- `📊 ANALYSIS:` - Risk analysis workflow steps
- `🔄 TPR:` - TPR workflow state transitions
- `🛏️ ITN:` - ITN planning tool execution
- `⚡ TOOL:` - Individual tool executions
- `🆔 SESSION:` - Session state information

## Log Format Structure

### Request Logging
```
========================================================
🔧 BACKEND: /send_message_streaming endpoint hit
  📝 User Message: [first 100 chars of message]
  🆔 Session ID: [session_id]
  📂 Session Keys: [list of session keys]
  🎯 Analysis Complete: [true/false]
  📊 Data Loaded: [true/false]
  🔄 TPR Complete: [true/false]
========================================================
```

### Tool Execution Logging
```
⚡ TOOL: _run_complete_analysis called
  🆔 Session ID: [session_id]
  📊 Variables: [list of variables]
```

### TPR Workflow Logging
```
========================================================
🔄 TPR: handle_workflow called
  📝 Query: [user query]
  🎯 Current Stage: [TPR stage]
  🆔 Session ID: [session_id]
  📊 Selections: {state: X, facility_level: Y, age_group: Z}
========================================================
```

## Workflow States to Monitor

### Risk Analysis Workflow
1. Data Upload
2. Analysis Triggered
3. Tool Execution
4. Results Generated
5. Visualization Created

### TPR Workflow
1. TPR_STATE_SELECTION
2. TPR_FACILITY_LEVEL
3. TPR_AGE_GROUP
4. TPR_CALCULATING
5. TPR_COMPLETE

### ITN Planning
1. Check Analysis Complete
2. Validate Parameters
3. Calculate Distribution
4. Generate Map
5. Create Exports

## Common Issues to Look For

### Session State Issues
- `Analysis Complete: False` when it should be True
- Missing session keys
- Session ID mismatches

### Tool Execution Failures
- Tool not found errors
- Missing parameters
- Data not loaded

### Workflow Transitions
- Stuck in wrong stage
- Stage not updating
- Selections not being saved

## Debug Utility Functions

The `app/core/debug_logger.py` module provides:
- `WorkflowDebugger` class for structured logging
- `@debug_route` decorator for automatic route logging
- `@debug_tool` decorator for tool execution logging
- Helper functions for logging specific events

## Deployment Locations
Debug logging is active on:
- Production Instance 1: 3.21.167.170
- Production Instance 2: 18.220.103.20
- CloudFront: https://d225ar6c86586s.cloudfront.net

## Monitoring Tips

1. **For Risk Analysis Issues:**
   - Check if `analysis_complete` flag is being set
   - Verify tool executions are completing
   - Look for file creation logs

2. **For TPR Workflow Issues:**
   - Track stage transitions
   - Verify selections are being saved
   - Check if files are being created

3. **For ITN Planning Issues:**
   - Confirm analysis is complete before ITN
   - Check parameter extraction
   - Verify export generation

4. **For Download Issues:**
   - Check `/export/list/` endpoint calls
   - Verify files exist in uploads/exports directories
   - Look for file path errors

## Real-time Monitoring Commands

```bash
# Watch for specific workflows
sudo journalctl -u chatmrpt -f | grep "TPR:"
sudo journalctl -u chatmrpt -f | grep "ANALYSIS:"
sudo journalctl -u chatmrpt -f | grep "ITN:"

# Watch for errors
sudo journalctl -u chatmrpt -f | grep "ERROR"

# Monitor specific session
sudo journalctl -u chatmrpt -f | grep "session_id_here"
```

## Browser Console Commands

```javascript
// Check current session
console.log(localStorage.getItem('sessionId'))

// Monitor network requests
// Go to Network tab and filter by 'Fetch/XHR'

// Check React state (if React DevTools installed)
// Go to Components tab and search for relevant components
```

## Next Steps

With this logging in place, you can now:
1. Run through workflows and watch the logs
2. Identify exactly where issues occur
3. See the full context when problems happen
4. Track session state across the entire flow

The logs will help explain issues better by showing:
- What the user did (frontend logs)
- What the backend received (route logs)
- What tools were executed (tool logs)
- What state transitions occurred (workflow logs)
- Any errors with full context