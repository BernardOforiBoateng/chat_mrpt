"""
Arena Integration Patch for Request Interpreter

This module provides the integration logic to seamlessly incorporate
Arena multi-model interpretations into the existing request interpreter flow.
Apply this patch to enable automatic Arena triggering based on conversation context.
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ArenaIntegrationMixin:
    """
    Mixin class that adds Arena interpretation capabilities to RequestInterpreter.

    Usage:
        class EnhancedRequestInterpreter(ArenaIntegrationMixin, RequestInterpreter):
            pass
    """

    def __init__(self, *args, **kwargs):
        """Initialize Arena integration components."""
        super().__init__(*args, **kwargs)

        # Initialize Arena components
        self._init_arena_system()

        # Track Arena state per session
        self.arena_states = {}

    def _init_arena_system(self):
        """Initialize Arena interpretation system."""
        try:
            # Prefer enhanced arena manager if available, otherwise fall back
            try:
                from .enhanced_arena_manager import EnhancedArenaManager  # type: ignore
            except Exception:
                EnhancedArenaManager = None  # Fallback handled below
            from .arena_trigger_detector import ConversationalArenaTrigger

            # Initialize enhanced Arena manager
            arena_config = {
                'phi3:mini': {'type': 'ollama', 'display_name': 'The Analyst'},
                'mistral:7b': {'type': 'ollama', 'display_name': 'The Statistician'},
                'qwen2.5:7b': {'type': 'ollama', 'display_name': 'The Technician'}
            }

            if EnhancedArenaManager is not None:
                self.arena_manager = EnhancedArenaManager(arena_config)
            else:
                # Fallback to standard ArenaManager if enhanced is not available
                from .arena_manager import ArenaManager
                self.arena_manager = ArenaManager()
            self.arena_enabled = True
            logger.info("Arena interpretation system initialized successfully")

        except Exception as e:
            logger.warning(f"Arena system not available: {e}")
            self.arena_enabled = False

    def process_message_with_arena(self, user_message: str, session_id: str,
                                  session_data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Enhanced process_message that includes Arena interpretation triggers.

        Args:
            user_message: User's message
            session_id: Session identifier
            session_data: Session data dictionary
            **kwargs: Additional parameters

        Returns:
            Response dictionary with potential Arena insights
        """
        # Get base response from original process_message
        result = self.process_message(user_message, session_id, session_data, **kwargs)

        # Check if Arena should be triggered
        if self.arena_enabled:
            arena_result = self._check_and_trigger_arena(
                user_message, session_id, session_data, result
            )

            if arena_result:
                # Integrate Arena insights into response
                result = self._integrate_arena_insights(result, arena_result)

        return result

    def _check_and_trigger_arena(self, user_message: str, session_id: str,
                                session_data: Dict[str, Any],
                                current_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Check if Arena should be triggered and execute if needed.

        Args:
            user_message: User's message
            session_id: Session identifier
            session_data: Session data
            current_result: Current response from base interpreter

        Returns:
            Arena results if triggered, None otherwise
        """
        try:
            # Get or create trigger detector for session
            if session_id not in self.arena_states:
                from .arena_trigger_detector import ConversationalArenaTrigger
                self.arena_states[session_id] = {
                    'trigger_detector': ConversationalArenaTrigger(session_id),
                    'last_arena_time': None,
                    'arena_count': 0
                }

            trigger_detector = self.arena_states[session_id]['trigger_detector']

            # Prepare context for trigger detection
            context = self._prepare_arena_context(session_id, session_data, current_result)

            # Check if Arena should trigger
            should_trigger, trigger_type, confidence = trigger_detector.should_trigger(
                user_message, context
            )

            if should_trigger:
                logger.info(f"Arena triggered for session {session_id}: {trigger_type} (confidence: {confidence:.2f})")

                # Execute Arena interpretation
                arena_result = self._execute_arena_interpretation(
                    user_message, session_id, trigger_type
                )

                # Update session state
                self.arena_states[session_id]['last_arena_time'] = time.time()
                self.arena_states[session_id]['arena_count'] += 1

                # Mark in session that Arena was used
                if session_data is not None:
                    session_data['arena_interpreted'] = True
                    session_data['last_arena_trigger'] = trigger_type

                return arena_result

        except Exception as e:
            logger.error(f"Error in Arena trigger check: {e}")

        return None

    def _prepare_arena_context(self, session_id: str, session_data: Dict[str, Any],
                              current_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare context for Arena trigger detection.

        Args:
            session_id: Session identifier
            session_data: Session data
            current_result: Current response

        Returns:
            Context dictionary for trigger detection
        """
        context = {
            'session_id': session_id,
            'analysis_complete': session_data.get('analysis_complete', False),
            'arena_interpreted': session_data.get('arena_interpreted', False),
            'data_loaded': session_data.get('data_loaded', False),
            'csv_loaded': session_data.get('csv_loaded', False),
            'shapefile_loaded': session_data.get('shapefile_loaded', False),
            'tpr_workflow_complete': session_data.get('tpr_workflow_complete', False),
            'itn_planning_complete': session_data.get('itn_planning_complete', False)
        }

        # Add statistics if available
        if hasattr(self, 'session_data') and session_id in self.session_data:
            try:
                from .arena_data_context import ArenaDataContextManager
                context_manager = ArenaDataContextManager(session_id)
                full_context = context_manager.load_full_context()

                context['statistics'] = full_context.get('statistics', {})
                context['visualizations'] = full_context.get('visualizations', {})
                context['data_quality'] = full_context.get('data_quality', {})

            except Exception as e:
                logger.debug(f"Could not load full context for trigger detection: {e}")

        # Add result context
        if 'visualizations' in current_result:
            context['last_visualization'] = True
            context['last_visualization_time'] = time.time()
            context['visualization_count'] = len(current_result['visualizations'])

        return context

    def _execute_arena_interpretation(self, user_message: str, session_id: str,
                                     trigger_type: str) -> Dict[str, Any]:
        """
        Execute Arena interpretation asynchronously.

        Args:
            user_message: User's message
            session_id: Session identifier
            trigger_type: Type of trigger

        Returns:
            Arena interpretation results
        """
        try:
            # Run async Arena interpretation
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                arena_result = loop.run_until_complete(
                    self.arena_manager.interpret_analysis_results(
                        session_id, user_message, trigger_type
                    )
                )
                return arena_result

            finally:
                loop.close()

        except Exception as e:
            logger.error(f"Error executing Arena interpretation: {e}")
            return None

    def _integrate_arena_insights(self, result: Dict[str, Any],
                                 arena_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Integrate Arena insights into the response.

        Args:
            result: Original response
            arena_result: Arena interpretation results

        Returns:
            Enhanced response with Arena insights
        """
        if not arena_result or not arena_result.get('success'):
            return result

        try:
            # Get trigger detector for formatting
            session_id = arena_result.get('session_id')
            trigger_detector = self.arena_states[session_id]['trigger_detector']

            # Format Arena insights for conversation
            arena_text = self.arena_manager.format_for_conversation(
                arena_result, trigger_detector
            )

            # Integrate into response
            if result.get('response'):
                # Add Arena insights after main response
                result['response'] += f"\n\n{arena_text}"
            else:
                result['response'] = arena_text

            # Add Arena metadata
            result['arena_triggered'] = True
            result['arena_trigger_type'] = arena_result.get('trigger_type')
            result['arena_confidence'] = arena_result.get('confidence_score', 0)
            result['arena_models'] = arena_result.get('models_used', [])

            # Add unique insights for potential follow-up
            if arena_result.get('unique_insights'):
                result['arena_insights_available'] = True
                result['arena_unique_insights'] = arena_result['unique_insights']

            # Add disagreements if present
            if arena_result.get('disagreements'):
                result['arena_disagreements'] = arena_result['disagreements']

            logger.info(f"Arena insights integrated successfully (confidence: {arena_result.get('confidence_score', 0):.2f})")

        except Exception as e:
            logger.error(f"Error integrating Arena insights: {e}")

        return result

    def handle_arena_follow_up(self, user_message: str, session_id: str,
                              previous_result: Dict[str, Any]) -> Optional[str]:
        """
        Handle follow-up questions about Arena interpretations.

        Args:
            user_message: User's follow-up message
            session_id: Session identifier
            previous_result: Previous response with Arena insights

        Returns:
            Follow-up response if applicable
        """
        if not previous_result.get('arena_triggered'):
            return None

        message_lower = user_message.lower()

        # Check for requests for more detail
        if any(word in message_lower for word in ['more', 'elaborate', 'expand', 'detail']):
            if 'arena_unique_insights' in previous_result:
                insights = previous_result['arena_unique_insights']
                response = "Here are additional unique perspectives from each model:\n\n"

                for model, insight in insights.items():
                    response += f"**{model}**: {insight}\n\n"

                return response

        # Check for disagreement exploration
        if any(word in message_lower for word in ['disagree', 'conflict', 'difference']):
            if 'arena_disagreements' in previous_result:
                disagreements = previous_result['arena_disagreements']
                response = "The models had the following points of disagreement:\n\n"

                for disagreement in disagreements:
                    response += f"• {disagreement}\n"

                response += "\nThese differences reflect varying analytical perspectives and should be considered when making decisions."
                return response

        return None


def patch_request_interpreter():
    """
    Patch the existing RequestInterpreter with Arena capabilities.

    This function should be called during application initialization to
    enable Arena interpretation features.
    """
    try:
        from app.core.request_interpreter import RequestInterpreter
        # Expose a RequestInterpreter attribute at module level for tests to patch
        globals()['RequestInterpreter'] = RequestInterpreter

        # Create enhanced class with Arena capabilities
        class EnhancedRequestInterpreter(ArenaIntegrationMixin, RequestInterpreter):
            """Request Interpreter with Arena multi-model interpretation capabilities."""

            def process_message(self, user_message: str, session_id: str,
                              session_data: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
                """Override to include Arena triggers."""
                return self.process_message_with_arena(user_message, session_id, session_data, **kwargs)

        # Replace the original class
        import app.core.request_interpreter
        app.core.request_interpreter.RequestInterpreter = EnhancedRequestInterpreter

        logger.info("RequestInterpreter successfully patched with Arena capabilities")
        return True

    except Exception as e:
        logger.error(f"Failed to patch RequestInterpreter: {e}")
        return False


# Initialization code for direct import
if __name__ != "__main__":
    # Attempt to patch on module import
    patch_success = patch_request_interpreter()
    if patch_success:
        logger.info("Arena integration patch applied successfully")
