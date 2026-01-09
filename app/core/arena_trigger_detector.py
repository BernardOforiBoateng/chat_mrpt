"""
Arena Conversational Trigger Detector

Detects when to automatically trigger Arena mode based on conversation context,
user queries, and analysis state. Enables natural, seamless integration of
multi-model interpretations without explicit user requests.
"""

import re
import logging
from typing import Dict, Any, Tuple, List, Optional
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)


class ConversationalArenaTrigger:
    """
    Detects when Arena mode should be triggered based on conversation patterns
    and analysis context.
    """

    # Explicit trigger patterns
    EXPLICIT_TRIGGERS = {
        'interpretation_request': [
            r'what does this mean',
            r'explain these results',
            r'explain further',
            r'interpret this',
            r'what are the implications',
            r'help me understand',
            r'what do you make of',
            r'can you explain',
            r'tell me what this shows'
        ],
        'comparison_request': [
            r'different perspectives',
            r'other interpretations',
            r'alternative views',
            r'what else could this mean',
            r'different opinions',
            r'another way to look at',
            r'compare interpretations',
            r'multiple viewpoints'
        ],
        'deep_dive': [
            r'tell me more about',
            r'dig deeper',
            r'explain why',
            r"what's driving",
            r'drill down',
            r'more detail on',
            r'elaborate on',
            r'break down'
        ],
        'uncertainty': [
            r'how confident',
            r'how sure',
            r'is this reliable',
            r'can we trust',
            r'margin of error',
            r'confidence level',
            r'how accurate',
            r'any doubts'
        ],
        'action_planning': [
            r'what should we do',
            r'next steps',
            r'recommendations',
            r'how to address',
            r'intervention strategies',
            r'action plan',
            r'what do you recommend',
            r'how to fix'
        ]
    }

    # Implicit trigger conditions
    IMPLICIT_TRIGGERS = {
        'post_analysis': {
            'condition': 'analysis_complete',
            'threshold': None,
            'description': 'Analysis just completed'
        },
        'high_risk_alert': {
            'condition': 'high_risk_count',
            'threshold': 10,
            'description': 'Many high-risk areas detected'
        },
        'anomaly_detected': {
            'condition': 'tpr_average',
            'threshold': 50,
            'description': 'Unusually high TPR detected'
        },
        'complex_results': {
            'condition': 'visualization_count',
            'threshold': 3,
            'description': 'Multiple visualizations generated'
        },
        'outlier_presence': {
            'condition': 'outlier_percentage',
            'threshold': 5,
            'description': 'Significant outliers detected'
        },
        'first_results_view': {
            'condition': 'first_view_after_analysis',
            'threshold': None,
            'description': 'First time viewing results'
        }
    }

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize trigger detector for a session.

        Args:
            session_id: Optional unique session identifier
        """
        self.session_id = session_id
        self.trigger_history = []
        self.last_arena_trigger = None
        self.cooldown_period = timedelta(minutes=5)  # Avoid triggering too frequently

    def should_trigger(self, message: str, context: Dict[str, Any]) -> Tuple[bool, str, float]:
        """
        Determine if Arena should be triggered based on message and context.

        Args:
            message: User's message
            context: Current session context including analysis state

        Returns:
            Tuple of (should_trigger, trigger_type, confidence_score)
        """
        # Check explicit triggers first (highest priority)
        explicit_result = self._check_explicit_triggers(message)
        if explicit_result[0]:
            # Apply cooldown only for explicit triggers
            if self._in_cooldown():
                logger.debug("Arena explicit trigger suppressed by cooldown")
                return False, None, 0.0
            logger.info(f"Explicit Arena trigger detected: {explicit_result[1]}")
            self._record_trigger(explicit_result[1], 'explicit')
            return explicit_result

        # Check implicit triggers based on context
        implicit_result = self._check_implicit_triggers(context)
        if implicit_result[0]:
            logger.info(f"Implicit Arena trigger detected: {implicit_result[1]}")
            self._record_trigger(implicit_result[1], 'implicit')
            return implicit_result

        # Check contextual triggers (combination of message and context)
        contextual_result = self._check_contextual_triggers(message, context)
        if contextual_result[0]:
            logger.info(f"Contextual Arena trigger detected: {contextual_result[1]}")
            self._record_trigger(contextual_result[1], 'contextual')
            return contextual_result

        return False, None, 0.0

    def _check_explicit_triggers(self, message: str) -> Tuple[bool, str, float]:
        """
        Check if message contains explicit trigger patterns.

        Args:
            message: User's message

        Returns:
            Tuple of (triggered, trigger_type, confidence)
        """
        message_lower = message.lower()

        for trigger_type, patterns in self.EXPLICIT_TRIGGERS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    # Calculate confidence based on pattern specificity
                    confidence = self._calculate_pattern_confidence(pattern, message_lower)
                    return True, trigger_type, confidence

        return False, None, 0.0

    def _check_implicit_triggers(self, context: Dict[str, Any]) -> Tuple[bool, str, float]:
        """
        Check implicit triggers based on analysis context.

        Args:
            context: Session context

        Returns:
            Tuple of (triggered, trigger_type, confidence)
        """
        # Check if analysis just completed and not yet interpreted
        if (context.get('analysis_complete') and
            not context.get('arena_interpreted') and
            not context.get('analysis_explained')):

            # Check if this is the first message after analysis
            if self._is_first_post_analysis_message(context):
                return True, 'post_analysis', 0.9

        # Check for high-risk scenarios
        stats = context.get('statistics', {})

        # High risk ward count
        if 'risk_distribution' in stats:
            high_risk = stats['risk_distribution'].get('High', 0)
            if high_risk >= self.IMPLICIT_TRIGGERS['high_risk_alert']['threshold']:
                return True, 'high_risk_alert', 0.8

        # High TPR average
        if 'tpr' in stats:
            tpr_mean = stats['tpr'].get('mean', 0)
            if tpr_mean >= self.IMPLICIT_TRIGGERS['anomaly_detected']['threshold']:
                return True, 'anomaly_detected', 0.85

        # Multiple visualizations generated
        viz_count = len(context.get('visualizations', {}).get('maps', [])) + \
                   len(context.get('visualizations', {}).get('charts', []))
        if viz_count >= self.IMPLICIT_TRIGGERS['complex_results']['threshold']:
            return True, 'complex_results', 0.7

        # Significant outliers
        if 'data_quality' in context:
            outliers = context['data_quality'].get('outliers', [])
            if outliers:
                total_outliers = sum(o.get('percentage', 0) for o in outliers)
                if total_outliers >= self.IMPLICIT_TRIGGERS['outlier_presence']['threshold']:
                    return True, 'outlier_presence', 0.75

        return False, None, 0.0

    def _check_contextual_triggers(self, message: str, context: Dict[str, Any]) -> Tuple[bool, str, float]:
        """
        Check triggers based on combination of message and context.

        Args:
            message: User's message
            context: Session context

        Returns:
            Tuple of (triggered, trigger_type, confidence)
        """
        message_lower = message.lower()

        # Questions about specific wards after analysis
        if context.get('analysis_complete'):
            # Check for ward-specific questions
            if re.search(r'ward|area|region|zone|lga', message_lower):
                if re.search(r'why|how|what|explain', message_lower):
                    return True, 'ward_investigation', 0.8

            # Questions about rankings
            if 'rank' in message_lower or 'top' in message_lower or 'highest' in message_lower:
                return True, 'ranking_explanation', 0.75

            # Questions about patterns
            if 'pattern' in message_lower or 'trend' in message_lower or 'cluster' in message_lower:
                return True, 'pattern_analysis', 0.8

        # Follow-up questions after visualization
        if context.get('last_visualization'):
            time_since_viz = datetime.now() - context.get('last_visualization_time', datetime.now())
            if time_since_viz < timedelta(minutes=2):
                # Quick follow-up after seeing visualization
                if any(word in message_lower for word in ['this', 'that', 'these', 'those', 'it']):
                    return True, 'visualization_followup', 0.7

        # Complex analytical questions
        analytical_keywords = ['correlation', 'relationship', 'impact', 'effect', 'cause',
                              'factor', 'driver', 'influence', 'contribute']
        if sum(1 for keyword in analytical_keywords if keyword in message_lower) >= 2:
            return True, 'analytical_inquiry', 0.75

        return False, None, 0.0

    def _calculate_pattern_confidence(self, pattern: str, message: str) -> float:
        """
        Calculate confidence score based on pattern match quality.

        Args:
            pattern: Regex pattern that matched
            message: User's message

        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence
        confidence = 0.7

        # Increase confidence for longer, more specific patterns
        if len(pattern) > 20:
            confidence += 0.1

        # Increase confidence if pattern matches early in message
        match = re.search(pattern, message)
        if match and match.start() < 10:
            confidence += 0.1

        # Increase confidence for question marks
        if '?' in message:
            confidence += 0.05

        return min(confidence, 1.0)

    def _is_first_post_analysis_message(self, context: Dict[str, Any]) -> bool:
        """
        Check if this is the first user message after analysis completion.

        Args:
            context: Session context

        Returns:
            True if first message post-analysis
        """
        # Check if analysis was completed recently
        if context.get('analysis_complete_time'):
            time_since_analysis = datetime.now() - context['analysis_complete_time']
            if time_since_analysis < timedelta(minutes=1):
                # Check if Arena hasn't been triggered yet for this analysis
                if not context.get('arena_interpreted'):
                    return True
        return False

    def _in_cooldown(self) -> bool:
        """
        Check if trigger is in cooldown period.

        Returns:
            True if in cooldown period
        """
        if self.last_arena_trigger:
            time_since_last = datetime.now() - self.last_arena_trigger
            return time_since_last < self.cooldown_period
        return False

    def _record_trigger(self, trigger_type: str, trigger_category: str):
        """
        Record trigger event for history and cooldown.

        Args:
            trigger_type: Type of trigger
            trigger_category: Category (explicit/implicit/contextual)
        """
        self.trigger_history.append({
            'timestamp': datetime.now(),
            'type': trigger_type,
            'category': trigger_category
        })
        self.last_arena_trigger = datetime.now()

    def get_trigger_explanation(self, trigger_type: str) -> str:
        """
        Get human-readable explanation for why Arena was triggered.

        Args:
            trigger_type: Type of trigger

        Returns:
            Explanation string
        """
        explanations = {
            'interpretation_request': "I'll provide multiple perspectives on these results",
            'comparison_request': "Let me show you different analytical viewpoints",
            'deep_dive': "I'll conduct a detailed multi-angle analysis",
            'uncertainty': "I'll assess confidence levels from multiple perspectives",
            'action_planning': "I'll gather diverse recommendations for action",
            'post_analysis': "Your analysis is complete. Let me provide comprehensive interpretations",
            'high_risk_alert': "With many high-risk areas detected, multiple perspectives will help prioritize",
            'anomaly_detected': "These unusual patterns warrant investigation from different angles",
            'complex_results': "Given the complexity of results, diverse interpretations will be helpful",
            'outlier_presence': "Significant outliers detected - let's examine from multiple viewpoints",
            'ward_investigation': "I'll analyze this ward-specific question from multiple angles",
            'ranking_explanation': "Let me explain these rankings from different perspectives",
            'pattern_analysis': "I'll identify patterns using diverse analytical approaches",
            'visualization_followup': "I'll interpret this visualization from multiple viewpoints",
            'analytical_inquiry': "This complex question benefits from multi-model analysis"
        }

        return explanations.get(trigger_type, "I'll provide multiple analytical perspectives")

    def should_show_divergence(self, confidence_score: float) -> bool:
        """
        Determine whether to show divergent opinions based on confidence.

        Args:
            confidence_score: Confidence in trigger detection

        Returns:
            True if divergent opinions should be shown
        """
        # Show divergence for high-confidence triggers or explicit requests
        return confidence_score > 0.8

    def get_cooldown_status(self) -> Dict[str, Any]:
        """
        Get current cooldown status.

        Returns:
            Dictionary with cooldown information
        """
        if self.last_arena_trigger:
            time_since = datetime.now() - self.last_arena_trigger
            remaining = max(timedelta(0), self.cooldown_period - time_since)
            return {
                'in_cooldown': remaining > timedelta(0),
                'remaining_seconds': remaining.total_seconds(),
                'last_trigger': self.last_arena_trigger.isoformat()
            }
        return {
            'in_cooldown': False,
            'remaining_seconds': 0,
            'last_trigger': None
        }

    def reset_cooldown(self):
        """Reset the cooldown timer."""
        self.last_arena_trigger = None

    def get_trigger_history(self) -> List[Dict[str, Any]]:
        """
        Get history of triggers for this session.

        Returns:
            List of trigger events
        """
        return self.trigger_history

    def detect_trigger(self, user_message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simplified trigger detection method for compatibility.

        Args:
            user_message: User's message to check
            context: Current session context

        Returns:
            Dict with 'use_arena' boolean and details
        """
        # Special handling for interpretation requests when data is loaded
        message_lower = user_message.lower()

        # If analysis is complete and data is loaded, be more liberal with triggers
        if context.get('analysis_complete', False) and context.get('data_loaded', False):
            # Any question about results, interpretation, or specific wards
            interpretation_keywords = ['explain', 'what does', 'mean', 'why', 'how', 'interpret']
            ward_keywords = ['ward', 'area', 'region', 'risk']

            has_interpretation = any(kw in message_lower for kw in interpretation_keywords)
            has_ward = any(kw in message_lower for kw in ward_keywords)

            if has_interpretation or has_ward:
                return {
                    'use_arena': True,
                    'trigger_type': 'interpretation_request',
                    'confidence': 0.9,
                    'reason': "I'll provide multiple perspectives on these results"
                }

        # Check if data is loaded
        if not context.get('data_loaded', False):
            return {'use_arena': False, 'reason': 'No data loaded'}

        # Use the main should_trigger method for other cases
        should_trigger, trigger_type, confidence = self.should_trigger(user_message, context)

        return {
            'use_arena': should_trigger,
            'trigger_type': trigger_type,
            'confidence': confidence,
            'reason': self.get_trigger_explanation(trigger_type) if should_trigger else None
        }
