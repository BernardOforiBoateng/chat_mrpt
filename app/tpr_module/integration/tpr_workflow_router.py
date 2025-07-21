"""
TPR Workflow Router - Intelligent routing for TPR conversations.

This module handles intelligent routing of messages during TPR workflow,
using NLP to understand user intent rather than hardcoded keywords.
"""

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class TPRWorkflowRouter:
    """
    Routes messages intelligently during TPR workflow.
    Uses NLP to understand when users want to continue TPR vs ask other questions.
    """
    
    def __init__(self, session_id: str, llm_manager=None):
        """
        Initialize the router.
        
        Args:
            session_id: Current session ID
            llm_manager: LLM manager for intent classification
        """
        self.session_id = session_id
        self.llm_manager = llm_manager
    
    def route_message(self, user_message: str, session_data: Dict) -> Dict[str, Any]:
        """
        Route the message based on intent.
        
        Args:
            user_message: User's message
            session_data: Current session data
            
        Returns:
            Response dictionary
        """
        try:
            # Get TPR state from state manager
            from ..core.tpr_state_manager import TPRStateManager
            state_manager = TPRStateManager(self.session_id)
            tpr_state = state_manager.get_state()
            
            # Merge TPR state with session data for context
            enhanced_session_data = {**session_data}
            enhanced_session_data['tpr_stage'] = tpr_state.get('workflow_stage', 'state_selection')
            enhanced_session_data['available_states'] = tpr_state.get('available_states', [])
            
            # Classify the intent using LLM
            intent = self._classify_intent(user_message, enhanced_session_data)
            
            if intent == 'tpr_continue':
                # Continue with TPR workflow
                return self._handle_tpr_message(user_message)
            
            elif intent == 'general_question':
                # Handle general question with gentle reminder
                return self._handle_general_question(user_message, enhanced_session_data)
            
            elif intent == 'exit_workflow':
                # User wants to leave TPR workflow
                return self._handle_workflow_exit(enhanced_session_data)
            
            else:
                # Default to TPR workflow with context
                return self._handle_tpr_message(user_message)
                
        except Exception as e:
            logger.error(f"Error in workflow routing: {str(e)}")
            return self._handle_tpr_message(user_message)
    
    def _classify_intent(self, user_message: str, session_data: Dict) -> str:
        """
        Use LLM to classify user intent.
        
        Returns one of: 'tpr_continue', 'general_question', 'exit_workflow'
        """
        if not self.llm_manager:
            # Fallback to simple heuristics if no LLM
            return self._simple_intent_classification(user_message, session_data)
        
        try:
            # Get current TPR stage for context
            stage = session_data.get('tpr_stage', 'unknown')
            
            prompt = f"""You are analyzing a user message during a Test Positivity Rate (TPR) analysis workflow.
The user has uploaded NMEP data and we are currently at stage: {stage}

User message: "{user_message}"

Classify the user's intent as one of:
1. "tpr_continue" - User is responding to the TPR workflow (selecting state, facility level, etc.)
2. "general_question" - User is asking a general question about the system or malaria analysis
3. "exit_workflow" - User wants to stop the TPR analysis and do something else

Consider:
- Questions about identity, capabilities, or help are general questions
- Selections of states, facilities, or age groups are TPR continuations
- Expressions of confusion or requests to stop indicate potential exit

Return only the intent classification, nothing else."""

            response = self.llm_manager.generate_response(prompt)
            intent = response.strip().lower()
            
            if intent in ['tpr_continue', 'general_question', 'exit_workflow']:
                return intent
            else:
                # Default to TPR if unclear
                return 'tpr_continue'
                
        except Exception as e:
            logger.error(f"LLM intent classification failed: {e}")
            return self._simple_intent_classification(user_message, session_data)
    
    def _simple_intent_classification(self, user_message: str, session_data: Dict) -> str:
        """
        Simple fallback intent classification without LLM.
        """
        lower_msg = user_message.lower().strip()
        
        # Check for state names from available states (TPR continuation)
        available_states = session_data.get('available_states', [])
        if available_states and any(state.lower() in lower_msg for state in available_states):
            return 'tpr_continue'
        
        # Check for facility levels
        if any(level in lower_msg for level in ['primary', 'secondary', 'tertiary', 'all']):
            return 'tpr_continue'
        
        # Check for age groups
        if any(age in lower_msg for age in ['under 5', 'over 5', 'pregnant', 'u5', 'o5']):
            return 'tpr_continue'
        
        # General questions often have question marks
        if '?' in user_message and len(user_message) > 10:
            return 'general_question'
        
        # Default to TPR continuation
        return 'tpr_continue'
    
    def _handle_tpr_message(self, user_message: str) -> Dict[str, Any]:
        """
        Handle TPR-specific message.
        """
        try:
            from app.tpr_module.integration.tpr_handler import get_tpr_handler
            tpr_handler = get_tpr_handler(self.session_id)
            result = tpr_handler.process_tpr_message(user_message)
            
            # Convert TPR response format to standard format
            return {
                'status': result.get('status', 'success'),
                'response': result.get('response', ''),
                'tools_used': ['tpr_workflow'],
                'visualizations': result.get('visualizations', []),
                'download_links': result.get('download_links', {}),
                'workflow': 'tpr',
                'stage': result.get('stage')
            }
        except Exception as e:
            logger.error(f"Error processing TPR message: {e}")
            raise
    
    def _handle_general_question(self, user_message: str, session_data: Dict) -> Dict[str, Any]:
        """
        Handle general question with gentle TPR reminder.
        """
        # Get current TPR context
        stage = session_data.get('tpr_stage', 'state_selection')
        states = session_data.get('available_states', [])
        
        # Create a gentle reminder based on context
        reminder = self._create_gentle_reminder(stage, states)
        
        # For now, redirect back to TPR with reminder
        return {
            'status': 'success',
            'response': f"I understand you have a question. {reminder}",
            'tools_used': ['tpr_workflow_reminder'],
            'workflow': 'tpr',
            'stage': stage
        }
    
    def _handle_workflow_exit(self, session_data: Dict) -> Dict[str, Any]:
        """
        Handle workflow exit request.
        """
        from flask import session
        session['tpr_workflow_active'] = False
        
        return {
            'status': 'success',
            'response': (
                "I've paused the TPR analysis. Your uploaded data is still available. "
                "How can I help you with malaria risk analysis? "
                "You can ask me to resume TPR analysis at any time."
            ),
            'tools_used': ['exit_tpr_workflow'],
            'visualizations': []
        }
    
    def _create_gentle_reminder(self, stage: str, states: list) -> str:
        """
        Create a gentle reminder about TPR workflow.
        """
        if stage == 'state_selection' and states:
            states_str = ", ".join(states) if states else "the available states"
            return f"We're currently selecting a state for TPR analysis. The available states are: {states_str}. Which would you like to analyze?"
        
        elif stage == 'facility_selection':
            return "We're currently selecting the facility level for TPR analysis. Would you like to analyze Primary, Secondary, or All facilities?"
        
        elif stage == 'age_selection':
            return "We're currently selecting the age group for TPR analysis. Would you like to analyze Under 5, Over 5, Pregnant Women, or All ages?"
        
        else:
            return "We're currently working through the TPR analysis. Would you like to continue with the analysis?"