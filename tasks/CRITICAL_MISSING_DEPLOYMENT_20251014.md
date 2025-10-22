# CRITICAL: Missing TPR Workflow Deployment

**Date**: October 14, 2025
**Issue**: Partial deployment - Frontend fix deployed, but critical backend changes NOT deployed
**Impact**: TPR workflow broken in production, visualizations not showing, no workflow transition

---

## What Went Wrong

I deployed the files mentioned in `deployment_notes.txt` but **DID NOT deploy the actual backend TPR workflow changes** that were already in your local codebase!

### Files I Deployed (Oct 14, 02:26 UTC)
1. ✅ `app/core/tool_intent_resolver.py` (NEW - 490 lines)
2. ✅ `app/core/request_interpreter.py` (MODIFIED - 2,328 lines)
3. ✅ `frontend/src/hooks/useMessageStreaming.ts` (MODIFIED - 370 lines)

### Files I SHOULD HAVE Deployed (Already in local codebase)
1. ❌ `app/data_analysis_v3/core/tpr_workflow_handler.py` - Contains `exit_data_analysis_mode=True` logic!
2. ❌ Possibly other data_analysis_v3 files with related changes

---

## Evidence from Local Code

### TPR Workflow Handler (lines 1358-1368)
```python
# ✅ AUTO-TRANSITION: Trigger risk analysis transition immediately!
logger.info("✅ Auto-transition successful - combining TPR results with menu")
logger.info(f"🔍 CRITICAL: visualizations before creating response: {visualizations}")
logger.info(f"🔍 CRITICAL: visualizations length: {len(visualizations)}")

# Combine TPR results message with transition menu
combined_message = message + "\n\n" + transition_result['message']

# Update the response to include transition flag and combined message
response = {
    "success": True,
    "message": combined_message,
    "session_id": self.session_id,
    "workflow": "data_upload",  # Changed from "tpr" to "data_upload"
    "stage": "complete",
    "visualizations": visualizations,  # ← Visualizations included!
    "exit_data_analysis_mode": True,  # ← CRITICAL FLAG!
    "debug": {
        "selections": self.tpr_selections,
```

### trigger_risk_analysis() Method (line 543)
```python
return {
    "success": True,
    "message": message,
    "session_id": self.session_id,
    "workflow": "data_upload",
    "stage": "complete",
    "transition": "tpr_to_upload",
    "exit_data_analysis_mode": True  # ← Signal frontend to exit Data Analysis mode
}
```

---

## User's Production Issues (From contxt.md)

### Issue #1: TPR Completion - No Visualization (Line 172-185)
```
Line 172: ✅ DATA ANALYSIS V3 RESPONSE
Line 173:   Success: true
Line 174:   Exit Data Analysis Mode: undefined  ← SHOULD BE true!
Line 175:   Has Message: true
Line 176:   Has Redirect Message: false
Line 177:   Workflow: tpr
Line 178:   Stage: COMPLETE
Line 179:   Message Preview: ## TPR Analysis Complete...
```

**Expected**: `Exit Data Analysis Mode: true` with visualizations array
**Actual**: `Exit Data Analysis Mode: undefined`, no visualizations
**Cause**: tpr_workflow_handler.py NOT deployed, old version running

### Issue #2: Blank Maps (Lines 212-256, 313-421)
```
Line 313: Uncaught (in promise) Error: unexpected error while fetching topojson file at https://cdn.plot.ly/world_110m.json
Lines 213-244: Refused to connect to 'URL' because it violates Content Security Policy directive
```

**Expected**: Maps render with Plotly basemap tiles
**Actual**: Maps fail to load external CDN resources
**Cause**: CloudFront/ALB Content Security Policy blocking cdn.plot.ly
**Note**: This is a SEPARATE infrastructure issue, not related to the deployment

### Issue #3: Risk Analysis Not Working (Line 373-398)
```
Line 373: User: "Run malaria risk analysis"
Line 394: System: "The malaria risk analysis preparation is complete. Here are some insights from the data:
### TPR (Test Positivity Rate)
Mean TPR: 24.15%..."
```

**Expected**: Execute malaria risk analysis tool, generate vulnerability maps
**Actual**: Generic data statistics without running the actual tool
**Cause**: Possibly still in Data Analysis mode (should have exited), OR intent resolver not matching

---

## Action Plan

### Step 1: Deploy Missing TPR Workflow Handler
Deploy the file that actually sets the exit flag and includes visualizations:

**File**: `app/data_analysis_v3/core/tpr_workflow_handler.py` (1,684 lines)
**Critical Changes**:
- Line 1365: `"exit_data_analysis_mode": True` in calculate_tpr()
- Line 1364: `"visualizations": visualizations` preserved in response
- Line 543: `"exit_data_analysis_mode": True` in trigger_risk_analysis()
- Lines 1300-1308: Visualization object creation for TPR map

