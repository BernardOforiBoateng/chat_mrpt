# Test Case: Option 2 TPR Workflow Issue

## Steps to Reproduce

1. **Open ChatMRPT**
   - Navigate to https://d225ar6c86586s.cloudfront.net

2. **Upload Data**
   - Click upload button
   - Select "Data Analysis" tab
   - Upload a CSV file with TPR data

3. **Observe Initial Response** ✅
   - Analysis summary appears (fixed in previous issue)
   - Menu shows:
     ```
     1️⃣ Explore the data
     2️⃣ Calculate Test Positivity Rate (TPR)
     3️⃣ Quick Overview
     ```

4. **Select Option 2** ❌
   - Type "2" in the input box
   - Press Enter

## Expected Result
- TPR workflow should start
- System should ask for age group selection
- Guide through TPR calculation process

## Actual Result  
- Nothing happens
- Message "2" may appear in chat
- No TPR workflow initiated
- System doesn't respond with TPR options

## Root Cause
- Message "2" is sent to `/send_message_streaming` (regular chat)
- Should be sent to `/api/v1/data-analysis/chat`
- Frontend doesn't track data analysis mode

## Browser Console Evidence
Look for:
```javascript
// After typing "2":
// You'll see normal message sending, NOT data analysis API call
// Missing: "Triggering data analysis chat API"
```

## Network Tab Evidence
After typing "2":
- ❌ Request to `/send_message_streaming`
- ✅ Should be request to `/api/v1/data-analysis/chat`

## Quick Verification
```javascript
// In browser console after upload:
useAnalysisStore.getState().dataAnalysisMode
// Returns: false (should be true!)
```

## Fix Verification
After fix is applied:
1. Repeat steps 1-4
2. Option 2 should trigger TPR workflow
3. Console should show data analysis API calls
4. TPR age selection menu should appear