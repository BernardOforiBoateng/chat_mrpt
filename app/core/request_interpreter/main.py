"""Core request interpreter coordinating LLM + tool execution."""
import logging
import time
from typing import Dict, Any, List, Optional
from flask import current_app
from .session import SessionMixin
from .tooling import ToolingMixin
from .streaming import StreamingMixin
from .analysis_tools import AnalysisToolsMixin
from .visualization_tools import VisualizationToolsMixin
from .data_tools import DataToolsMixin
from .prompting import PromptMixin
logger = logging.getLogger(__name__)
ARENA_INTEGRATION_AVAILABLE = False

class RequestInterpreter(SessionMixin, ToolingMixin, StreamingMixin, AnalysisToolsMixin, VisualizationToolsMixin, DataToolsMixin, PromptMixin):
    """True py-sidebot inspired interpreter wiring LLMs to Python tools."""

    @staticmethod
    def force_session_save():
        """Force Flask session to save when using Redis backend."""
        from flask import session
        session.permanent = True
        session.modified = True
        for key in ['data_loaded', 'csv_loaded', 'shapefile_loaded']:
            if key in session:
                session[key] = session[key]

    def __init__(self, llm_manager, data_service, analysis_service, visualization_service):
        self.llm_manager = llm_manager
        self.data_service = data_service
        self.analysis_service = analysis_service
        self.visualization_service = visualization_service
        self.conversation_history = {}
        self.session_data = {}
        self._memory_summary_tracker: Dict[str, Dict[str, Any]] = {}
        self.choice_interpreter = None
        self.tool_intent_resolver = None
        try:
            from app.services.memory_service import get_memory_service
            self.memory = get_memory_service()
        except Exception as e:
            logger.debug(f'Memory service not available: {e}')
            self.memory = None
        try:
            from .session_context_service import SessionContextService
            from .data_repository import DataRepository
            from .prompt_builder import PromptBuilder
            from .tool_runner import ToolRunner
            from .llm_orchestrator import LLMOrchestrator
            self.data_repo = DataRepository()
            self.context_service = SessionContextService(self.data_repo)
            self.prompt_builder = PromptBuilder()
            self.tool_runner = ToolRunner(fallbacks={'explain_analysis_methodology': self._explain_analysis_methodology, 'run_malaria_risk_analysis': self._run_malaria_risk_analysis, 'create_settlement_map': self._create_settlement_map, 'show_settlement_statistics': self._show_settlement_statistics, 'list_dataset_columns': self._list_dataset_columns})
            self.orchestrator = LLMOrchestrator()
        except Exception as e:
            logger.warning(f'Refactor services init failed (non-fatal): {e}')
            self.context_service = None
            self.prompt_builder = None
            self.tool_runner = None
            self.orchestrator = None
        try:
            from .choice_interpreter import ChoiceInterpreter
            self.choice_interpreter = ChoiceInterpreter(self.llm_manager)
        except Exception as e:
            logger.warning(f'ChoiceInterpreter init failed (non-fatal): {e}')
            self.choice_interpreter = None
        try:
            from .tool_intent_resolver import ToolIntentResolver
            self.tool_intent_resolver = ToolIntentResolver(self.llm_manager)
        except Exception as e:
            logger.warning(f'ToolIntentResolver init failed (non-fatal): {e}')
            self.tool_intent_resolver = None
        self.conversational_data_access = None
        self.tools = {}
        self.data_agents = {}
        self._register_tools()

    def process_message(self, user_message: str, session_id: str, session_data: Dict[str, Any]=None, **kwargs) -> Dict[str, Any]:
        """py-sidebot pattern: Pass message directly to LLM with tools."""
        start_time = time.time()
        try:
            logger.info('=' * 60)
            logger.info('📊 ANALYSIS: RequestInterpreter.process_message')
            logger.info(f'  📝 User Message: {user_message[:100]}...')
            logger.info(f'  🆔 Session ID: {session_id}')
            logger.info(f"  📂 Session Keys: {(list(session_data.keys()) if session_data else 'None')}")
            logger.info(f"  🎯 Analysis Mode: {kwargs.get('is_data_analysis', False)}")
            logger.info(f"  🔄 Tab Context: {kwargs.get('tab_context', 'unknown')}")
            from flask import session as flask_session
            logger.info('  📊 Session State:')
            logger.info(f"    - Analysis Complete: {flask_session.get('analysis_complete', False)}")
            logger.info(f"    - Data Loaded: {flask_session.get('data_loaded', False)}")
            logger.info(f"    - ITN Planning Complete: {flask_session.get('itn_planning_complete', False)}")
            logger.info(f"    - TPR Workflow Complete: {flask_session.get('tpr_workflow_complete', False)}")
            logger.info('=' * 60)
            logger.info(f'🔄 Checking special workflows for: {user_message[:50]}...')
            special_result = self._handle_special_workflows(user_message, session_id, session_data, **kwargs)
            if special_result:
                return special_result
            session_context = self._get_session_context(session_id, session_data)
            session_context = self._enrich_session_context_with_memory(session_id, session_context)
            direct_result = self._attempt_direct_tool_resolution(user_message, session_id, session_context)
            if direct_result:
                self._store_conversation(session_id, user_message, direct_result.get('response', ''))
                direct_result['total_time'] = time.time() - start_time
                return direct_result
            if not session_context.get('data_loaded', False):
                return self._simple_conversational_response(user_message, session_context, session_id)
            system_prompt = self._build_system_prompt_refactored(session_context, session_id)
            if self.tool_runner and self.orchestrator:
                function_schemas = self.tool_runner.get_function_schemas()
                result = self.orchestrator.run_with_tools(self.llm_manager, system_prompt, user_message, function_schemas, session_id, self.tool_runner)
            else:
                result = self._llm_with_tools(user_message, session_context, session_id)
            self._store_conversation(session_id, user_message, result.get('response', ''))
            result['total_time'] = time.time() - start_time
            return result
        except Exception as e:
            logger.error(f'Error in py-sidebot processing: {e}')
            return {'status': 'error', 'response': f'I encountered an issue: {str(e)}', 'tools_used': []}

    def _explain_analysis_methodology(self, session_id: str, method: str='both'):
        """Explain how malaria risk analysis methodologies work (composite scoring, PCA, or both)."""
        try:
            if method == 'composite':
                explanation = '**Composite Scoring Methodology**\n\nComposite scoring combines multiple malaria risk indicators into a single vulnerability score:\n\n1. **Variable Selection**: Selects scientifically-validated variables based on Nigerian geopolitical zones\n2. **Normalization**: Standardizes all variables to 0-1 scale for fair comparison\n3. **Equal Weighting**: All variables contribute equally to the final score\n4. **Aggregation**: Sums normalized values to create composite vulnerability score\n5. **Ranking**: Ranks wards from highest to lowest risk for intervention targeting\n\nThis method is transparent, interpretable, and follows WHO guidelines for malaria stratification.'
            elif method == 'pca':
                explanation = '**Principal Component Analysis (PCA) Methodology**\n\nPCA reduces dimensionality while preserving variance in malaria risk data:\n\n1. **Data Standardization**: Centers and scales all variables\n2. **Covariance Analysis**: Identifies relationships between variables\n3. **Component Extraction**: Finds principal components that explain maximum variance\n4. **Weight Calculation**: Automatically determines variable importance\n5. **Score Generation**: Creates data-driven vulnerability scores\n6. **Interpretation**: First component typically captures overall malaria risk\n\nThis method is statistically robust and reveals hidden patterns in the data.'
            else:
                explanation = '**Dual-Method Malaria Risk Analysis**\n\nChatMRPT uses both composite scoring and PCA for comprehensive assessment:\n\n**Composite Scoring**: Transparent, equal-weighted approach following WHO guidelines\n- Pros: Interpretable, policy-friendly, scientifically grounded\n- Use when: Clear intervention priorities needed\n\n**PCA Analysis**: Statistical approach revealing data patterns\n- Pros: Objective, captures complex relationships, statistically robust\n- Use when: Exploring underlying risk structures\n\n**Comparison**: Both methods often agree on high-risk areas but may differ in rankings. Use both for robust decision-making and to validate findings.'
            return explanation
        except Exception as e:
            return f'Error explaining methodology: {str(e)}'
