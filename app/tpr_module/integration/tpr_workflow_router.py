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
            logger.info(f"TPR Router: Processing message '{user_message}' for session {self.session_id}")
            
            # Get TPR state from state manager
            from ..core.tpr_state_manager import TPRStateManager
            state_manager = TPRStateManager(self.session_id)
            tpr_state = state_manager.get_state()
            
            # Merge TPR state with session data for context
            enhanced_session_data = {**session_data}
            enhanced_session_data['tpr_stage'] = tpr_state.get('workflow_stage', 'state_selection')
            enhanced_session_data['available_states'] = tpr_state.get('available_states', [])
            
            logger.info(f"TPR Router: Current stage='{enhanced_session_data['tpr_stage']}', "
                       f"Available states={len(enhanced_session_data.get('available_states', []))}")
            
            # Classify the intent using LLM
            intent = self._classify_intent(user_message, enhanced_session_data)
            logger.info(f"TPR Router: Intent classified as '{intent}' for message '{user_message}'")
            
            if intent == 'tpr_continue':
                # Continue with TPR workflow
                logger.info(f"TPR Router: Routing to TPR handler for continuation")
                return self._handle_tpr_message(user_message)
            
            elif intent == 'general_question':
                # Handle general question with gentle reminder
                logger.warning(f"TPR Router: General question detected, may interrupt workflow")
                return self._handle_general_question(user_message, enhanced_session_data)
            
            elif intent == 'exit_workflow':
                # User wants to leave TPR workflow
                logger.warning(f"TPR Router: User explicitly exiting TPR workflow")
                return self._handle_workflow_exit(enhanced_session_data)
            
            else:
                # Default to TPR workflow with context
                logger.info(f"TPR Router: Unknown intent '{intent}', defaulting to TPR handler")
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
- State selections can be very brief (e.g., just "Adamawa" or "Kwara State")

Examples:
- "Adamawa" -> tpr_continue
- "Adamawa State" -> tpr_continue
- "What is Adamawa?" -> tpr_continue (still selecting state)
- "stop TPR analysis" -> exit_workflow
- "Who are you?" -> general_question

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
        Enhanced to better handle state names and prevent false exits.
        """
        lower_msg = user_message.lower().strip()
        
        # Priority 1: Check state names with variations
        available_states = session_data.get('available_states', [])
        if available_states:
            for state in available_states:
                # Create variations of state name for matching
                state_variations = [
                    state.lower(),
                    state.lower().replace(' state', ''),
                    state.lower().replace('state', '').strip()
                ]
                # Check if message contains state or state contains message (for single words)
                if any(var in lower_msg or lower_msg in var for var in state_variations):
                    logger.info(f"Intent: Detected state name '{state}' in message '{user_message}' - TPR continue")
                    return 'tpr_continue'
        
        # Priority 2: Single/two word inputs are likely state names or selections
        word_count = len(lower_msg.split())
        if word_count <= 2 and '?' not in lower_msg:
            logger.info(f"Intent: Treating '{user_message}' as potential state name (word count: {word_count}) - TPR continue")
            return 'tpr_continue'
        
        # Check for facility levels
        if any(level in lower_msg for level in ['primary', 'secondary', 'tertiary', 'all']):
            logger.info(f"Intent: Detected facility level in '{user_message}' - TPR continue")
            return 'tpr_continue'
        
        # Check for age groups
        if any(age in lower_msg for age in ['under 5', 'over 5', 'pregnant', 'u5', 'o5', 'all ages']):
            logger.info(f"Intent: Detected age group in '{user_message}' - TPR continue")
            return 'tpr_continue'
        
        # Only classify as exit if explicitly requested with TPR mention
        if ('stop' in lower_msg or 'exit' in lower_msg or 'cancel' in lower_msg) and 'tpr' in lower_msg:
            logger.info(f"Intent: Explicit exit request in '{user_message}' - exit workflow")
            return 'exit_workflow'
        
        # General questions need clear indicators (not just any question mark)
        general_indicators = ['what can you', 'who are you', 'help me understand', 'how does']
        if '?' in user_message and any(indicator in lower_msg for indicator in general_indicators):
            logger.info(f"Intent: General question detected in '{user_message}'")
            return 'general_question'
        
        # Default to TPR continuation to prevent accidental exits
        logger.info(f"Intent: Defaulting to TPR continue for '{user_message}'")
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
        session.pop('tpr_session_id', None)
        # CRITICAL: Force session update for multi-worker environment
        session.modified = True
        logger.info(f"TPR workflow exited by user request for session {self.session_id}")
        
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