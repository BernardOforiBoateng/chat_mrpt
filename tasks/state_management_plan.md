# State Management Implementation Plan for Data Analysis V3

## Overview
Add stateful conversation management to fix TPR workflow amnesia while preserving the agent's flexibility for general data analysis.

## Current Agent Behavior
- **Stateless**: New agent instance for each message
- **LangGraph-based**: Uses graph workflow with tool nodes
- **Flexible**: Can handle any data analysis request
- **Problem**: No memory between messages

## Proposed Changes

### 1. Add State Manager (New Component)
- [ ] Create `app/data_analysis_v3/core/state_manager.py`
  - Session-based state storage
  - Cross-worker compatibility (file-based like production)
  - Minimal overhead for non-TPR queries

### 2. Enhance Agent Initialization
- [ ] Modify `DataAnalysisAgent.__init__()` to:
  ```python
  def __init__(self, session_id: str):
      self.session_id = session_id
      self.state_manager = DataAnalysisStateManager(session_id)
      self._restore_state()  # Load previous conversation state
      # ... rest of init
  ```

### 3. State Restoration Logic
- [ ] Add `_restore_state()` method:
  - Restore conversation stage
  - Restore TPR selections (if in TPR workflow)
  - Restore chat history
  - Restore data reference

### 4. Workflow Detection
- [ ] Add intent classification to detect:
  - TPR workflow initiation ("guide me through TPR")
  - TPR continuation (age group, facility level selections)
  - General analysis queries
  - Workflow exits

### 5. State Updates
- [ ] Update state after each interaction:
  - TPR workflow: Track stage progression
  - General analysis: Just maintain chat history
  - Mixed mode: Allow switching between modes

## Impact on Agent Behavior

### Positive Changes
1. **TPR Workflow**: Will remember selections and progress naturally
2. **Context Preservation**: Agent remembers previous queries
3. **Better UX**: No more asking for confirmation of already-stated choices
4. **Flexibility Retained**: Can still handle ad-hoc queries

### Minimal Disruption
1. **Backward Compatible**: Non-TPR queries work exactly the same
2. **Optional State**: State only matters for multi-turn workflows
3. **Graceful Fallback**: If state fails to load, works like current system
4. **Performance**: State check is quick (file existence check)

## Implementation Strategy

### Phase 1: Core State Management
```python
class DataAnalysisStateManager:
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state_file = f"instance/uploads/{session_id}/.agent_state.json"
    
    def save_state(self, state: Dict):
        # Save to file for cross-worker access
        
    def load_state(self) -> Dict:
        # Load from file if exists
        
    def update_workflow_stage(self, stage: str):
        # Update just the workflow stage
```

### Phase 2: Agent Integration
```python
class DataAnalysisAgent:
    def _restore_state(self):
        state = self.state_manager.load_state()
        if state:
            self.current_stage = ConversationStage(state.get('stage', 'INITIAL'))
            self.tpr_selections = state.get('tpr_selections', {})
            self.chat_history = state.get('chat_history', [])
    
    def _save_state(self):
        self.state_manager.save_state({
            'stage': self.current_stage.value,
            'tpr_selections': self.tpr_selections,
            'chat_history': self._serialize_chat_history()
        })
```

### Phase 3: TPR Workflow Logic
```python
def _handle_tpr_workflow(self, user_message: str):
    # Check current stage
    if self.current_stage == ConversationStage.TPR_AGE_GROUP:
        # User is selecting age group
        self.tpr_selections['age_group'] = self._extract_age_group(user_message)
        self.current_stage = ConversationStage.TPR_TEST_METHOD
        self._save_state()
        return "What test method would you like to use?"
    
    elif self.current_stage == ConversationStage.TPR_TEST_METHOD:
        # User is selecting test method
        self.tpr_selections['test_method'] = self._extract_test_method(user_message)
        self.current_stage = ConversationStage.TPR_FACILITY_LEVEL
        self._save_state()
        return "What facility level?"
    # etc...
```

## Testing Plan
1. **TPR Workflow**: Test complete flow without amnesia
2. **General Analysis**: Ensure normal queries still work
3. **Mode Switching**: Test switching between TPR and general analysis
4. **Multi-Worker**: Test state persistence across workers
5. **Error Recovery**: Test graceful handling of corrupted state

## Risk Mitigation
- **State Corruption**: Validate state on load, fallback to stateless
- **Performance**: Use lightweight JSON, lazy loading
- **Concurrency**: File locking for state updates
- **Memory**: Limit chat history size (last 20 messages)

## Success Criteria
- [ ] TPR workflow progresses without re-asking questions
- [ ] General analysis queries work unchanged
- [ ] State persists across page refreshes
- [ ] Works with multi-worker deployment
- [ ] No performance degradation