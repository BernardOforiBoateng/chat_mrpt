"""Tool registration and resolution helpers for RequestInterpreter."""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class ToolingMixin:
    """Provide tool registration and intent-resolution helpers."""

    def _register_tools(self) -> None:
        """Register actual Python functions as tools - true py-sidebot style."""
        logger.info("Registering tools - py-sidebot pattern")

        # Analysis
        self.tools['run_malaria_risk_analysis'] = self._run_malaria_risk_analysis
        # self.tools['run_composite_analysis'] = self._run_composite_analysis  # intentionally disabled
        # self.tools['run_pca_analysis'] = self._run_pca_analysis

        # Visualization
        self.tools['create_vulnerability_map'] = self._create_vulnerability_map
        # self.tools['create_box_plot'] = self._create_box_plot  # replaced by analyze_data_with_python
        self.tools['create_pca_map'] = self._create_pca_map
        self.tools['create_variable_distribution'] = self._create_variable_distribution
        self.tools['create_urban_extent_map'] = self._create_urban_extent_map
        self.tools['create_decision_tree'] = self._create_decision_tree
        self.tools['create_composite_score_maps'] = self._create_composite_score_maps

        # Settlement tools
        self.tools['create_settlement_map'] = self._create_settlement_map
        self.tools['show_settlement_statistics'] = self._show_settlement_statistics

        # Explanation / planning
        self.tools['explain_analysis_methodology'] = self._explain_analysis_methodology
        self.tools['run_itn_planning'] = self._run_itn_planning

        # Python execution tool (replaces many legacy helpers)
        self.tools['analyze_data_with_python'] = self._analyze_data_with_python

        # Dataset exploration
        self.tools['list_dataset_columns'] = self._list_dataset_columns

        logger.info(
            "Registered %d tools (legacy redundant tools handled by analyze_data_with_python)",
            len(self.tools),
        )

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
            except Exception as exc:  # pragma: no cover - defensive logging
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

    def _get_tool_parameters(self, tool_name: str) -> Dict[str, Any]:
        base_params = {
            'type': 'object',
            'properties': {
                'session_id': {'type': 'string', 'description': 'Session identifier'},
            },
            'required': ['session_id'],
        }

        if 'analysis' in tool_name:
            base_params['properties']['variables'] = {
                'type': 'array',
                'items': {'type': 'string'},
                'description': 'Optional custom variables for analysis. When specified, these will override automatic region-based selection.',
            }

        if 'map' in tool_name or 'plot' in tool_name:
            if tool_name == 'create_vulnerability_map':
                base_params['properties']['method'] = {
                    'type': 'string',
                    'enum': ['composite', 'pca'],
                    'description': 'Analysis method to visualize. If not specified, shows side-by-side comparison of both methods.',
                }
            else:
                base_params['properties']['method'] = {
                    'type': 'string',
                    'enum': ['composite', 'pca'],
                    'description': 'Analysis method to visualize',
                }

        if tool_name == 'execute_data_query':
            base_params['properties'].update({
                'query': {'type': 'string', 'description': 'Natural language query about the data'},
                'code': {'type': 'string', 'description': 'Optional Python code to execute'},
            })
            base_params['required'].append('query')

        if tool_name == 'execute_sql_query':
            base_params['properties'].update({
                'query': {
                    'type': 'string',
                    'description': 'SQL query to execute on the dataframe (table named df).',
                }
            })
            base_params['required'].append('query')

        if tool_name == 'explain_analysis_methodology':
            base_params['properties']['method'] = {
                'type': 'string',
                'enum': ['composite', 'pca', 'both'],
                'description': 'Which methodology to explain',
            }

        if tool_name == 'create_variable_distribution':
            base_params['properties']['variable_name'] = {
                'type': 'string',
                'description': 'Exact column name from the dataset to visualize (required).',
            }
            base_params['required'].append('variable_name')

        if tool_name == 'create_settlement_map':
            base_params['properties'].update({
                'ward_name': {
                    'type': 'string',
                    'description': 'Optional specific ward name to highlight and focus on',
                },
                'zoom_level': {
                    'type': 'integer',
                    'description': 'Map zoom level (11=city, 13=ward, 15=detailed)',
                    'default': 11,
                },
            })

        if tool_name == 'run_itn_planning':
            base_params['properties'].update({
                'total_nets': {
                    'type': 'integer',
                    'description': 'Total number of bed nets available for distribution (e.g., 50000, 100000)',
                },
                'avg_household_size': {
                    'type': 'number',
                    'description': 'Average household size in the area (default: 5.0)',
                },
                'urban_threshold': {
                    'type': 'number',
                    'description': 'Urban percentage threshold for prioritization (default: 30.0)',
                },
                'method': {
                    'type': 'string',
                    'enum': ['composite', 'pca'],
                    'description': 'Ranking method to use (default: composite)',
                },
            })

        if tool_name == 'list_dataset_columns':
            base_params['properties'].update({
                'page': {
                    'type': 'integer',
                    'description': 'Page number to display (1-indexed)',
                    'default': 1,
                },
                'page_size': {
                    'type': 'integer',
                    'description': 'Number of columns per page (default 15)',
                    'default': 15,
                },
            })

        return base_params

__all__ = ['ToolingMixin']