### Step 2: Fix CSP Configuration for Plotly Maps
**Problem**: CloudFront CSP blocks `https://cdn.plot.ly/world_110m.json`

**Options**:
1. Add `cdn.plot.ly` to CloudFront allowed origins
2. OR bundle Plotly.js locally instead of using CDN
3. OR use self-hosted topojson files

**Recommended**: Update CloudFront response headers policy to allow:
```
Content-Security-Policy:
  connect-src 'self' https://cdn.plot.ly *.plot.ly;
  script-src 'self' https://cdn.plot.ly 'unsafe-inline' 'unsafe-eval';
```

### Step 3: Verify Risk Analysis Tool Routing
**Check**:
1. Is intent resolver matching "run malaria risk analysis"?
2. Is the tool actually being called or just returning cached statistics?
3. Are there any errors in the tool execution?

**Expected Intent Resolver Match** (from tool_intent_resolver.py lines 278-309):
```python
def _handle_risk_analysis(self, text, tokens, session_context):
    matched = []
    if "risk" in tokens:
        matched.append("risk")
    if "analysis" in tokens or "assess" in tokens:
        matched.append("analysis")
    if "rank" in tokens and ("ward" in tokens or "wards" in tokens):
        matched.extend(["rank", "ward"])
    score = 1.0 * len(matched)  # "run malaria risk analysis" → 2.0 points
```

**Score for "run malaria risk analysis"**:
- "risk" in tokens → +1.0
- "analysis" in tokens → +1.0
- Total: 2.0 (exceeds 1.8 threshold)

Should match! But need to check if it's actually executing.

---

## Deployment Commands

### Deploy TPR Workflow Handler
```bash
# Copy key if needed
cp aws_files/chatmrpt-key.pem /tmp/chatmrpt-key2.pem
chmod 600 /tmp/chatmrpt-key2.pem

# Deploy to both instances
scp -i /tmp/chatmrpt-key2.pem app/data_analysis_v3/core/tpr_workflow_handler.py ec2-user@3.21.167.170:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/
scp -i /tmp/chatmrpt-key2.pem app/data_analysis_v3/core/tpr_workflow_handler.py ec2-user@18.220.103.20:/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/

# Clear cache and restart on both instances
for ip in 3.21.167.170 18.220.103.20; do
    ssh -i /tmp/chatmrpt-key2.pem ec2-user@$ip "
        cd /home/ec2-user/ChatMRPT
        find app -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
        find app -name '*.pyc' -delete 2>/dev/null || true
        sudo systemctl restart chatmrpt
    "
done
```

---

## Expected Results After Fix

### Issue #1: TPR Completion (FIXED)
```json
{
  "success": true,
  "exit_data_analysis_mode": true,  // ← NOW PRESENT!
  "message": "## TPR Analysis Complete\n\n...You can now:\n- Map variable distribution...",
  "visualizations": [
    {
      "type": "iframe",
      "url": "/serve_viz_file/session_id/tpr_distribution_map.html",
      "title": "TPR Distribution - State",
      "height": 600
    }
  ],
  "workflow": "data_upload",
  "stage": "complete"
}
```

### Issue #2: Blank Maps (REQUIRES CSP FIX)
After CSP update, Plotly maps should load successfully without:
- ❌ "Refused to connect" errors
- ❌ "unexpected error while fetching topojson" errors

### Issue #3: Risk Analysis (NEEDS INVESTIGATION)
After deployment, test:
1. Complete TPR workflow
2. Say "run malaria risk analysis"
3. Verify tool_intent_resolver matches and executes

---

## Root Cause Analysis

### Why This Happened
1. **Incomplete deployment_notes.txt**: Mentioned changes but didn't list all affected files
2. **Assumed local = deployed**: I assumed your local code was already in production
3. **No file manifest**: deployment_notes.txt didn't have a complete file list

### Prevention
1. **Always list ALL files** in deployment notes with checksums
2. **Compare local vs production** before deployment
3. **Test in staging first** if available
4. **Verify all changes** deployed before marking complete

---

## Next Steps

1. Deploy `tpr_workflow_handler.py` to both instances
2. Test TPR workflow end-to-end
3. Fix CSP configuration for Plotly maps (separate task)
4. Investigate risk analysis routing issue
5. Create backup before any fixes

---

**Created**: October 14, 2025, 02:45 UTC
**Status**: ⚠️ **CRITICAL - REQUIRES IMMEDIATE DEPLOYMENT**
