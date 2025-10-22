# Retrieved TPR Production Code

## Overview
This file contains the deleted production TPR module code that handled the TPR workflow correctly without amnesia issues.

## Key Files Retrieved

### 1. TPRConversationManager (app/tpr_module/core/tpr_conversation_manager.py)

```python
"""
TPR Conversation Manager - Natural language interface for TPR processing.
Uses LLM for intent recognition and flexible user interaction.
"""

class ConversationStage(Enum):
    """Conversation stages - flexible flow, not rigid steps."""
    INITIAL_ANALYSIS = "initial_analysis"
    STATE_SELECTION = "state_selection"
    FACILITY_SELECTION = "facility_selection"
    AGE_GROUP_SELECTION = "age_group_selection"
    CALCULATION = "calculation"
    THRESHOLD_CHECK = "threshold_check"
    ALTERNATIVE_CALC = "alternative_calc"
    FINALIZATION = "finalization"
    COMPLETE = "complete"


class TPRConversationManager:
    """
    Manages conversational flow for TPR processing.
    Uses natural language understanding rather than rigid patterns.
    """
    
    def __init__(self, state_manager=None, llm_client=None):
        self.llm_client = llm_client
        self.state_manager = state_manager or TPRStateManager()
        self.parser = NMEPParser()
        self._update_stage(ConversationStage.INITIAL_ANALYSIS)
        
        # Components
        self.facility_filter = FacilityFilter()
        self.calculator = TPRCalculator()
        self.threshold_detector = ThresholdDetector()
        self.validator = DataValidator()
        
        # Conversation context - STORES USER SELECTIONS
        self.file_path = None
        self.parsed_data = None
        self.selected_state = None
        self.selected_facility_level = None
        self.selected_age_group = None
    
    def _update_stage(self, new_stage: ConversationStage) -> None:
        """Update conversation stage and force session update for multi-worker environment."""
        self.current_stage = new_stage
        
        # Force session update in multi-worker environment
        try:
            from flask import session
            session.modified = True
            logger.debug(f"Updated stage to {new_stage.value} and marked session as modified")
        except ImportError:
            pass
```

### 2. TPRHandler (app/tpr_module/integration/tpr_handler.py)

```python
class TPRHandler:
    """Main handler for TPR workflow integration."""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.state_manager = TPRStateManager(session_id)
        
        # Initialize with LLM if available
        llm_client = self._get_llm_client()
        self.conversation_manager = TPRConversationManager(
            self.state_manager,
            llm_client=llm_client
        )
        
        # Initialize services
        self.nmep_parser = NMEPParser()
        self.state_selector = StateSelector()
        self.output_generator = OutputGenerator(session_id)
        
        # CRITICAL: Restore parsed data if available
        self._restore_parsed_data()
        
    def _restore_parsed_data(self):
        """Restore parsed data from state manager."""
        try:
            state = self.state_manager.get_state()
            if state.get('nmep_data') is not None:
                # Restore data to parser
                self.nmep_parser.data = state['nmep_data']
                
                # CRITICAL: Also restore data to conversation manager's parser!
                self.conversation_manager.parser.data = state['nmep_data']
                
                # Restore to conversation manager
                self.conversation_manager.parsed_data = state.get('parsed_data')
                self.conversation_manager.selected_state = state.get('selected_state')
                self.conversation_manager.selected_facility_level = state.get('selected_facility_level')
                
                # Set the conversation stage based on workflow stage
                stage_map = {
                    'state_selection': ConversationStage.STATE_SELECTION,
                    'facility_selection': ConversationStage.FACILITY_SELECTION,
                    'age_selection': ConversationStage.AGE_GROUP_SELECTION,
                    'calculation': ConversationStage.CALCULATION
                }
                workflow_stage = state.get('workflow_stage', 'state_selection')
                if workflow_stage in stage_map:
                    self.conversation_manager.current_stage = stage_map[workflow_stage]
                
        except Exception as e:
            logger.error(f"Error restoring parsed data: {e}")
    
    def process_tpr_message(self, user_message: str) -> Dict[str, Any]:
        """
        Process a user message in the TPR workflow.
        
        Args:
            user_message: User's message
            
        Returns:
            Response with next steps
        """
        try:
            # CRITICAL: Restore parsed data before processing message
            # This ensures data is available across requests
            self._restore_parsed_data()
            
            # Get current state
            current_state = self.state_manager.get_state()
            
            # Process based on workflow stage...
```

### 3. TPRWorkflowRouter (app/tpr_module/integration/tpr_workflow_router.py)

