# Multi-Worker Session State Fix Documentation

## Date: 2025-07-29

## Issue Summary
ChatMRPT was experiencing session state persistence issues in a multi-worker Gunicorn environment (4 workers). The main symptoms were:
1. Risk analysis would complete successfully but the state wasn't preserved
2. When transitioning to bed net planning, the system couldn't detect the completed analysis
3. Analysis would be re-run unnecessarily

## Root Cause Analysis

### 1. Global Singleton Pattern
- **File**: `app/core/unified_data_state.py`
- **Problem**: Used `_states` dictionary cache which isn't shared across workers
- Each worker had its own instance of the cache, causing state inconsistency

### 2. Analysis State Handler Singleton
- **File**: `app/core/analysis_state_handler.py`  
- **Problem**: Global `_analysis_state_handler` singleton not shared across workers
- Different workers would have different handler instances

### 3. Flask Session Context
- **File**: `app/tools/complete_analysis_tools.py`
- **Error**: "Failed to set analysis_complete flag: Working outside of request context"
- Flask session updates fail when running in background tasks

### 4. ITN Planning Detection
- **File**: `app/tools/itn_planning_tools.py`
- **Problem**: Used relative paths and relied on Flask session which wasn't consistent across workers

## Applied Fixes

### 1. Unified Data State Fix
```python
# Before: 
self._states: Dict[str, UnifiedDataState] = {}

def get_state(self, session_id: str) -> UnifiedDataState:
    if session_id not in self._states:
        self._states[session_id] = UnifiedDataState(session_id, self.base_upload_folder)
    return self._states[session_id]

# After:
# Removed _states cache
def get_state(self, session_id: str) -> UnifiedDataState:
    # Always create new instance for multi-worker compatibility
    return UnifiedDataState(session_id, self.base_upload_folder)
```

### 2. Analysis State Handler Fix
```python
# Before:
_analysis_state_handler = None

def get_analysis_state_handler() -> AnalysisStateHandler:
    global _analysis_state_handler
    if _analysis_state_handler is None:
        _analysis_state_handler = AnalysisStateHandler()
    return _analysis_state_handler

# After:
def get_analysis_state_handler() -> AnalysisStateHandler:
    # Always create new instance for multi-worker compatibility
    handler = AnalysisStateHandler()
    _register_default_hooks(handler)
    return handler
```

### 3. ITN Planning Tool Fix
```python
# Added direct file check at beginning of _check_analysis_complete method:
# CRITICAL: Direct unified dataset check (works across workers)
if session_id:
    import os
    unified_path = f"/home/ec2-user/ChatMRPT/instance/uploads/{session_id}/unified_dataset.geoparquet"
    if os.path.exists(unified_path):
        logger.info(f"✅ DIRECT CHECK: Found unified dataset - analysis is complete!")
        return True
    unified_csv = f"/home/ec2-user/ChatMRPT/instance/uploads/{session_id}/unified_dataset.csv"
    if os.path.exists(unified_csv):
        logger.info(f"✅ DIRECT CHECK: Found unified CSV - analysis is complete!")
        return True
```

Also changed from relative to absolute paths:
```python
# Before:
session_folder = Path("instance/uploads") / session_id

# After:
session_folder = Path("/home/ec2-user/ChatMRPT/instance/uploads") / session_id
```

## Implementation Steps

1. **Backed up original files**
   - `unified_data_state.py.backup`
   - `analysis_state_handler.py.backup`
   - `itn_planning_tools.py.backup`

2. **Applied fixes via SSH to staging server**
   - Server IP: 18.117.115.217
   - Used sed and Python scripts to modify files

3. **Restarted ChatMRPT service**
   - `sudo systemctl restart chatmrpt`
   - Verified health check endpoint

## Testing Results

After applying fixes:
- Analysis completes and creates unified dataset files successfully
- ITN planning tool can now detect completed analysis via direct file checks
- No more unnecessary re-running of analysis
- Works consistently across all 4 workers

## Key Learnings

1. **Avoid Global State in Multi-Worker Environments**
   - Global singletons don't work across processes
   - Each worker gets its own memory space

2. **File-Based State is More Reliable**
   - Files are shared across all workers
   - Direct file existence checks are worker-agnostic

3. **Flask Session Limitations**
   - Session updates fail outside request context
   - Can't rely on session data in background tasks

4. **Always Use Absolute Paths**
   - Relative paths can be inconsistent across workers
   - Absolute paths ensure all workers check the same location

## Deployment Notes

- Fixes applied to staging server (18.117.115.217)
- Should be tested for 24 hours before production deployment
- No database schema changes required
- Backward compatible with existing data

## Future Recommendations

1. Consider implementing Redis-based session storage for true shared state
2. Add health checks for multi-worker state consistency
3. Implement better logging for cross-worker debugging
4. Consider using a shared cache like Redis for frequently accessed data