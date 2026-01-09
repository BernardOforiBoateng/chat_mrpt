"""Tool registration and invocation helpers for the request interpreter."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class ToolingMixin:
    def _register_tools(self):
        """Register actual Python functions as tools - true py-sidebot style."""
        logger.info("Registering tools - py-sidebot pattern")

        # Register analysis tools
        self.tools['run_malaria_risk_analysis'] = self._run_malaria_risk_analysis
        # Disabled single-method tools to prevent confusion
        # self.tools['run_composite_analysis'] = self._run_composite_analysis
        # self.tools['run_pca_analysis'] = self._run_pca_analysis

        # Register visualization tools
        self.tools['create_vulnerability_map'] = self._create_vulnerability_map
        # REMOVED: create_box_plot - Tool #19 (analyze_data_with_python) can create matplotlib box plots
        # self.tools['create_box_plot'] = self._create_box_plot
        self.tools['create_pca_map'] = self._create_pca_map
        self.tools['create_variable_distribution'] = self._create_variable_distribution
        self.tools['create_urban_extent_map'] = self._create_urban_extent_map
        self.tools['create_decision_tree'] = self._create_decision_tree
        self.tools['create_composite_score_maps'] = self._create_composite_score_maps

        # Register settlement visualization tools
        self.tools['create_settlement_map'] = self._create_settlement_map
        self.tools['show_settlement_statistics'] = self._show_settlement_statistics

        # REMOVED: Redundant data tools - Tool #19 (analyze_data_with_python) handles all of these
        # self.tools['execute_data_query'] = self._execute_data_query  # Tool #19 does pandas queries
        # self.tools['execute_sql_query'] = self._execute_sql_query  # Tool #19 does SQL-equivalent (better!)
        # self.tools['run_data_quality_check'] = self._run_data_quality_check  # Tool #19 does df.info(), df.describe()

        # Register explanation tools
        self.tools['explain_analysis_methodology'] = self._explain_analysis_methodology

        # NEW: ITN Planning Tool
        self.tools['run_itn_planning'] = self._run_itn_planning

        # NEW: Python execution tool (Tool #19) - Replaces execute_data_query, execute_sql_query, run_data_quality_check, create_box_plot
        self.tools['analyze_data_with_python'] = self._analyze_data_with_python

        # Dataset exploration helpers
        self.tools['list_dataset_columns'] = self._list_dataset_columns

        logger.info(f"Registered {len(self.tools)} tools (4 redundant tools removed, now handled by analyze_data_with_python)")

    # ------------------------------------------------------------------
    # Tool intent routing helpers
    # ------------------------------------------------------------------
    def _get_session_state(self, session_id: str) -> Dict[str, Any]:
        state = self.session_data.setdefault(session_id, {})
        state.setdefault('history', [])
        state.setdefault('last_tool', None)
        state.setdefault('last_variable_distribution', None)
        state.setdefault('recent_variables', [])
        return state

    def _record_tool_invocation(self, session_id: str, tool_name: str, args: Dict[str, Any]) -> None:
        state = self._get_session_state(session_id)
        entry = {
            'tool': tool_name,
            'args': dict(args or {}),
            'timestamp': time.time(),
        }
        state['history'].append(entry)
        state['last_tool'] = tool_name
        if len(state['history']) > 40:
            state['history'] = state['history'][-40:]

        if tool_name == 'create_variable_distribution':
            variable = args.get('variable_name') or args.get('map_variable') or args.get('variable')
            if variable:
                state['last_variable_distribution'] = variable
                recent = state.setdefault('recent_variables', [])
                recent.append(variable)
                if len(recent) > 10:
                    state['recent_variables'] = recent[-10:]

    def _attempt_direct_tool_resolution(
        self,
        user_message: str,
        session_id: str,
        session_context: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if not self.tool_intent_resolver:
            return None

        session_state = self._get_session_state(session_id)
        resolution = self.tool_intent_resolver.resolve(user_message, session_context, session_state)
        if not resolution:
            return None

        logger.info(
            "🧠 ToolIntentResolver match: %s (confidence=%.2f, reason=%s)",
            resolution.tool,
            resolution.confidence,
            resolution.reason,
        )

        final_args = self._finalize_arguments_for_tool(
            resolution,
            user_message,
            session_id,
            session_context,
            session_state,
        )
        if final_args is None:
            logger.info("🧠 Intent resolved to %s but arguments missing", resolution.tool)
            return None

        execution_result = self._execute_direct_tool(resolution, session_id, final_args)
        self._record_tool_invocation(session_id, resolution.tool, final_args)

        # Annotate debug metadata
        debug_block = execution_result.setdefault('debug', {})
        debug_block['intent_resolver'] = {
            'tool': resolution.tool,
            'confidence': resolution.confidence,
            'score': resolution.score,
            'reason': resolution.reason,
            'matched_terms': list(resolution.matched_terms),
            'final_args': final_args,
        }
        execution_result.setdefault('tools_used', [resolution.tool])

        # Surface lightweight debug info for visibility (shown as collapsible block)
        debug_note = (
            f"<details><summary>Debug: intent resolver</summary>"
            f"Tool → {resolution.tool} | score={resolution.score:.2f} | confidence={resolution.confidence:.2f}\n"
            f"Args → {final_args}\n"
            f"Matched terms → {', '.join(resolution.matched_terms) if resolution.matched_terms else 'n/a'}"
            f"</details>"
        )
        base_response = execution_result.get('response') or execution_result.get('message') or ''
        if base_response:
            execution_result['response'] = f"{base_response}\n\n{debug_note}"
            execution_result['message'] = execution_result['response']
        else:
            execution_result['response'] = debug_note
            execution_result['message'] = debug_note

        return execution_result

    def _finalize_arguments_for_tool(
        self,
        resolution,
        user_message: str,
        session_id: str,
        session_context: Dict[str, Any],
        session_state: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        args = dict(resolution.inferred_args or {})

        # Use ChoiceInterpreter to refine/fill arguments when available
        need_choice = resolution.requires_args or (not args and resolution.supports_choice_interpreter)
        if self.choice_interpreter and resolution.supports_choice_interpreter and need_choice:
            try:
                columns_context = {
                    'columns': session_context.get('columns', []),
                    'schema_columns': session_context.get('schema_columns', []),
                }
                memory_summary = session_context.get('memory_summary')
                choice = self.choice_interpreter.resolve(
                    resolution.tool,
                    user_message,
                    memory_summary=memory_summary,
                    columns_context=columns_context,
                    session_id=session_id,
                )
                if choice and isinstance(choice.get('args'), dict):
                    choice_conf = float(choice.get('confidence', 0.0))
                    if choice_conf >= 0.35:
                        args.update(choice['args'])
            except Exception as exc:
                logger.warning(f"ChoiceInterpreter failed for {resolution.tool}: {exc}")

        normalized_args = self._normalize_tool_arguments(
            resolution.tool,
            args,
            user_message,
            session_state,
        )

        if resolution.requires_args and not normalized_args:
            return None

        return normalized_args

    def _normalize_tool_arguments(
        self,
        tool_name: str,
        args: Dict[str, Any],
        user_message: str,
        session_state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Normalize raw argument dict into the signature expected by helpers."""
        normalized = {k: v for k, v in (args or {}).items() if v not in (None, "", [])}

        if tool_name == 'create_variable_distribution':
            candidate = (
                normalized.pop('map_variable', None)
                or normalized.get('variable')
                or normalized.get('variable_name')
            )
            if candidate:
                normalized['variable_name'] = candidate
            elif session_state.get('last_variable_distribution') and any(
                token in user_message.lower() for token in ['it', 'them', 'that', 'those', 'these']
            ):
                normalized['variable_name'] = session_state['last_variable_distribution']

        if tool_name == 'run_malaria_risk_analysis':
            variables = normalized.get('variables')
            if isinstance(variables, str):
                normalized['variables'] = [v.strip() for v in variables.split(',') if v.strip()]

        if tool_name == 'analyze_data_with_python':
            normalized.setdefault('query', user_message)

        if tool_name == 'list_dataset_columns':
            page = normalized.get('page')
            if isinstance(page, str) and page.isdigit():
                normalized['page'] = int(page)

        if tool_name == 'run_itn_planning':
            # Normalise shorthand like "200k"
            for key in ('total_nets', 'avg_household_size'):
                value = normalized.get(key)
                if isinstance(value, str):
                    cleaned = value.replace(',', '').strip()
                    multiplier = 1
                    if cleaned.lower().endswith('k'):
                        multiplier = 1000
                        cleaned = cleaned[:-1]
                    elif cleaned.lower().endswith('m'):
                        multiplier = 1_000_000
                        cleaned = cleaned[:-1]
                    try:
                        number = float(cleaned)
                        normalized[key] = int(number * multiplier)
                    except ValueError:
                        pass

        return normalized

    def _execute_direct_tool(
        self,
        resolution,
        session_id: str,
        args: Dict[str, Any],
    ) -> Dict[str, Any]:
        tool_name = resolution.tool

        try:
            if tool_name in self.tools:
                result = self.tools[tool_name](session_id, **args)
            else:
                payload = json.dumps({**args, 'session_id': session_id})
                result = self.tool_runner.execute(tool_name, payload)
        except Exception as exc:
            logger.error(f"Error executing resolved tool {tool_name}: {exc}")
            return {
                'status': 'error',
                'response': f"I ran into an issue while executing {tool_name}: {exc}",
                'tools_used': [tool_name],
            }

        normalized = self._normalize_tool_result(tool_name, result)
        return normalized

    def _normalize_tool_result(self, tool_name: str, raw_result: Any) -> Dict[str, Any]:
        if isinstance(raw_result, dict):
            response_text = raw_result.get('response') or raw_result.get('message') or ''
            normalized = dict(raw_result)
            normalized['response'] = response_text
            normalized.setdefault('message', response_text)
            normalized.setdefault('status', 'success')
            normalized.setdefault('tools_used', [tool_name])
            return normalized

        response_text = str(raw_result or '')
        return {
            'status': 'success',
            'response': response_text,
            'message': response_text,
            'tools_used': [tool_name],
        }

    def _list_dataset_columns(self, session_id: str, page: int = 1, page_size: int = 15) -> Dict[str, Any]:
        """Return a concise list of dataset columns (no pagination)."""
        column_details: List[Dict[str, Any]] = []
        if self.memory:
            try:
                stored = self.memory.get_fact(session_id, 'dataset_schema_columns')
                if isinstance(stored, list):
                    column_details = stored
            except Exception:
                column_details = []

        if not column_details:
            try:
                context_snapshot = self._get_session_context(session_id)
                column_details = context_snapshot.get('schema_columns', []) if context_snapshot else []
            except Exception:
                column_details = []

        if not column_details:
            return {
                'response': 'I could not find any dataset columns yet. Please upload data or run the analysis first.',
                'status': 'error',
                'tools_used': ['list_dataset_columns']
            }

        total = len(column_details)
        lines = [f"Dataset columns ({total} total):"]
        for col in column_details:
            name = col.get('name', 'unknown')
            dtype = col.get('dtype', 'object')
            non_null = col.get('non_null', 'n/a')
            unique = col.get('unique', 'n/a')
            sample_values = col.get('sample_values') or []
            sample = ', '.join(sample_values) if sample_values else '–'
            lines.append(f"- **{name}** ({dtype}) — non-null: {non_null}, unique: {unique}, sample: {sample}")

        return {
            'response': "\n".join(lines),
            'status': 'success',
            'tools_used': ['list_dataset_columns']
        }

