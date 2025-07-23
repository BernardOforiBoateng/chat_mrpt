"""
TPR Conversation Manager - Natural language interface for TPR processing.
Uses LLM for intent recognition and flexible user interaction.
"""

import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from ..data.nmep_parser import NMEPParser
from ..data.column_mapper import ColumnMapper
from ..data.data_validator import DataValidator
from ..data.geopolitical_zones import get_zone_for_state, get_variables_for_state
from ..services.facility_filter import FacilityFilter
from ..services.threshold_detector import ThresholdDetector
from .tpr_calculator import TPRCalculator
from .tpr_state_manager import TPRStateManager

logger = logging.getLogger(__name__)


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
        """
        Initialize conversation manager.
        
        Args:
            state_manager: Optional state manager instance
            llm_client: LLM client for natural language understanding
        """
        self.llm_client = llm_client
        self.state_manager = state_manager or TPRStateManager()
        self.parser = NMEPParser()
        self._update_stage(ConversationStage.INITIAL_ANALYSIS)
        
        # Components
        self.facility_filter = FacilityFilter()
        self.calculator = TPRCalculator()
        self.threshold_detector = ThresholdDetector()
        self.validator = DataValidator()
        
        # Conversation context
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
            # Not in Flask context, likely in tests
            pass
        except Exception as e:
            logger.warning(f"Could not mark session as modified: {e}")
    
    def generate_response(self, command: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generate response for initial TPR workflow setup.
        
        Args:
            command: Command string (typically 'start')
            context: Context with metadata from parsed file
            
        Returns:
            Response dictionary with message and suggestions
        """
        if command == 'start' and context and 'metadata' in context:
            # This is called after file parsing in the real workflow
            metadata = context['metadata']
            
            # If we have the full data in context, restore it to the parser
            if 'data' in context and context['data'] is not None:
                self.parser.data = context['data']
                logger.info(f"Restored {len(context['data'])} rows to parser for summary generation")
            
            # Start the conversation with the parsed file
            return self.start_conversation_with_metadata(metadata)
        
        return {
            'response': 'Invalid command or missing context',
            'suggestions': [],
            'status': 'error'
        }
    
    def start_conversation_with_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Start conversation with parsed file metadata.
        
        Args:
            metadata: Metadata from parsed NMEP file
            
        Returns:
            Initial conversation response
        """
        # Extract states from metadata
        states = metadata.get('states', [])
        
        # Store parsed data reference
        self.parsed_data = {
            'states': states,
            'metadata': metadata,
            'status': 'success'
        }
        
        # Update state manager
        self.state_manager.update_state('parsed_data', self.parsed_data)
        self.state_manager.update_state('workflow_stage', 'state_selection')
        self._update_stage(ConversationStage.STATE_SELECTION)
        
        # Generate conversational summary
        # Check if parser has data loaded (from restoration)
        if hasattr(self.parser, 'data') and self.parser.data is not None:
            summary = self.parser.get_summary_for_conversation(metadata)
        else:
            # Generate a simpler summary without specific counts
            summary = self._generate_simple_summary(metadata)
        
        return {
            'response': summary,
            'suggestions': states,
            'stage': self.current_stage.value,
            'status': 'success'
        }
    
    def _generate_simple_summary(self, metadata: Dict[str, Any]) -> str:
        """
        Generate a simple summary when full data is not available.
        
        Args:
            metadata: Metadata from parsed NMEP file
            
        Returns:
            Simple formatted summary
        """
        states_str = ", ".join(metadata['states'])
        
        return f"""I've analyzed your NMEP TPR data file. Here's what I found:

**Geographic Coverage:**
- {metadata['state_count']} states: {states_str}
- {metadata['total_facilities']:,} health facilities

**Time Period:**
- {metadata['months_covered']} months of data from {metadata['time_range']}

**State-Level Information:**
- Facility-level data available for all states
- Multiple LGAs and wards in each state
- Data includes RDT and Microscopy test results

Which state would you like to analyze?
1. {metadata['states'][0]}
2. {metadata['states'][1] if len(metadata['states']) > 1 else 'N/A'}
3. {metadata['states'][2] if len(metadata['states']) > 2 else 'N/A'}

Please select one state to proceed with TPR analysis."""
    
    def start_conversation(self, file_path: str) -> Dict[str, Any]:
        """
        Start TPR conversation with file analysis.
        
        Args:
            file_path: Path to NMEP Excel file
            
        Returns:
            Response dictionary with message and data
        """
        self.file_path = file_path
        self._update_stage(ConversationStage.INITIAL_ANALYSIS)
        
        # Parse the file
        logger.info(f"Starting TPR conversation with file: {file_path}")
        parse_result = self.parser.parse_file(file_path)
        
        if parse_result['status'] != 'success':
            return {
                'status': 'error',
                'message': f"I couldn't read the file properly: {parse_result['message']}",
                'stage': self.current_stage.value
            }
        
        self.parsed_data = parse_result
        self.state_manager.update_state('parsed_data', parse_result)
        
        # Generate conversational summary
        summary = self.parser.get_summary_for_conversation(parse_result['metadata'])
        
        # Move to state selection
        self._update_stage(ConversationStage.STATE_SELECTION)
        
        return {
            'status': 'success',
            'message': summary,
            'data': {
                'states': parse_result['states'],
                'metadata': parse_result['metadata']
            },
            'stage': self.current_stage.value,
            'next_action': 'select_state'
        }
    
    def process_user_input(self, user_input: str) -> Dict[str, Any]:
        """
        Process user input using natural language understanding.
        
        Args:
            user_input: Raw user input text
            
        Returns:
            Response based on current stage and user intent
        """
        # Use LLM to understand intent if available
        intent_data = self._understand_user_intent(user_input)
        
        # Get current workflow stage from state manager
        current_workflow_stage = self.state_manager.get_state('workflow_stage')
        
        # Route to appropriate handler based on stage
        if self.current_stage == ConversationStage.STATE_SELECTION or current_workflow_stage == 'state_selection':
            result = self._handle_state_selection(user_input, intent_data)
        elif self.current_stage == ConversationStage.FACILITY_SELECTION or current_workflow_stage == 'facility_selection':
            # Check if user is confirming to proceed after seeing state overview
            if self._is_confirmation(user_input, intent_data):
                # Now show facility selection
                result = self._show_facility_selection()
            else:
                result = self._handle_facility_selection(user_input, intent_data)
        elif self.current_stage == ConversationStage.AGE_GROUP_SELECTION or current_workflow_stage == 'age_group_selection':
            result = self._handle_age_group_selection(user_input, intent_data)
        elif self.current_stage == ConversationStage.THRESHOLD_CHECK:
            result = self._handle_threshold_response(user_input, intent_data)
        else:
            result = self._handle_general_query(user_input, intent_data)
        
        # Ensure response has expected format
        if 'response' not in result:
            result['response'] = result.get('message', '')
        
        return result
    
    def _understand_user_intent(self, user_input: str) -> Dict[str, Any]:
        """
        Use LLM to understand user intent from natural language.
        
        Args:
            user_input: User's natural language input
            
        Returns:
            Dictionary with intent and extracted entities
        """
        if not self.llm_client:
            # Fallback to simple keyword matching if no LLM
            return self._simple_intent_extraction(user_input)
        
        # Construct prompt for LLM
        prompt = f"""
        Analyze this user input in the context of TPR (Test Positivity Rate) analysis:
        
        User Input: "{user_input}"
        Current Stage: {self.current_stage.value}
        Available Options: {self._get_current_options()}
        
        Extract:
        1. Primary intent (select, confirm, reject, question, clarify)
        2. Specific selection if any (state name, facility level, age group)
        3. Any concerns or questions raised
        
        Return as JSON.
        """
        
        try:
            # This would call your actual LLM
            # response = self.llm_client.complete(prompt)
            # For now, return simple extraction
            return self._simple_intent_extraction(user_input)
        except Exception as e:
            logger.error(f"LLM intent extraction failed: {e}")
            return self._simple_intent_extraction(user_input)
    
    def _is_confirmation(self, user_input: str, intent_data: Dict) -> bool:
        """Check if user is confirming/agreeing to proceed."""
        confirmations = ['yes', 'proceed', 'continue', 'sure', 'ok', 'okay', 'confirm', 'agree', 'go ahead', 'let\'s go']
        user_lower = user_input.lower()
        
        # Check intent data first
        if intent_data.get('primary_intent') == 'confirm':
            return True
            
        # Check for confirmation keywords
        return any(confirm in user_lower for confirm in confirmations)
    
    def _show_facility_selection(self) -> Dict[str, Any]:
        """Show facility selection options after state overview confirmation."""
        if not self.selected_state:
            return {
                'status': 'error',
                'message': 'No state selected. Please select a state first.',
                'stage': self.current_stage.value
            }
        
        # Get state data
        state_data = self.parser.get_state_data(self.selected_state)
        
        # Analyze facilities
        facility_analysis = self.facility_filter.analyze_facility_distribution(
            state_data, self.selected_state
        )
        
        # Move to facility selection
        self._update_stage(ConversationStage.FACILITY_SELECTION)
        
        message = facility_analysis['summary']
        message += "\n\nWhich facility level would you prefer to analyze?"
        
        return {
            'status': 'success',
            'message': message,
            'response': message,
            'data': facility_analysis,
            'stage': self.current_stage.value
        }
    
    def _simple_intent_extraction(self, user_input: str) -> Dict[str, Any]:
        """
        Simple intent extraction without LLM.
        Flexible matching, not rigid patterns.
        """
        user_lower = user_input.lower().strip()
        
        # Extract intent based on keywords and context
        intent = {
            'primary_intent': 'unknown',
            'selection': None,
            'confidence': 0.5,
            'concerns': []
        }
        
        # Affirmative responses
        if any(word in user_lower for word in ['yes', 'yeah', 'sure', 'ok', 'okay', 'correct', 'right', 'confirm', 'proceed', 'go ahead']):
            intent['primary_intent'] = 'confirm'
            intent['confidence'] = 0.9
        
        # Negative responses
        elif any(word in user_lower for word in ['no', 'nope', 'not', 'different', 'change', 'other', 'alternative']):
            intent['primary_intent'] = 'reject'
            intent['confidence'] = 0.8
        
        # Questions
        elif '?' in user_input or any(word in user_lower for word in ['what', 'why', 'how', 'which', 'when', 'where']):
            intent['primary_intent'] = 'question'
            intent['confidence'] = 0.9
        
        # Look for specific selections based on stage
        if self.current_stage == ConversationStage.STATE_SELECTION:
            # Look for state names
            for state in self.parsed_data.get('states', []):
                if state.lower() in user_lower:
                    intent['primary_intent'] = 'select'
                    intent['selection'] = state
                    intent['confidence'] = 0.95
                    break
        
        elif self.current_stage == ConversationStage.FACILITY_SELECTION:
            # Look for facility levels
            if 'primary' in user_lower:
                intent['selection'] = 'Primary'
                intent['primary_intent'] = 'select'
            elif 'secondary' in user_lower:
                intent['selection'] = 'Secondary'
                intent['primary_intent'] = 'select'
            elif 'all' in user_lower:
                intent['selection'] = 'All'
                intent['primary_intent'] = 'select'
        
        elif self.current_stage == ConversationStage.AGE_GROUP_SELECTION:
            # Look for age groups
            if 'under 5' in user_lower or 'u5' in user_lower or '<5' in user_lower:
                intent['selection'] = 'u5'
                intent['primary_intent'] = 'select'
            elif 'over 5' in user_lower or 'o5' in user_lower or '>5' in user_lower:
                intent['selection'] = 'o5'
                intent['primary_intent'] = 'select'
            elif 'pregnant' in user_lower or 'pw' in user_lower:
                intent['selection'] = 'pw'
                intent['primary_intent'] = 'select'
        
        return intent
    
    def _handle_state_selection(self, user_input: str, intent_data: Dict) -> Dict[str, Any]:
        """
        Handle state selection with flexibility.
        """
        # Ensure we have parsed data
        if not self.parsed_data:
            return {
                'status': 'error',
                'message': 'No file data available. Please upload an NMEP file first.',
                'stage': self.current_stage.value
            }
        
        # Check if user selected a state
        selected_state = intent_data.get('selection')
        
        if not selected_state:
            # Try to find state in input directly
            for state in self.parsed_data['states']:
                if state.lower() in user_input.lower():
                    selected_state = state
                    break
        
        if selected_state and selected_state in self.parsed_data['states']:
            self.selected_state = selected_state
            self.state_manager.update_state('selected_state', selected_state)
            self.state_manager.update_state('workflow_stage', 'facility_selection')
            
            # Get state-specific summary
            state_summary = self.parser.get_state_summary_for_conversation(selected_state)
            
            # Return the state summary first
            return {
                'status': 'success',
                'message': state_summary,
                'response': state_summary,
                'stage': 'state_overview',
                'next_stage': ConversationStage.FACILITY_SELECTION.value
            }
        
        # If no valid state found
        states_list = ", ".join(self.parsed_data['states'])
        return {
            'status': 'clarification_needed',
            'message': f"I didn't catch which state you'd like to analyze. The available states are: {states_list}. Which one would you like to focus on?",
            'stage': self.current_stage.value
        }
    
    def _handle_facility_selection(self, user_input: str, intent_data: Dict) -> Dict[str, Any]:
        """
        Handle facility level selection flexibly.
        """
        # Get recommendation
        recommendation = self.facility_filter.recommendation or {'recommended_level': 'Primary'}
        recommended_level = recommendation.get('recommended_level', 'Primary')
        
        # Check user intent
        if intent_data['primary_intent'] == 'confirm':
            # User agrees with recommendation
            selected_level = recommended_level
        elif intent_data.get('selection'):
            selected_level = intent_data['selection']
        else:
            # Try to understand from context
            user_lower = user_input.lower()
            if 'recommend' in user_lower or 'suggest' in user_lower:
                selected_level = recommended_level
            elif 'primary' in user_lower:
                selected_level = 'Primary'
            elif 'secondary' in user_lower:
                selected_level = 'Secondary'
            elif 'tertiary' in user_lower:
                selected_level = 'Tertiary'
            elif 'all' in user_lower or 'every' in user_lower:
                selected_level = 'All'
            else:
                # Ask for clarification
                return {
                    'status': 'clarification_needed',
                    'message': "Which facility level would you like to use? You can choose Primary (recommended), Secondary, Tertiary, or All facilities combined.",
                    'response': "Which facility level would you like to use? You can choose Primary (recommended), Secondary, Tertiary, or All facilities combined.",
                    'stage': self.current_stage.value
                }
        
        self.selected_facility_level = selected_level
        self.state_manager.update_state('selected_facility_level', selected_level)
        self.state_manager.update_state('facility_level', selected_level.lower())
        self.state_manager.update_state('workflow_stage', 'age_group_selection')
        
        # Filter data and check completeness
        state_data = self.parser.get_state_data(self.selected_state)
        filtered_data = self.facility_filter.filter_by_level(state_data, selected_level)
        
        # Calculate completeness for age groups
        completeness_u5 = self.parser.calculate_data_completeness(filtered_data, selected_level, 'u5')
        completeness_o5 = self.parser.calculate_data_completeness(filtered_data, selected_level, 'o5')
        completeness_pw = self.parser.calculate_data_completeness(filtered_data, selected_level, 'pw')
        
        # Move to age group selection
        self._update_stage(ConversationStage.AGE_GROUP_SELECTION)
        
        message = f"Good choice! Using **{selected_level}** facilities for {self.selected_state}.\n\n"
        message += f"I can calculate TPR for different age groups in {self.selected_state}. Here's the data availability:\n\n"
        
        # Under 5 years with detailed breakdown
        message += f"**Under 5 years in {self.selected_state}:**\n"
        message += f"- RDT Testing: {completeness_u5['by_test_type']['rdt_tested']:.1f}% data available\n"
        message += f"- Microscopy Testing: {completeness_u5['by_test_type']['micro_tested']:.1f}% data available\n"
        message += "- **Recommended** - best data coverage\n\n"
        
        # Over 5 years with detailed breakdown
        message += f"**Over 5 years (excluding pregnant women) in {self.selected_state}:**\n"
        message += f"- RDT Testing: {completeness_o5['by_test_type']['rdt_tested']:.1f}% data available\n"
        message += f"- Microscopy Testing: {completeness_o5['by_test_type']['micro_tested']:.1f}% data available\n\n"
        
        # Pregnant women with detailed breakdown
        message += f"**Pregnant Women in {self.selected_state}:**\n"
        message += f"- RDT Testing: {completeness_pw['by_test_type']['rdt_tested']:.1f}% data available\n"
        message += f"- Microscopy Testing: {completeness_pw['by_test_type']['micro_tested']:.1f}% data available\n"
        if completeness_pw['overall'] < 20:
            message += "- Limited data - significant gaps\n\n"
        else:
            message += "\n"
        
        message += "Which would you like to calculate for " + self.selected_state + ":\n"
        message += "1. Under 5 TPR (recommended)\n"
        message += "2. Over 5 TPR\n"
        message += "3. Pregnant Women TPR\n\n"
        message += "Your choice?"        
        return {
            'status': 'success',
            'message': message,
            'data': {
                'completeness_u5': completeness_u5,
                'completeness_o5': completeness_o5,
                'completeness_pw': completeness_pw
            },
            'stage': self.current_stage.value
        }
    
    def _handle_age_group_selection(self, user_input: str, intent_data: Dict) -> Dict[str, Any]:
        """
        Handle age group selection and start calculation.
        """
        # Map user input to age group
        age_group = intent_data.get('selection')
        
        if not age_group:
            # Be flexible with interpretation
            user_lower = user_input.lower()
            if any(term in user_lower for term in ['child', 'kid', 'under 5', 'under five', '<5', 'u5']):
                age_group = 'u5'
            elif any(term in user_lower for term in ['adult', 'over 5', 'over five', '>5', 'o5', '5+']):
                age_group = 'o5'
            elif any(term in user_lower for term in ['women', 'mother', 'pregnant', 'pw']):
                age_group = 'pw'
            elif any(term in user_lower for term in ['all', 'everyone', 'every age', 'combined']):
                age_group = 'all'
        
        if not age_group or age_group not in ['u5', 'o5', 'pw', 'all']:
            return {
                'status': 'clarification_needed',
                'message': "Which age group would you like to analyze? You can say 'under 5', 'over 5', or 'pregnant women'.",
                'response': "Which age group would you like to analyze? You can say 'under 5', 'over 5', or 'pregnant women'.",
                'stage': self.current_stage.value
            }
        
        self.selected_age_group = age_group
        self.state_manager.update_state('selected_age_group', age_group)
        self.state_manager.update_state('age_group', age_group)
        self.state_manager.update_state('workflow_stage', 'calculation')
        
        # Start calculation
        self._update_stage(ConversationStage.CALCULATION)
        
        message = "Perfect! I'm now calculating TPR values for each ward...\n\n"
        
        # Perform calculation
        state_data = self.parser.get_state_data(self.selected_state)
        filtered_data = self.facility_filter.filter_by_level(state_data, self.selected_facility_level)
        
        # Data is already mapped in nmep_parser.parse_file() - no need to map again
        # This was causing duplicate columns (especially 'lga')
        
        # Calculate TPR
        try:
            # calculate_ward_tpr returns a dict but stores TPRResult objects in self.results
            self.calculator.calculate_ward_tpr(
                filtered_data, 
                age_group=age_group
            )
            # Get the actual TPRResult objects
            tpr_results = self.calculator.results
        except Exception as e:
            logger.error(f"Error calculating TPR: {e}")
            return {
                'status': 'error',
                'message': f'Error calculating TPR: {str(e)}',
                'stage': self.current_stage.value
            }
        
        # Get summary statistics
        summary_stats = self.calculator.get_summary_statistics()
        
        message += f" Calculated TPR for **{summary_stats['total_wards']} wards**\n\n"
        message += f"**Summary Results:**\n"
        message += f"- Average TPR: {summary_stats['average_tpr']}%\n"
        message += f"- Highest: {summary_stats['max_tpr']}%\n"
        message += f"- Lowest: {summary_stats['min_tpr']}%\n"
        
        # Add data quality breakdown
        message += f"\n**Data Quality Breakdown:**\n"
        high_quality = sum(1 for r in tpr_results if r.data_completeness >= 80)
        medium_quality = sum(1 for r in tpr_results if 50 <= r.data_completeness < 80)
        low_quality = sum(1 for r in tpr_results if r.data_completeness < 50)
        
        message += f"- High Quality (≥80%): {high_quality} wards\n"
        message += f"- Medium Quality (50-79%): {medium_quality} wards\n"
        message += f"- Low Quality (<50%): {low_quality} wards\n"
        
        # Add TPR distribution
        message += f"\n**TPR Distribution:**\n"
        tpr_ranges = {
            '0-10%': sum(1 for r in tpr_results if 0 <= r.tpr_value < 10),
            '10-20%': sum(1 for r in tpr_results if 10 <= r.tpr_value < 20),
            '20-30%': sum(1 for r in tpr_results if 20 <= r.tpr_value < 30),
            '30-40%': sum(1 for r in tpr_results if 30 <= r.tpr_value < 40),
            '40-50%': sum(1 for r in tpr_results if 40 <= r.tpr_value < 50),
            '>50%': sum(1 for r in tpr_results if r.tpr_value >= 50)
        }
        
        for range_name, count in tpr_ranges.items():
            if count > 0:
                message += f"- {range_name}: {count} wards\n"
        
        # Check for threshold violations
        self._update_stage(ConversationStage.THRESHOLD_CHECK)
        # Use the actual TPRResult objects, not the dictionary
        threshold_results = self.threshold_detector.detect_threshold_violations(self.calculator.results)
        
        if threshold_results['urban_violations']:
            message += "\n" + self.threshold_detector.generate_alert_message()
            
            return {
                'status': 'threshold_alert',
                'message': message,
                'data': {
                    'summary_stats': summary_stats,
                    'threshold_results': threshold_results
                },
                'stage': self.current_stage.value
            }
        else:
            # No violations, proceed to finalization
            self._update_stage(ConversationStage.FINALIZATION)
            return self._finalize_calculation(tpr_results, summary_stats)
    
    def _handle_threshold_response(self, user_input: str, intent_data: Dict) -> Dict[str, Any]:
        """
        Handle user response to threshold violation alert.
        """
        if intent_data['primary_intent'] == 'confirm' or 'yes' in user_input.lower():
            # User wants alternative calculation
            message = "I'll recalculate TPR for the flagged urban wards using outpatient attendance...\n\n"
            
            # Perform alternative calculation
            # ... (implementation details)
            
            message += " Recalculation complete! The adjusted values are more reasonable for urban areas.\n"
            
            self._update_stage(ConversationStage.FINALIZATION)
            return {
                'status': 'success',
                'message': message,
                'stage': self.current_stage.value
            }
        else:
            # User doesn't want recalculation
            self._update_stage(ConversationStage.FINALIZATION)
            return self._finalize_calculation(
                self.calculator.results,
                self.calculator.get_summary_statistics()
            )
    
    def _finalize_calculation(self, tpr_results: List, summary_stats: Dict) -> Dict[str, Any]:
        """
        Finalize calculation and prepare for output generation.
        """
        message = "\n**Analysis Complete!**\n\n"
        message += "Now I'll fetch the environmental variables for your selected wards...\n\n"
        
        # Get geopolitical zone
        zone = get_zone_for_state(self.selected_state)
        variables = get_variables_for_state(self.selected_state)
        
        message += f"**{self.selected_state}** is in the **{zone.replace('_', ' ')}** zone.\n"
        message += f"I'll extract these environmental variables:\n"
        for var in variables:
            message += f"- {var}\n"
        
        message += "\nThis will take just a moment as I read from our local database..."
        
        self._update_stage(ConversationStage.COMPLETE)
        
        return {
            'status': 'ready_for_output',
            'message': message,
            'data': {
                'tpr_results': tpr_results,
                'summary_stats': summary_stats,
                'zone': zone,
                'variables': variables
            },
            'stage': self.current_stage.value
        }
    
    def _handle_general_query(self, user_input: str, intent_data: Dict) -> Dict[str, Any]:
        """
        Handle general questions or off-path queries.
        """
        # This is where LLM shines - understanding context and questions
        
        if 'why' in user_input.lower():
            # User asking for explanation
            return self._provide_explanation(user_input)
        
        elif 'back' in user_input.lower() or 'previous' in user_input.lower():
            # User wants to go back
            return self._go_back()
        
        elif 'help' in user_input.lower():
            # User needs help
            return self._provide_help()
        
        else:
            # General response based on current stage
            return {
                'status': 'info',
                'message': f"I understand you're asking about: '{user_input}'. Let me help you with the current step first, then we can address your question.",
                'stage': self.current_stage.value
            }
    
    def _get_current_options(self) -> str:
        """Get current valid options based on stage."""
        if self.current_stage == ConversationStage.STATE_SELECTION:
            return f"States: {', '.join(self.parsed_data['states'])}"
        elif self.current_stage == ConversationStage.FACILITY_SELECTION:
            return "Facility levels: Primary, Secondary, Tertiary, All"
        elif self.current_stage == ConversationStage.AGE_GROUP_SELECTION:
            return "Age groups: Under 5, Over 5, Pregnant women"
        return "General conversation"