# Concurrent Session Investigation Findings

## Executive Summary
Critical P0 issue identified: All concurrent users share the same session ID, causing data bleed and inconsistent behavior. Two major issues found:

1. **Session ID Reuse** - Frontend persists and reuses session IDs via localStorage
2. **Deployment Inconsistency** - Different instances running different code versions

## ROOT CAUSE 1: Session ID Persistence in Frontend

### Evidence
- ALL 5 test runs used identical session ID: `f4ab9a14-e7c4-47e6-bb70-eeb21f99dbc2`
- Session IDs logged at lines: 96, 270, 513, 773, 1010 in context.md

### Problem Location
**Frontend (React/JavaScript):**
- The React app stores session IDs in localStorage (`localStorage.setItem("session_id", sessionId)`)
- Uses Zustand store with persistence via `chat-storage` key
- When a user uploads a file, the backend returns a session ID
- This session ID gets stored in localStorage and reused for ALL subsequent uploads
- Even concurrent uploads from different tabs/windows reuse the same stored session ID

### Impact
- All concurrent users share the same session directory (`instance/uploads/{session_id}/`)
- Data files overwrite each other
- State bleeds between sessions
- Users see each other's data

## ROOT CAUSE 2: Inconsistent Code Deployment

### Evidence
- RUNs 1-3: Show OLD workflow with 'show facilities', 'show tests' prompts
- RUNs 4-5: Show NEW progressive disclosure format with actual TPR calculations
- RUN 2 uploaded `kebbi_tpr_cleaned.csv` but reports "All data is from Benue"

### Problem
- 2 production instances: 3.21.167.170 and 18.220.103.20
- 6 Gunicorn workers per instance
- Some instances/workers have old code, some have new code
- Load balancer randomly distributes requests → users see different versions

## ROOT CAUSE 3: Backend Session Generation Issues

### `/api/data-analysis/upload` (line 35):
```python
session_id = session.get('session_id')
if not session_id:
    session_id = request.form.get('session_id', f'session_{os.urandom(8).hex()}')
```
- Falls back to form data session_id (which frontend provides from localStorage)
- Only generates new ID if both Flask session AND form data are empty

### `/upload_both_files` decorator chain:
- `@validate_session` decorator generates UUID only if session.get('session_id') is None
- But if frontend sends the old session_id, it gets reused

## Data Contamination Chain
1. User 1 uploads `benue_tpr_cleaned.csv` → gets session `f4ab9a14...`
2. Session ID stored in localStorage
3. User opens new tab/window for concurrent test
4. New tab reads same localStorage → sends same session ID
5. All uploads go to same directory → files overwrite each other
6. Different workers/instances serve different code versions
7. Result: Data bleed + inconsistent UI

## Critical Files Affected
- Frontend: `app/static/react/assets/index-DMqRx-uT.js` (Zustand store with localStorage)
- Backend: `app/web/routes/data_analysis_v3_routes.py` (session handling)
- Backend: `app/web/routes/upload_routes.py` (file upload handling)
- Backend: `app/core/decorators.py` (validate_session decorator)

## Why Individual Runs Work
- Single user = single session ID = no conflicts
- No concurrent access to same session directory
- Consistent code version throughout single session

## Severity Assessment
**CRITICAL P0** - System is unsafe for production with multiple concurrent users
- Data integrity compromised
- User privacy violated (seeing other users' data)
- Unpredictable behavior due to code version mismatch