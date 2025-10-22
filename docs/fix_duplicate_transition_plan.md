# Fix Duplicate Transition Messages - Comprehensive Plan

## Problem Analysis
When user says "yes" to proceed from TPR to risk analysis:
1. V3 agent correctly returns `exit_data_analysis_mode: true` with exploration menu ✅
2. Frontend correctly displays the first menu ✅
3. OLD TPR code in message-handler.js triggers ANOTHER `__DATA_UPLOADED__` ❌
4. This causes DUPLICATE exploration menu ❌

## Files to Modify

### 1. **app/static/js/modules/chat/core/message-handler.js**
**Lines to DELETE: 183-199**
```javascript
// DELETE THIS ENTIRE BLOCK - IT'S OLD TPR LOGIC
if (fullResponse.trigger_data_uploaded) {
    console.log('🎯 TPR complete - triggering data exploration menu');
    setTimeout(() => {
        this.sendMessage('__DATA_UPLOADED__');
    }, 2000);
}

// DELETE THIS TOO
if (fullResponse.trigger_exploration && fullResponse.response === '__DATA_UPLOADED__') {
    console.log('🎯 TPR triggering exploration workflow');
    setTimeout(() => {
        this.sendMessage('__DATA_UPLOADED__');
    }, 100);
}
```

### 2. **app/static/js/modules/utils/api-client.js**
**Keep current code but ADD cache busting:**
- Line 165-169: Current code is correct (doesn't send duplicate)
- But browser may have cached old version

### 3. **app/templates/index.html** (or wherever JS is loaded)
**Add cache busting to force reload:**
```html
<script src="/static/js/modules/chat/core/message-handler.js?v={{ timestamp }}"></script>
<script src="/static/js/modules/utils/api-client.js?v={{ timestamp }}"></script>
```

## Production's Approach
Production uses old tpr_module which:
1. Completes TPR calculation
2. Returns a simple redirect to upload workflow
3. Does NOT have Data Analysis V3 complexity
4. Does NOT have multiple places triggering `__DATA_UPLOADED__`

## What We're Implementing
1. V3 agent handles ENTIRE transition (already does ✅)
2. Frontend just displays what V3 sends (no extra triggers)
3. Remove ALL automatic `__DATA_UPLOADED__` triggers from frontend
4. Let the backend control the flow completely

## Testing Steps
1. Upload TPR data
2. Complete TPR calculation
3. Say "yes" to proceed
4. Should see exploration menu ONCE
5. Check console for no duplicate "Sending redirect message"