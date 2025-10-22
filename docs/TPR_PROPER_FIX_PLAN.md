# TPR Workflow - Proper Fix Plan

## Problem Analysis

### Root Cause
The TPR module uses an **in-memory handler cache** that doesn't work in multi-worker environments:

```python
# In tpr_handler.py
_tpr_handlers = {}  # This is per-worker memory!

def get_tpr_handler(session_id: str) -> TPRHandler:
    if session_id not in _tpr_handlers:
        _tpr_handlers[session_id] = TPRHandler(session_id)
    return _tpr_handlers[session_id]
```

### Why It Fails
1. Worker A processes file upload → Creates handler in its memory
2. Worker B processes next message → No handler in its memory → Creates new handler
3. New handler has no state → Falls to generic response

### Current Infrastructure
- ✅ Redis is installed and working
- ✅ Flask sessions are using Redis
- ❌ TPR state is NOT saved to Flask session
- ❌ TPR relies on in-memory cache

## Proper Solution Design

### Option 1: Full Session Integration (Recommended)
**Approach**: Save TPR state to Flask session after every operation

**Pros**:
- Works with any number of workers
- Survives server restarts
- Integrates with existing session management

**Cons**:
- Requires careful state serialization
- Need to handle large data (parsed Excel data)

### Option 2: Redis-Based Handler Cache
**Approach**: Replace in-memory cache with Redis cache

**Pros**:
- Minimal changes to existing code
- Direct replacement of current approach

**Cons**:
- Another Redis dependency
- Need to serialize entire handler

### Option 3: Stateless Design
**Approach**: Make TPR handler completely stateless

**Pros**:
- Most scalable approach
- No session storage needed

**Cons**:
- Major refactoring required
- Would need to reload data from files each request

## Recommended Implementation Plan

### Phase 1: Session State Storage
1. Modify `TPRStateManager` to serialize its state to a simple dict
2. Save this dict to Flask session after each update
3. Load state from session when handler is created

### Phase 2: Data Storage Strategy
1. Save parsed Excel data to a temporary file (not session - too large)
2. Store only the file path in session
3. Reload data from file when needed

### Phase 3: Handler Lifecycle
1. Remove the in-memory handler cache completely
2. Create fresh handler for each request
3. Handler loads state from session on init
4. Handler saves state to session after each operation

## Implementation Steps

### Step 1: Create Serializable State
```python
# In TPRStateManager
def to_session_dict(self):
    """Convert state to session-safe dictionary"""
    return {
        'session_id': self.session_id,
        'current_stage': self.state.current_stage,
        'selected_state': self.state.selected_state,
        'selected_facility_level': self.state.selected_facility_level,
        'selected_age_group': self.state.selected_age_group,
        'workflow_stage': self.state.workflow_stage,
        'parsed_data_file': self.state.parsed_data_file,  # Path to temp file
        'metadata': self.state.file_metadata,
        # ... other serializable fields
    }

def from_session_dict(self, session_data):
    """Restore state from session dictionary"""
    # Restore all fields
```

### Step 2: Session Integration
```python
# In TPRHandler.__init__
def __init__(self, session_id):
    # ... existing init ...
    
    # Load state from session
    if 'tpr_state' in session:
        self.state_manager.from_session_dict(session['tpr_state'])
        
    # Load parsed data if available
    if self.state_manager.state.parsed_data_file:
        self.nmep_parser.load_from_file(self.state_manager.state.parsed_data_file)

# After any state change
def _save_state_to_session(self):
    session['tpr_state'] = self.state_manager.to_session_dict()
    session.modified = True
```

### Step 3: Remove Handler Cache
```python
# Replace get_tpr_handler function
def get_tpr_handler(session_id: str) -> TPRHandler:
    """Create TPR handler for a session (no caching)"""
    return TPRHandler(session_id)
```

## Testing Plan
1. Test file upload
2. Test state selection across workers
3. Test full workflow completion
4. Test browser refresh mid-workflow
5. Test concurrent users

## Rollback Plan
All original files are backed up and can be restored if needed.

## Success Criteria
- TPR workflow works reliably at every stage
- No "I understand you're asking about..." messages
- State persists across workers and page refreshes
- Multiple concurrent users can use TPR