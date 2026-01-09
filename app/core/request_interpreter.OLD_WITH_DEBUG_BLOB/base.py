"""True py-sidebot implementation for ChatMRPT."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List, Optional

from flask import current_app

from .conversation import ConversationMixin
from .tooling import ToolingMixin
from .analysis_methods import AnalysisToolsMixin
from .context import ContextMixin
from .streaming import StreamingMixin

logger = logging.getLogger(__name__)

ARENA_INTEGRATION_AVAILABLE = False  # Disabled to prevent duplicate routing


class RequestInterpreter(
    ConversationMixin,
    ToolingMixin,
    AnalysisToolsMixin,
    ContextMixin,
    StreamingMixin,
):
    """Orchestrates tool-enabled conversations using the py-sidebot pattern."""

    @staticmethod
    def force_session_save() -> None:
        """Force Flask session to persist when using Redis backend."""
        from flask import session

        session.permanent = True
        session.modified = True
        for key in ['data_loaded', 'csv_loaded', 'shapefile_loaded']:
            if key in session:
                session[key] = session[key]

    def __init__(
        self,
        llm_manager,
        data_service,
        analysis_service,
        visualization_service,
    ) -> None:
        self.llm_manager = llm_manager
        self.data_service = data_service
        self.analysis_service = analysis_service
        self.visualization_service = visualization_service

        self.conversation_history: Dict[str, List[Dict[str, str]]] = {}
        self.session_data: Dict[str, Dict[str, Any]] = {}
        self._memory_summary_tracker: Dict[str, Dict[str, Any]] = {}
        self.choice_interpreter = None
        self.tool_intent_resolver = None

        try:
            from app.services.memory_service import get_memory_service

            self.memory = get_memory_service()
        except Exception as exc:  # pragma: no cover - defensive
            logger.debug("Memory service not available: %s", exc)
            self.memory = None

        try:
            from app.core.session_context_service import SessionContextService
            from app.core.data_repository import DataRepository
            from app.core.prompt_builder import PromptBuilder
            from app.core.tool_runner import ToolRunner
            from app.core.llm_orchestrator import LLMOrchestrator

            self.data_repo = DataRepository()
            self.context_service = SessionContextService(self.data_repo)
            self.prompt_builder = PromptBuilder()
            self.tool_runner = ToolRunner(
                fallbacks={
                    'explain_analysis_methodology': self._explain_analysis_methodology,
                    'run_malaria_risk_analysis': self._run_malaria_risk_analysis,
                    'create_settlement_map': self._create_settlement_map,
                    'show_settlement_statistics': self._show_settlement_statistics,
                    'list_dataset_columns': self._list_dataset_columns,
                }
            )
            self.orchestrator = LLMOrchestrator()
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Refactor services init failed (non-fatal): %s", exc)
            self.context_service = None
            self.prompt_builder = None
            self.tool_runner = None
            self.orchestrator = None

        try:
            from app.core.choice_interpreter import ChoiceInterpreter

            self.choice_interpreter = ChoiceInterpreter(self.llm_manager)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("ChoiceInterpreter init failed (non-fatal): %s", exc)
            self.choice_interpreter = None

        try:
            from app.core.tool_intent_resolver import ToolIntentResolver

            self.tool_intent_resolver = ToolIntentResolver(self.llm_manager)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("ToolIntentResolver init failed (non-fatal): %s", exc)
            self.tool_intent_resolver = None

        self.conversational_data_access = None
        self.tools: Dict[str, Any] = {}
        self.data_agents: Dict[str, Any] = {}

        self._register_tools()

    def process_message(
        self,
        user_message: str,
        session_id: str,
        session_data: Optional[Dict[str, Any]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Process a user message and return the assistant response."""
        start_time = time.time()

        try:
            logger.info("=" * 60)
            logger.info("📊 ANALYSIS: RequestInterpreter.process_message")
            logger.info("  📝 User Message: %s...", user_message[:100])
            logger.info("  🆔 Session ID: %s", session_id)
            logger.info(
                "  📂 Session Keys: %s",
                list(session_data.keys()) if session_data else 'None',
            )
            logger.info("  🎯 Analysis Mode: %s", kwargs.get('is_data_analysis', False))
            logger.info("  🔄 Tab Context: %s", kwargs.get('tab_context', 'unknown'))

            from flask import session as flask_session

            logger.info("  📊 Session State:")
            logger.info(
                "    - Analysis Complete: %s",
                flask_session.get('analysis_complete', False),
            )
            logger.info(
                "    - Data Loaded: %s", flask_session.get('data_loaded', False)
            )
            logger.info(
                "    - ITN Planning Complete: %s",
                flask_session.get('itn_planning_complete', False),
            )
            logger.info(
                "    - TPR Workflow Complete: %s",
                flask_session.get('tpr_workflow_complete', False),
            )
            logger.info("=" * 60)

            logger.info(
                "🔄 Checking special workflows for: %s...", user_message[:50]
            )
            special_result = self._handle_special_workflows(
                user_message,
                session_id,
                session_data,
                **kwargs,
            )
            if special_result:
                return special_result

            session_context = self._get_session_context(session_id, session_data)
            session_context = self._enrich_session_context_with_memory(
                session_id,
                session_context,
            )

            direct_result = self._attempt_direct_tool_resolution(
                user_message,
                session_id,
                session_context,
            )
            if direct_result:
                self._store_conversation(
                    session_id,
                    user_message,
                    direct_result.get('response', ''),
                )
                direct_result['total_time'] = time.time() - start_time
                return direct_result

            if not session_context.get('data_loaded', False):
                return self._simple_conversational_response(
                    user_message,
                    session_context,
                    session_id,
                )

            system_prompt = self._build_system_prompt_refactored(
                session_context,
                session_id,
            )

            if self.tool_runner and self.orchestrator:
                function_schemas = self.tool_runner.get_function_schemas()
                result = self.orchestrator.run_with_tools(
                    self.llm_manager,
                    system_prompt,
                    user_message,
                    function_schemas,
                    session_id,
                    self.tool_runner,
                )
            else:
                result = self._llm_with_tools(
                    user_message,
                    session_context,
                    session_id,
                )

            self._store_conversation(
                session_id,
                user_message,
                result.get('response', ''),
            )

            result['total_time'] = time.time() - start_time
            return result

        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Error in py-sidebot processing: %s", exc)
            return {
                'status': 'error',
                'response': f'I encountered an issue: {str(exc)}',
                'tools_used': [],
            }
