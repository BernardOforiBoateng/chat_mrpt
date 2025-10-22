# TPR Workflow Amnesia Issue Analysis

## Date: 2025-08-13

## Problem Description
After user says "I want you to guide me through TPR calculation" and selects "Under 5 years" for age group, the system asks for confirmation again instead of proceeding to the next step (test method selection).

## Console Log Evidence
```
User: "I want you to guide me through TPR calculation"
System: "Which age group should I focus on for the TPR calculation?"
User: "Under 5 years"
System: "To provide you with the best analysis for the 'Under 5 years' group, could you please confirm if you would like to calculate the Test Positivity Rate (TPR)..."
```

## Root Cause Analysis

### Current System (Data Analysis V3)
- **Stateless Architecture**: Creates new `DataAnalysisAgent` for each message
- **No Workflow State**: Has `ConversationStage` enum defined but doesn't use it
- **No Memory**: Doesn't remember previous selections or stage progression
- **LangGraph Based**: Uses LangGraph which doesn't maintain conversation state

### Production System (Deleted TPR Module)
- **Stateful Architecture**: Used `TPRHandler` with persistent state
- **State Management**: `TPRStateManager` stored workflow state
- **Clear Progression**: Tracked stages (STATE_SELECTION → FACILITY_SELECTION → AGE_GROUP_SELECTION → CALCULATION)
- **State Restoration**: Called `_restore_parsed_data()` at start of each message

## Key Differences

| Aspect | Current (Data Analysis V3) | Production (TPR Module) |
|--------|---------------------------|------------------------|
| State Management | None - new agent each time | TPRStateManager persists state |
| Workflow Tracking | ConversationStage enum unused | Active stage tracking with _update_stage() |
| User Selections | Not stored | Stored in state (selected_state, selected_facility_level, etc.) |
| Data Persistence | Reloads from file each time | Restored from state manager |
| Intent Classification | None | TPRWorkflowRouter with LLM-based intent detection |

## Production Code Components Retrieved

### 1. TPRConversationManager
- Maintained conversation state with `self.current_stage`
- Stored selections in instance variables
- Used `_update_stage()` to track workflow progression
- Forced session updates for multi-worker environment

### 2. TPRHandler
- Centralized handler for TPR workflow
- Restored state at beginning of each request
- Managed progression through stages
- Integrated with Flask session management

### 3. TPRWorkflowRouter
- Intelligent message routing
- LLM-based intent classification
- Prevented accidental workflow exits
- Handled transitions between TPR and main workflow

### 4. TPRStateManager
- Persistent state storage
- Cross-worker compatibility
- Session-based state management

## Solution Approach

To fix the amnesia issue, we need to:

1. **Add State Management**: Implement a state manager for Data Analysis V3 that persists TPR workflow state
2. **Track Workflow Stage**: Actually use the ConversationStage enum to track where we are
3. **Store User Selections**: Keep track of age_group, test_method, facility_level selections
4. **Restore State**: Load previous state at the beginning of each message processing
5. **Smart Routing**: Add intent detection to know when user is continuing TPR vs asking other questions

## Technical Implementation Notes

The current agent initialization:
```python
def __init__(self, session_id: str):
    self.session_id = session_id
    self.current_stage = ConversationStage.INITIAL  # Set but never updated
    self.tpr_selections = {}  # Created but not used effectively
```

Should be enhanced to:
```python
def __init__(self, session_id: str):
    self.session_id = session_id
    self.state_manager = DataAnalysisStateManager(session_id)
    self._restore_state()  # Load previous state
    
def _restore_state(self):
    state = self.state_manager.get_state()
    self.current_stage = state.get('stage', ConversationStage.INITIAL)
    self.tpr_selections = state.get('tpr_selections', {})
    # etc.
```

## Impact
This issue causes poor user experience as the system appears to "forget" the conversation context, requiring users to confirm things they've already stated. This breaks the natural flow of the TPR workflow that was working correctly in production.