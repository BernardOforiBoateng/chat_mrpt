"""
Data Analysis State Manager

Manages conversation state for Data Analysis V3 agent to fix workflow amnesia.
Uses file-based storage for cross-worker compatibility.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import threading
from enum import Enum

logger = logging.getLogger(__name__)


class ConversationStage(Enum):
    """Conversation stages for TPR and general analysis workflows."""
    INITIAL = "initial"
    # TPR workflow stages (3-step process)
    TPR_STATE_SELECTION = "tpr_state_selection"
    TPR_FACILITY_LEVEL = "tpr_facility_level"
    TPR_AGE_GROUP = "tpr_age_group"
    TPR_CALCULATING = "tpr_calculating"
    TPR_COMPLETE = "tpr_complete"
    # General data exploration
    DATA_EXPLORING = "data_exploring"
    COMPLETE = "complete"


class DataAnalysisStateManager:
    """
    Manages persistent state for Data Analysis V3 agent.
    
    Features:
    - File-based storage for multi-worker support
    - Thread-safe operations
    - Automatic state validation
    - Graceful error handling
    """
    
    def __init__(self, session_id: str):
        """
        Initialize state manager for a session.
        
        Args:
            session_id: Unique session identifier
        """
        self.session_id = session_id
        self.state_dir = Path(f"instance/uploads/{session_id}")
        self.state_file = self.state_dir / ".agent_state.json"
        self._lock = threading.Lock()
        
        # Ensure directory exists
        self.state_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"StateManager initialized for session {session_id}")
    
    def save_state(self, state: Dict[str, Any]) -> bool:
        """
        Save state to file with thread safety.
        
        Args:
            state: State dictionary to save
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self._lock:
                # Add metadata
                state['_last_updated'] = datetime.now().isoformat()
                state['_session_id'] = self.session_id
                
                # Write to temporary file first (atomic operation)
                temp_file = self.state_file.with_suffix('.tmp')
                with open(temp_file, 'w') as f:
                    json.dump(state, f, indent=2, default=str)
                
                # Atomic rename
                temp_file.replace(self.state_file)
                
                logger.debug(f"State saved for session {self.session_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False
    
    def load_state(self) -> Dict[str, Any]:
        """
        Load state from file with validation.
        
        Returns:
            State dictionary or empty dict if not found/invalid
        """
        try:
            with self._lock:
                if not self.state_file.exists():
                    return {}
                
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                
                # Validate session ID
                if state.get('_session_id') != self.session_id:
                    logger.warning(f"Session ID mismatch in state file")
                    return {}
                
                return state
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in state file: {e}")
            return {}
        except Exception as e:
            logger.error(f"Failed to load state: {e}")
            return {}
    
    def update_state(self, updates: Dict[str, Any]) -> bool:
        """
        Update specific fields in state.
        
        Args:
            updates: Dictionary of fields to update
            
        Returns:
            True if successful
        """
        try:
            # Load current state
            state = self.load_state()
            
            # Apply updates
            state.update(updates)
            
            # Save back
            return self.save_state(state)
            
        except Exception as e:
            logger.error(f"Failed to update state: {e}")
            return False
    
    def get_field(self, field: str, default: Any = None) -> Any:
        """
        Get a specific field from state.
        
        Args:
            field: Field name to retrieve
            default: Default value if field not found
            
        Returns:
            Field value or default
        """
        state = self.load_state()
        return state.get(field, default)
    
    def get_state(self) -> Dict[str, Any]:
        """
        Get the entire state dictionary.
        
        Returns:
            Complete state dictionary
        """
        return self.load_state()
    
    def update_workflow_stage(self, stage: ConversationStage) -> bool:
        """
        Update the workflow stage.
        
        Args:
            stage: New conversation stage
            
        Returns:
            True if successful
        """
        return self.update_state({
            'current_stage': stage.value,
            'stage_updated_at': datetime.now().isoformat()
        })
    
    def get_workflow_stage(self) -> ConversationStage:
        """
        Get current workflow stage.
        
        Returns:
            Current conversation stage
        """
        stage_value = self.get_field('current_stage', ConversationStage.INITIAL.value)
        try:
            return ConversationStage(stage_value)
        except ValueError:
            logger.warning(f"Invalid stage value: {stage_value}, defaulting to INITIAL")
            return ConversationStage.INITIAL
    
    def save_tpr_selection(self, selection_type: str, value: Any) -> bool:
        """
        Save a TPR workflow selection.
        
        Args:
            selection_type: Type of selection (state, facility_level, age_group)
            value: Selected value
            
        Returns:
            True if successful
        """
        state = self.load_state()
        if 'tpr_selections' not in state:
            state['tpr_selections'] = {}
        
        state['tpr_selections'][selection_type] = value
        state['tpr_selections'][f'{selection_type}_timestamp'] = datetime.now().isoformat()
        
        return self.save_state(state)
    
    def get_tpr_selections(self) -> Dict[str, Any]:
        """
        Get all TPR workflow selections.
        
        Returns:
            Dictionary of TPR selections
        """
        state = self.load_state()
        return state.get('tpr_selections', {})
    
    def mark_tpr_workflow_active(self) -> bool:
        """
        Mark TPR workflow as active.
        
        Returns:
            True if successful
        """
        return self.update_state({
            'tpr_workflow_active': True,
            'tpr_workflow_started_at': datetime.now().isoformat()
        })
    
    def mark_tpr_workflow_complete(self) -> bool:
        """
        Mark TPR workflow as complete.
        
        Returns:
            True if successful
        """
        return self.update_state({
            'tpr_workflow_active': False,
            'tpr_workflow_completed_at': datetime.now().isoformat(),
            'current_stage': ConversationStage.TPR_COMPLETE.value
        })
    
    def is_tpr_workflow_active(self) -> bool:
        """
        Check if TPR workflow is currently active.
        
        Returns:
            True if TPR workflow is active
        """
        return self.get_field('tpr_workflow_active', False)
    
    def clear_state(self) -> bool:
        """
        Clear all state for this session.
        
        Returns:
            True if successful
        """
        try:
            with self._lock:
                if self.state_file.exists():
                    self.state_file.unlink()
                logger.info(f"State cleared for session {self.session_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to clear state: {e}")
            return False
    
    def log_event(self, event_type: str, details: Dict[str, Any]) -> bool:
        """
        Log an event to state history.
        
        Args:
            event_type: Type of event
            details: Event details
            
        Returns:
            True if successful
        """
        state = self.load_state()
        
        if 'event_history' not in state:
            state['event_history'] = []
        
        event = {
            'type': event_type,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        
        state['event_history'].append(event)
        
        # Keep only last 50 events
        if len(state['event_history']) > 50:
            state['event_history'] = state['event_history'][-50:]
        
        return self.save_state(state)