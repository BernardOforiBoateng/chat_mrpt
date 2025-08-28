"""
Hybrid LLM Router for ChatMRPT

Routes queries to appropriate LLM based on complexity and requirements:
- Complex tool-calling workflows → OpenAI
- General conversational queries → Arena mode with local models
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Classification of query types."""
    TOOL_CALLING = "tool_calling"  # Requires function calling
    DATA_ANALYSIS = "data_analysis"  # Data Analysis V3 workflow
    TPR_WORKFLOW = "tpr_workflow"  # TPR calculation workflow
    VISUALIZATION = "visualization"  # Chart/map generation
    GENERAL_CHAT = "general_chat"  # Simple conversational
    REPORT_GENERATION = "report_generation"  # Report building
    FILE_OPERATION = "file_operation"  # File upload/download


class RoutingDecision:
    """Represents a routing decision with reasoning."""
    
    def __init__(self, route: str, query_type: QueryType, reasoning: str, 
                 use_arena: bool = False, confidence: float = 1.0):
        self.route = route  # 'openai' or 'arena'
        self.query_type = query_type
        self.reasoning = reasoning
        self.use_arena = use_arena
        self.confidence = confidence
        self.selected_models = []  # For arena mode


class HybridLLMRouter:
    """
    Intelligent router that decides whether to use OpenAI or Arena mode.
    
    Decision factors:
    1. Query complexity
    2. Tool calling requirements
    3. Session context (data loaded, workflow active)
    4. User preferences
    """
    
    def __init__(self, arena_manager=None):
        self.arena_manager = arena_manager
        
        # Keywords that indicate tool calling needed
        self.tool_keywords = [
            'calculate', 'analyze', 'visualize', 'create map', 'generate chart',
            'test positivity rate', 'tpr', 'risk analysis', 'vulnerability',
            'export', 'download', 'save report', 'pca analysis'
        ]
        
        # Keywords for general chat
        self.chat_keywords = [
            'what is', 'explain', 'tell me about', 'how does', 'why',
            'when', 'who', 'describe', 'definition', 'meaning',
            'help', 'can you', 'should i', 'best practice'
        ]
        
        # Compile regex patterns for efficiency
        self.tool_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(kw) for kw in self.tool_keywords) + r')\b',
            re.IGNORECASE
        )
        self.chat_pattern = re.compile(
            r'\b(' + '|'.join(re.escape(kw) for kw in self.chat_keywords) + r')\b',
            re.IGNORECASE
        )
        
        logger.info("Hybrid LLM Router initialized")
    
    def route_query(self, user_message: str, session_context: Dict[str, Any]) -> RoutingDecision:
        """
        Determine the best route for a query.
        
        Args:
            user_message: The user's query
            session_context: Current session state including:
                - data_loaded: bool
                - csv_loaded: bool
                - shapefile_loaded: bool
                - tpr_workflow_active: bool
                - analysis_complete: bool
                - current_workflow: str
                - conversation_history: list
                
        Returns:
            RoutingDecision object with routing information
        """
        # Normalize message for analysis
        message_lower = user_message.lower().strip()
        
        # Check session context first (highest priority)
        decision = self._check_session_context(session_context, message_lower)
        if decision:
            return decision
        
        # Check for explicit tool requirements
        decision = self._check_tool_requirements(message_lower, session_context)
        if decision:
            return decision
        
        # Check query complexity
        decision = self._analyze_query_complexity(message_lower, session_context)
        if decision:
            return decision
        
        # Default to arena mode for general chat
        return RoutingDecision(
            route='arena',
            query_type=QueryType.GENERAL_CHAT,
            reasoning='General conversational query suitable for model comparison',
            use_arena=True,
            confidence=0.9
        )
    
    def _check_session_context(self, context: Dict[str, Any], message: str) -> Optional[RoutingDecision]:
        """Check session context for routing hints."""
        
        # Active TPR workflow must use OpenAI
        if context.get('tpr_workflow_active'):
            return RoutingDecision(
                route='openai',
                query_type=QueryType.TPR_WORKFLOW,
                reasoning='TPR workflow active, requires OpenAI for tool calling',
                use_arena=False,
                confidence=1.0
            )
        
        # Data Analysis V3 tab active
        if context.get('current_tab') == 'data_analysis':
            return RoutingDecision(
                route='openai',
                query_type=QueryType.DATA_ANALYSIS,
                reasoning='Data Analysis V3 tab requires OpenAI with LangGraph',
                use_arena=False,
                confidence=1.0
            )
        
        # Data loaded and user asking for analysis
        if context.get('data_loaded') and any(kw in message for kw in ['analyze', 'calculate', 'show me']):
            return RoutingDecision(
                route='openai',
                query_type=QueryType.TOOL_CALLING,
                reasoning='Data loaded and analysis requested, needs tool calling',
                use_arena=False,
                confidence=0.95
            )
        
        return None
    
    def _check_tool_requirements(self, message: str, context: Dict[str, Any]) -> Optional[RoutingDecision]:
        """Check if query explicitly requires tool calling."""
        
        # Check for tool keywords
        if self.tool_pattern.search(message):
            # Special case: "What is TPR?" is educational, not calculation
            if 'what is' in message and not context.get('data_loaded'):
                return None  # Let it fall through to general chat
            
            return RoutingDecision(
                route='openai',
                query_type=QueryType.TOOL_CALLING,
                reasoning='Query contains tool-calling keywords',
                use_arena=False,
                confidence=0.9
            )
        
        # Check for file operations
        if any(kw in message for kw in ['upload', 'download', 'export', 'save']):
            return RoutingDecision(
                route='openai',
                query_type=QueryType.FILE_OPERATION,
                reasoning='File operation requested',
                use_arena=False,
                confidence=0.95
            )
        
        # Check for visualization requests
        if any(kw in message for kw in ['map', 'chart', 'graph', 'plot', 'visualize']):
            return RoutingDecision(
                route='openai',
                query_type=QueryType.VISUALIZATION,
                reasoning='Visualization requested, needs tool calling',
                use_arena=False,
                confidence=0.9
            )
        
        return None
    
    def _analyze_query_complexity(self, message: str, context: Dict[str, Any]) -> Optional[RoutingDecision]:
        """Analyze query complexity to determine routing."""
        
        # Simple questions about malaria (good for arena)
        if self.chat_pattern.search(message) and not context.get('data_loaded'):
            return RoutingDecision(
                route='arena',
                query_type=QueryType.GENERAL_CHAT,
                reasoning='General knowledge question suitable for comparison',
                use_arena=True,
                confidence=0.85
            )
        
        # Multi-step reasoning (needs OpenAI)
        if len(message.split()) > 50 or message.count('and') > 3:
            return RoutingDecision(
                route='openai',
                query_type=QueryType.TOOL_CALLING,
                reasoning='Complex multi-step query requires advanced reasoning',
                use_arena=False,
                confidence=0.8
            )
        
        return None
    
    def should_use_arena(self, user_message: str, session_context: Dict[str, Any]) -> bool:
        """
        Simple boolean check for arena mode eligibility.
        
        Args:
            user_message: The user's query
            session_context: Current session state
            
        Returns:
            True if arena mode should be used, False otherwise
        """
        decision = self.route_query(user_message, session_context)
        return decision.use_arena
    
    def get_arena_models(self) -> Tuple[str, str]:
        """
        Get a pair of models for arena comparison.
        
        Returns:
            Tuple of (model_a, model_b) names
        """
        if not self.arena_manager:
            # Fallback models if arena manager not initialized
            return ('llama-3.1-8b', 'mistral-7b')
        
        return self.arena_manager.get_random_model_pair()
    
    def log_routing_decision(self, decision: RoutingDecision, session_id: str):
        """Log routing decision for analysis."""
        logger.info(f"[Session {session_id}] Routed to {decision.route}: "
                   f"Type={decision.query_type.value}, "
                   f"Confidence={decision.confidence:.2f}, "
                   f"Reason={decision.reasoning}")
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get statistics about routing decisions."""
        # This would connect to a database in production
        return {
            'total_queries': 0,
            'openai_routes': 0,
            'arena_routes': 0,
            'routing_distribution': {
                QueryType.TOOL_CALLING.value: 0,
                QueryType.DATA_ANALYSIS.value: 0,
                QueryType.GENERAL_CHAT.value: 0,
            }
        }


class RouterConfig:
    """Configuration for the hybrid router."""
    
    def __init__(self):
        self.enable_arena = True
        self.arena_probability = 1.0  # Probability of using arena when eligible
        self.force_openai_for_errors = True  # Fallback to OpenAI on errors
        self.max_arena_retries = 2
        self.preferred_models = ['llama-3.1-8b', 'mistral-7b']
        self.blocked_models = []  # Models to never use
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            'enable_arena': self.enable_arena,
            'arena_probability': self.arena_probability,
            'force_openai_for_errors': self.force_openai_for_errors,
            'max_arena_retries': self.max_arena_retries,
            'preferred_models': self.preferred_models,
            'blocked_models': self.blocked_models
        }