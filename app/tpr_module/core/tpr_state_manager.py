"""
TPR State Manager - Tracks conversation state and user choices.
Maintains context throughout the TPR processing journey.
"""

import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ConversationState:
    """Container for conversation state data."""
    session_id: str
    start_time: datetime
    current_stage: str
    
    # File information
    file_path: Optional[str] = None
    file_metadata: Optional[Dict] = None
    
    # User selections
    selected_state: Optional[str] = None
    selected_facility_level: Optional[str] = None
    selected_age_group: Optional[str] = None
    
    # Processing flags
    alternative_calculation_requested: bool = False
    threshold_violations_found: bool = False
    
    # Results
    tpr_results: Optional[List] = None
    environmental_variables: Optional[Dict] = None
    output_files: Optional[Dict] = None
    
    # Conversation history
    interaction_count: int = 0
    clarification_count: int = 0
    
    # Dynamic attributes
    workflow_stage: Optional[str] = None
    _extra_attrs: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        # Convert datetime to string
        data['start_time'] = self.start_time.isoformat()
        # Include extra attrs if any
        if self._extra_attrs:
            data.update(self._extra_attrs)
        return data


class TPRStateManager:
    """
    Manages conversation state throughout TPR processing.
    Provides context persistence and recovery capabilities.
    """
    
    def __init__(self, session_id: str = None):
        """
        Initialize state manager.
        
        Args:
            session_id: Unique session identifier
        """
        self.session_id = session_id or self._generate_session_id()
        self.state = ConversationState(
            session_id=self.session_id,
            start_time=datetime.now(),
            current_stage='initial'
        )
        self.state_history = []
        
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        import uuid
        return f"tpr_{uuid.uuid4().hex[:8]}"
    
    def update_state(self, key_or_dict: Any, value: Any = None) -> None:
        """
        Update state attribute(s).
        
        Args:
            key_or_dict: State attribute name or dictionary of updates
            value: New value (if key_or_dict is a string)
        """
        # Save current state to history first
        self._save_to_history()
        
        # Handle dictionary update
        if isinstance(key_or_dict, dict):
            for key, val in key_or_dict.items():
                if hasattr(self.state, key):
                    setattr(self.state, key, val)
                    logger.debug(f"State updated: {key} = {val}")
                else:
                    # Store in extra attrs if not a standard attribute
                    if self.state._extra_attrs is None:
                        self.state._extra_attrs = {}
                    self.state._extra_attrs[key] = val
                    logger.debug(f"State updated (extra): {key} = {val}")
            
            # Increment interaction count once for batch update
            self.state.interaction_count += 1
        else:
            # Single key-value update
            if hasattr(self.state, key_or_dict):
                setattr(self.state, key_or_dict, value)
                logger.debug(f"State updated: {key_or_dict} = {value}")
            else:
                # Store in extra attrs if not a standard attribute
                if self.state._extra_attrs is None:
                    self.state._extra_attrs = {}
                self.state._extra_attrs[key_or_dict] = value
                logger.debug(f"State updated (extra): {key_or_dict} = {value}")
                
            # Increment interaction count
            if key_or_dict not in ['interaction_count', 'clarification_count']:
                self.state.interaction_count += 1
    
    def _save_to_history(self) -> None:
        """Save current state to history."""
        state_snapshot = self.state.to_dict()
        self.state_history.append({
            'timestamp': datetime.now().isoformat(),
            'state': state_snapshot
        })
        
        # Keep only last 10 states to prevent memory issues
        if len(self.state_history) > 10:
            self.state_history = self.state_history[-10:]
    
    def get_state(self, key: str = None) -> Any:
        """
        Get state value or entire state.
        
        Args:
            key: Optional specific attribute to retrieve
            
        Returns:
            State value or entire state dict
        """
        if key:
            # First check standard attributes
            if hasattr(self.state, key):
                return getattr(self.state, key)
            # Then check extra attrs
            elif self.state._extra_attrs and key in self.state._extra_attrs:
                return self.state._extra_attrs[key]
            else:
                return None
        return self.state.to_dict()
    
    def get_context_summary(self) -> str:
        """
        Get a natural language summary of current context.
        Useful for maintaining conversation continuity.
        
        Returns:
            Context summary string
        """
        parts = []
        
        if self.state.selected_state:
            parts.append(f"analyzing {self.state.selected_state}")
        
        if self.state.selected_facility_level:
            parts.append(f"using {self.state.selected_facility_level} facilities")
        
        if self.state.selected_age_group:
            age_map = {
                'u5': 'under-5 age group',
                'o5': 'over-5 age group',
                'pw': 'pregnant women'
            }
            parts.append(f"for {age_map.get(self.state.selected_age_group, self.state.selected_age_group)}")
        
        if parts:
            return f"We're {' '.join(parts)}."
        return "We're just getting started with your TPR analysis."
    
    def track_clarification(self) -> None:
        """Track when clarification was needed."""
        self.state.clarification_count += 1
        
        # Log if too many clarifications
        if self.state.clarification_count > 3:
            logger.warning(f"High clarification count ({self.state.clarification_count}) for session {self.session_id}")
    
    def can_proceed(self) -> Tuple[bool, Optional[str]]:
        """
        Check if we have enough information to proceed.
        
        Returns:
            Tuple of (can_proceed, missing_info_message)
        """
        stage = self.state.current_stage
        
        if stage == 'facility_selection' and not self.state.selected_state:
            return False, "I need to know which state to analyze first."
        
        if stage == 'age_group_selection' and not self.state.selected_facility_level:
            return False, "Please select a facility level first."
        
        if stage == 'calculation' and not self.state.selected_age_group:
            return False, "Please select an age group for the analysis."
        
        return True, None
    
    def get_next_step_hint(self) -> str:
        """
        Get a hint about what the next step should be.
        Helps guide users without being restrictive.
        
        Returns:
            Hint message
        """
        stage = self.state.current_stage
        
        hints = {
            'initial': "Upload your NMEP Excel file to begin",
            'state_selection': f"Choose from: {', '.join(self.state.file_metadata.get('states', []))}",
            'facility_selection': "Consider Primary facilities for community-level insights",
            'age_group_selection': "Under-5 is typically used for malaria burden assessment",
            'threshold_check': "You can accept the values or request recalculation",
            'finalization': "Almost done! Preparing your output files..."
        }
        
        return hints.get(stage, "Continue with your analysis")
    
    def reset_to_stage(self, stage: str) -> None:
        """
        Reset state to a specific stage.
        Useful for going back in the conversation.
        
        Args:
            stage: Stage to reset to
        """
        # Clear selections after this stage
        stage_order = [
            'initial', 'state_selection', 'facility_selection', 
            'age_group_selection', 'calculation', 'threshold_check', 
            'finalization'
        ]
        
        if stage in stage_order:
            stage_index = stage_order.index(stage)
            
            # Clear future selections
            if stage_index < stage_order.index('facility_selection'):
                self.state.selected_facility_level = None
                self.state.selected_age_group = None
            
            if stage_index < stage_order.index('age_group_selection'):
                self.state.selected_age_group = None
            
            self.state.current_stage = stage
            logger.info(f"Reset conversation to stage: {stage}")
    
    def export_conversation_log(self) -> Dict[str, Any]:
        """
        Export conversation log for analysis or debugging.
        
        Returns:
            Conversation log dictionary
        """
        return {
            'session_id': self.session_id,
            'start_time': self.state.start_time.isoformat(),
            'duration_minutes': (datetime.now() - self.state.start_time).seconds / 60,
            'current_state': self.state.to_dict(),
            'interaction_count': self.state.interaction_count,
            'clarification_count': self.state.clarification_count,
            'selections': {
                'state': self.state.selected_state,
                'facility_level': self.state.selected_facility_level,
                'age_group': self.state.selected_age_group
            },
            'flags': {
                'alternative_calc': self.state.alternative_calculation_requested,
                'threshold_violations': self.state.threshold_violations_found
            },
            'history_length': len(self.state_history)
        }
    
    def get_progress_percentage(self) -> int:
        """
        Get conversation progress as percentage.
        
        Returns:
            Progress percentage (0-100)
        """
        stages = {
            'initial': 0,
            'state_selection': 20,
            'facility_selection': 40,
            'age_group_selection': 60,
            'calculation': 70,
            'threshold_check': 80,
            'finalization': 90,
            'complete': 100
        }
        
        return stages.get(self.state.current_stage, 0)
    
    def clear_state(self) -> None:
        """Clear all state data and reset to initial state."""
        self.state = ConversationState(
            session_id=self.session_id,
            start_time=datetime.now(),
            current_stage='initial'
        )
        self.state_history = []
        logger.info(f"State cleared for session {self.session_id}")