```python
class TPRWorkflowRouter:
    """
    Routes messages intelligently during TPR workflow.
    Uses NLP to understand when users want to continue TPR vs ask other questions.
    """
    
    def _classify_intent(self, user_message: str, session_data: Dict) -> str:
        """
        Use LLM to classify user intent.
        
        Returns one of: 'tpr_continue', 'general_question', 'exit_workflow'
        """
        if not self.llm_manager:
            return self._simple_intent_classification(user_message, session_data)
        
        try:
            stage = session_data.get('tpr_stage', 'unknown')
            
            prompt = f"""You are analyzing a user message during a Test Positivity Rate (TPR) analysis workflow.
The user has uploaded NMEP data and we are currently at stage: {stage}
Available states for selection: {session_data.get('available_states', [])}

User message: "{user_message}"

Classify the user's intent as one of:
1. "tpr_continue" - User is responding to the TPR workflow (selecting state, facility level, etc.)
2. "general_question" - User is asking a general question about the system or malaria analysis
3. "exit_workflow" - User wants to stop the TPR analysis and do something else

IMPORTANT RULES:
- Any mention of a state name (even partial) should ALWAYS be classified as "tpr_continue"
- Single words that could be state names should be "tpr_continue"
- Two-word responses without question marks should be "tpr_continue"
- Only classify as "exit_workflow" if user explicitly says "stop TPR" or "exit TPR"
- When in doubt, default to "tpr_continue" to avoid disrupting the workflow
"""
            response = self.llm_manager.generate_response(prompt)
            intent = response.strip().lower()
            
            if intent in ['tpr_continue', 'general_question', 'exit_workflow']:
                return intent
            else:
                return 'tpr_continue'  # Default to TPR
                
        except Exception as e:
            logger.error(f"LLM intent classification failed: {e}")
            return self._simple_intent_classification(user_message, session_data)
```

### 4. TPRPipeline (app/tpr_module/core/tpr_pipeline.py)

```python
class TPRPipeline:
    """Coordinate the complete TPR analysis pipeline."""
    
    def __init__(self, nmep_parser=None, state_selector=None, output_generator=None):
        # Core components
        self.column_mapper = ColumnMapper()
        self.validator = DataValidator()
        self.calculator = TPRCalculator()
        self.facility_filter = FacilityFilter()
        self.threshold_detector = ThresholdDetector()
        self.raster_extractor = RasterExtractor()
        
        # Injected components
        self.nmep_parser = nmep_parser
        self.state_selector = state_selector
        self.output_generator = output_generator
    
    def run(self, nmep_data, state_name, state_boundaries, 
            facility_level='all', age_group='all_ages', metadata=None):
        """
        Run the complete TPR analysis pipeline.
        """
        # Step 1: Map columns to standard names
        mapped_data = self.column_mapper.map_nmep_columns(nmep_data)
        
        # Step 2: Filter for selected state
        state_data = self._filter_state_data(mapped_data, state_name)
        
        # Step 3: Apply facility level filter
        if facility_level != 'all':
            filtered_data = self.facility_filter.filter_by_level(state_data, facility_level)
        
        # Step 4: Calculate TPR with selected age group
        tpr_results = self.calculator.calculate_tpr(filtered_data, age_group)
        
        # Continue with analysis...
```

## Key Features of Production System

1. **Stateful Conversation Management**
   - Maintained conversation stage throughout workflow
   - Stored user selections (state, facility level, age group)
   - Restored state at beginning of each message

2. **Clear Workflow Progression**
   - STATE_SELECTION → FACILITY_SELECTION → AGE_GROUP_SELECTION → CALCULATION
   - Each stage knew what question to ask next
   - No re-asking for confirmation

3. **Intent Classification**
   - Used LLM to understand if user was continuing TPR or asking other questions
   - Prevented accidental workflow exits
   - Smart routing based on context

4. **Multi-Worker Support**
   - Forced session updates with `session.modified = True`
   - State persistence across worker processes
   - File-based state checking for cross-worker compatibility

## How Production Handled the Exact Scenario

When user said "Under 5 years" after being asked about age group:
1. System classified intent as 'tpr_continue'
2. Stored 'under_5' in `selected_age_group`
3. Updated stage to FACILITY_SELECTION
4. Asked next question: "What facility level would you like to analyze?"
5. NO re-confirmation needed!

## Recommendation

To fix the current amnesia issue, we need to:
1. Implement a DataAnalysisStateManager similar to TPRStateManager
2. Restore state at the beginning of each message processing
3. Track workflow progression through stages
4. Store user selections persistently
5. Add intent classification to understand context