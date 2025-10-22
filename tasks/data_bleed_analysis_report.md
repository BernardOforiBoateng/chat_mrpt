# ChatMRPT Data Bleed Root Cause Analysis Report

## Executive Summary

The ChatMRPT application is experiencing critical data bleeding across users in the production environment. Multiple users are seeing each other's data when processing requests simultaneously. This report identifies the root causes of this issue.

## Critical Findings

### 1. Global Singleton Pattern in Multi-Worker Environment

**Problem**: The application uses global singleton patterns for state management that persist across requests and workers.

**Affected Files**:
- `/app/core/unified_data_state.py` (lines 302-309):
  ```python
  # Global instance
  _data_state_manager = None

  def get_data_state_manager() -> UnifiedDataStateManager:
      """Get the global data state manager instance."""
      global _data_state_manager
      if _data_state_manager is None:
          _data_state_manager = UnifiedDataStateManager()
      return _data_state_manager
  ```

- `/app/core/analysis_state_handler.py` (lines 147-158): Similar global singleton pattern
- `/app/core/redis_state_manager.py` (lines 333-340): Another global singleton

**Impact**: When Worker 1 processes User A's request, it stores data in the global singleton. When the same worker processes User B's request, it retrieves User A's data from the same singleton.

### 2. In-Memory State Storage in UnifiedDataStateManager

**Problem**: The `UnifiedDataStateManager` stores session states in an in-memory dictionary.

**Evidence** (`/app/core/unified_data_state.py`, lines 276-289):
```python
class UnifiedDataStateManager:
    def __init__(self, base_upload_folder: str = "instance/uploads"):
        self.base_upload_folder = base_upload_folder
        self._states: Dict[str, UnifiedDataState] = {}  # <-- In-memory storage

    def get_state(self, session_id: str) -> UnifiedDataState:
        """Get or create data state for session."""
        if session_id not in self._states:
            self._states[session_id] = UnifiedDataState(...)
        return self._states[session_id]
```

**Impact**: All sessions processed by a worker share the same `_states` dictionary. If Worker 1 handles both User A and User B, their data is stored in the same dictionary instance.

### 3. Service Container Singleton Registration

**Problem**: Services are registered as singletons by default in the service container.

**Evidence** (`/app/services/container.py`, lines 53-59):
```python
def register(self, name: str, factory: callable, singleton: bool = True) -> None:
    """Register a service factory."""
    self._factories[name] = factory

    if singleton:  # Default is True
        self._singletons[name] = None
```

**Impact**: Services like `data_service`, `analysis_service` maintain state across different user requests.

### 4. Request Interpreter Session Data Storage

**Problem**: The RequestInterpreter stores conversation history and session data at the instance level.

**Evidence** (`/app/core/request_interpreter.py`, lines 60-62):
```python
# py-sidebot approach: Simple conversation storage
self.conversation_history = {}  # Shared across all requests
self.session_data = {}  # Shared across all requests
```

**Impact**: Conversation history from one user can leak to another user when served by the same worker.

### 5. Redis Fallback Issues

**Problem**: When Redis is unavailable, the system falls back to in-memory storage.

**Evidence** (`/app/core/redis_state_manager.py`, lines 94-97):
```python
except Exception as e:
    logger.error(f"❌ Redis connection failed: {e}")
    # Fallback to in-memory storage (not ideal but prevents crashes)
    self.redis_client = None
    self._fallback_storage = {}  # <-- In-memory fallback
```

**Impact**: When Redis fails, all session state is stored in worker memory, causing immediate data bleeding.

### 6. No Session Validation in Data Access

**Problem**: There's no validation that the data being accessed belongs to the requesting session.

**Evidence**: Throughout the codebase, data is retrieved using session_id without verifying it matches the current request's session:
```python
def get_state(self, session_id: str) -> UnifiedDataState:
    if session_id not in self._states:
        self._states[session_id] = UnifiedDataState(...)
    return self._states[session_id]  # No validation
```

**Impact**: If a session_id is incorrectly passed or cached, users can access other users' data.

## How Data Bleeding Occurs

### Scenario 1: Same Worker Processing
1. User A uploads data → Worker 1 → Stores in global `_data_state_manager._states['session_A']`
2. User B makes request → Worker 1 → Due to bug/cache, accesses `_states['session_A']` instead of `_states['session_B']`
3. User B sees User A's data

### Scenario 2: Service Singleton Contamination
1. User A's request → `analysis_service` singleton processes and stores results
2. User B's request → Same `analysis_service` singleton returns cached User A results

### Scenario 3: Redis Fallback
1. Redis connection fails
2. System falls back to in-memory `_fallback_storage`
3. Multiple users' data stored in same worker memory
4. Cross-contamination occurs

## Evidence of Previous Fix Attempts

Found in `/scripts/utilities/simple_risk_fix.sh`:
- Comments indicate awareness of multi-worker issues
- Attempted to remove singleton patterns
- Incomplete implementation - only addressed 2 of 6+ singleton patterns

## Current Architecture Issues

### Multi-Worker Deployment
- Running with multiple Gunicorn workers (likely 6 based on CLAUDE.md)
- Each worker is a separate process
- Workers share nothing by design EXCEPT when using global singletons

### Session Management
- Flask sessions stored in Redis (when available) or filesystem
- Session contains `session_id`
- Data files stored correctly in `instance/uploads/{session_id}/`
- BUT: In-memory state managers don't respect these boundaries

### Data Flow
1. User request → Load Balancer → One of 6 workers
2. Worker creates/retrieves global singleton
3. Singleton stores data in memory
4. Next request to same worker sees previous data

## Summary of Root Causes

1. **Global Singleton Anti-Pattern**: Using global singletons in a multi-worker environment
2. **In-Memory State Storage**: Storing session state in worker memory instead of external store
3. **Service Persistence**: Services maintaining state across requests
4. **Missing Session Validation**: No verification that data belongs to requesting user
5. **Inadequate Isolation**: No process or memory isolation between user sessions
6. **Redis Fallback to Memory**: Falling back to in-memory storage when Redis fails

## Severity Assessment

**CRITICAL** - This allows users to see each other's sensitive health data, including:
- Personal demographic information
- Health indicators and risk scores
- Geographic location data
- Analysis results and recommendations

---

**Report Date**: 2025-09-25
**Finding Type**: Security - Data Isolation Failure
**Affected Component**: Session Management & State Storage
**Environment**: AWS Production (Multiple EC2 instances with Gunicorn workers)