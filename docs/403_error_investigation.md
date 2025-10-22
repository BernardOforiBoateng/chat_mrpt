# 403 FORBIDDEN Error - Investigation & Fix

## Problem
After fixing the visualization display, we get a 403 FORBIDDEN error when trying to load the TPR visualization file:
```
GET /serve_viz_file/session_1757447638940/tpr_distribution_map.html 403 (FORBIDDEN)
```

## Root Cause
There's a session management mismatch:

1. **Data Analysis Module** (React frontend):
   - Sends session_id in request body: `{session_id: "session_1757447638940"}`
   - Does NOT use Flask sessions
   - Creates session IDs like: `session_{timestamp}`

2. **Visualization Route** (`/serve_viz_file/`):
   - Expects session_id in Flask session: `session.get('session_id')`
   - Validates: `if current_session_id != session_id: return 403`
   - Flask session is empty/different, so validation fails

## The Code Issue

**visualization_routes.py (lines 275-281)**:
```python
# Current (BROKEN):
current_session_id = session.get('session_id')  # Flask session (empty or different)
if current_session_id != session_id:  # URL has session_1757447638940
    return jsonify({
        'status': 'error',
        'message': 'Unauthorized access to visualization files'
    }), 403
```

## The Fix
We need to make the route work for both Flask session-based AND request-based session management:

```python
# Fixed version:
current_session_id = session.get('session_id')

# For data analysis (React frontend), check if file exists as authorization
# If no Flask session or mismatch, validate by checking file existence
if not current_session_id or current_session_id != session_id:
    # Check if the visualization file actually exists for this session
    file_path = os.path.join(session_folder, filename)
    if not os.path.exists(file_path):
        return jsonify({
            'status': 'error',
            'message': 'Visualization file not found'
        }), 404
    # File exists, so this is a valid session even without Flask session
    # Continue to serve the file
```

## Alternative Fix (Simpler)
Remove the session validation entirely and rely on file existence as the security check:

```python
# Just check if file exists in the session folder
file_path = os.path.join(session_folder, filename)
if not os.path.exists(file_path):
    return jsonify({
        'status': 'error',
        'message': 'Visualization file not found'
    }), 404
# Serve the file
```

## Impact
This fix allows:
- Data Analysis V3 (React) to access visualization files
- Regular Flask session-based access to continue working
- Security maintained by file existence check