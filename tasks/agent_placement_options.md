# Agent Placement Options

## Option 1: Separate Agents (RECOMMENDED ✅)

### Structure
```
app/data_analysis_v3/core/
├── agent.py                          # DataAnalysisAgent (TPR workflow)
├── data_exploration_agent.py         # DataExplorationAgent (conversational)
└── ...

app/web/routes/
└── analysis_routes.py                # Routes to appropriate agent

app/core/
└── request_interpreter.py            # Fallback/legacy orchestrator
```

### Routing
```python
# In analysis_routes.py (line ~831)
if tpr_complete or has_standard_upload:
    agent = DataExplorationAgent(session_id)
else:
    agent = DataAnalysisAgent(session_id)

result = agent.analyze(user_message)
```

### Pros ✅
- Clean separation of concerns
- Easy to test independently
- No circular dependencies
- Clear architecture
- Can deprecate RequestInterpreter later

### Cons ❌
- One more file to maintain
- Routing logic in analysis_routes.py

---

## Option 2: Inside RequestInterpreter

### Structure
```
app/core/
└── request_interpreter.py
    ├── class RequestInterpreter
    │   ├── __init__()
    │   ├── process_message()
    │   ├── _create_data_exploration_agent()  # NEW
    │   └── ... (existing methods)
    └── ...

app/data_analysis_v3/core/
└── agent.py                          # DataAnalysisAgent (TPR workflow only)
```

### Implementation
```python
class RequestInterpreter:
    def process_message(self, user_message, session_id, **kwargs):
        # Determine routing
        session_folder = f"instance/uploads/{session_id}"
        tpr_complete = os.path.exists(f"{session_folder}/.tpr_complete")
        has_standard_upload = (session.get('upload_type') == 'csv_shapefile')

        # Route to agent if applicable
        if tpr_complete or has_standard_upload:
            return self._process_with_exploration_agent(
                user_message,
                session_id
            )
        elif is_tpr_workflow:
            return self._process_with_tpr_agent(user_message, session_id)
        else:
            # Fallback to tool-based processing
            return self._process_with_tools(user_message, session_id)

    def _process_with_exploration_agent(self, user_message, session_id):
        """Use DataExplorationAgent for conversational queries."""
        from app.data_analysis_v3.core.data_exploration_agent import DataExplorationAgent

        agent = DataExplorationAgent(session_id=session_id)
        result = agent.analyze(user_message)

        return {
            'status': 'success',
            'response': result.get('message', ''),
            'visualizations': result.get('visualizations', []),
            'tools_used': ['data_exploration_agent']
        }
```

### Pros ✅
- All routing logic in one place
- RequestInterpreter becomes "master orchestrator"
- Easier to understand flow (everything starts here)

### Cons ❌
- RequestInterpreter becomes even larger (1,600+ → 1,700+ lines)
- Circular dependency risk (agent might call tools from RequestInterpreter)
- Harder to test independently
- Violates single responsibility principle
- Makes RequestInterpreter harder to deprecate later

---

## Option 3: Hybrid (Middle Ground)

### Structure
```
app/core/
├── request_interpreter.py            # Legacy tool-based processing
└── agent_router.py                   # NEW - Smart agent routing

app/data_analysis_v3/core/
├── agent.py                          # TPR workflow agent
└── data_exploration_agent.py         # Conversational agent

app/web/routes/
└── analysis_routes.py                # Routes to AgentRouter
```

### Implementation
```python
# app/core/agent_router.py
class AgentRouter:
    """
    Routes requests to appropriate agent based on session state.
    Clean separation from legacy RequestInterpreter.
    """

    def route(self, user_message, session_id, session_data):
        session_folder = f"instance/uploads/{session_id}"

        # Detect workflow phase
        tpr_complete = os.path.exists(f"{session_folder}/.tpr_complete")
        has_standard_upload = (session_data.get('upload_type') == 'csv_shapefile')

        if tpr_complete or has_standard_upload:
            from app.data_analysis_v3.core.data_exploration_agent import DataExplorationAgent
            agent = DataExplorationAgent(session_id)
        else:
            from app.data_analysis_v3.core.agent import DataAnalysisAgent
            agent = DataAnalysisAgent(session_id)

        return agent.analyze(user_message)
```

### Pros ✅
- Clean routing logic separated from processing
- Easy to test
- Clear architecture
- Can coexist with RequestInterpreter
- Easy migration path

### Cons ❌
- One more file (AgentRouter)
- Need to decide when to use AgentRouter vs RequestInterpreter

---

## Recommendation

**Option 1: Separate Agents** ✅

### Why?

1. **Clean Architecture**
   - Each component has single responsibility
   - DataAnalysisAgent = TPR workflow
   - DataExplorationAgent = Conversational queries
   - analysis_routes.py = Routing

2. **Easy to Test**
   ```python
   # Test exploration agent independently
   agent = DataExplorationAgent('test_session')
   result = agent.analyze("Show top 10 wards")
   assert result['success']
   ```

3. **No Circular Dependencies**
   - Agents don't need RequestInterpreter
   - They use their own tools
   - Clean separation

4. **Future-Proof**
   - Easy to add more agents later
   - Easy to deprecate RequestInterpreter
   - Clear migration path

5. **Follows Existing Pattern**
   - DataAnalysisAgent already separate
   - Just adding one more similar agent
   - Consistent with current architecture

### Implementation
```
app/data_analysis_v3/core/
├── agent.py                      # Existing (TPR workflow)
├── data_exploration_agent.py     # NEW (conversational)
└── ...
```

**File**: `app/data_analysis_v3/core/data_exploration_agent.py`
**Lines**: ~250 (inherits from DataAnalysisAgent, adds data loading)

**Routing**: In `analysis_routes.py` (~20 lines)

**Total new code**: ~270 lines

---

## Summary Table

| Aspect | Option 1 (Separate) | Option 2 (Inside RI) | Option 3 (Hybrid) |
|--------|-------------------|---------------------|-------------------|
| **Complexity** | Low | Medium | Medium |
| **Testability** | ✅ Easy | ❌ Hard | ✅ Easy |
| **Separation of Concerns** | ✅ Clear | ❌ Mixed | ✅ Clear |
| **Code Size** | +270 lines | +100 lines | +350 lines |
| **Circular Dependencies** | ✅ None | ⚠️ Risk | ✅ None |
| **Future Deprecation** | ✅ Easy | ❌ Hard | ✅ Easy |
| **Consistency** | ✅ Matches current | ❌ Different | ⚠️ New pattern |

**Winner: Option 1 - Separate Agents** ✅

---

## Final Recommendation

1. **Create**: `app/data_analysis_v3/core/data_exploration_agent.py`
2. **Inherit**: From `DataAnalysisAgent` (reuse everything)
3. **Override**: `_get_input_data()` to load CSV + shapefile
4. **Route**: In `analysis_routes.py` based on session state
5. **Keep**: RequestInterpreter for legacy/fallback

This is clean, testable, and follows the existing architecture pattern.
