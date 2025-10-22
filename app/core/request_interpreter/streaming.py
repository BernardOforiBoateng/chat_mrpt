"""Streaming utilities for RequestInterpreter."""

from __future__ import annotations

import json
import logging
import time
from typing import Dict, Any, Generator, Iterable

logger = logging.getLogger(__name__)


class StreamingMixin:
    """Provide SSE-style streaming helpers for tool-enabled conversations."""

    def process_message_streaming(
        self,
        user_message: str,
        session_id: str,
        session_data: Dict[str, Any] | None = None,
        **kwargs,
    ) -> Iterable[Dict[str, Any]]:
        """Stream assistant responses chunk by chunk."""

        session_context = self._get_session_context(session_id, session_data)
        session_context = self._enrich_session_context_with_memory(session_id, session_context)

        system_prompt = self._build_system_prompt_refactored(session_context, session_id)

        function_schemas = None
        if self.tool_runner:
            try:
                function_schemas = self.tool_runner.get_function_schemas()
            except Exception as exc:  # pragma: no cover
                logger.warning(f"Failed to fetch tool schemas: {exc}")

        if self.orchestrator and function_schemas:
            stream = self.orchestrator.stream_with_tools(
                self.llm_manager,
                system_prompt,
                user_message,
                function_schemas,
                session_id,
                self.tool_runner,
                interpretation_cb=lambda raw, msg: self._interpret_raw_output(raw, msg, session_context, session_id),
            )
            yield from stream
            return

        yield from self._stream_with_tools(user_message, session_context, session_id, system_prompt)

    def _llm_with_tools(
        self,
        user_message: str,
        session_context: Dict[str, Any],
        session_id: str,
    ) -> Dict[str, Any]:
        """Fallback synchronous implementation when orchestrator is unavailable."""

        try:
            response = self.llm_manager.generate_with_tools(
                prompt=user_message,
                system_prompt=self._build_system_prompt_refactored(session_context, session_id),
                tools=self.tool_runner.get_function_schemas() if self.tool_runner else None,
                session_id=session_id,
            )
        except Exception as exc:  # pragma: no cover
            logger.error(f"LLM tool call failed: {exc}")
            return {
                'status': 'error',
                'response': f'I encountered an error while processing your request: {exc}',
                'tools_used': [],
            }

        return self._process_llm_response(response, session_id, session_context)

    def _stream_with_tools(
        self,
        user_message: str,
        session_context: Dict[str, Any],
        session_id: str,
        system_prompt: str,
    ) -> Generator[Dict[str, Any], None, None]:
        """Stream responses using legacy tool runner path."""

        accumulated_content: list[str] = []
        chunks = self.llm_manager.stream_with_tools(
            prompt=user_message,
            system_prompt=system_prompt,
            tools=self.tool_runner.get_function_schemas() if self.tool_runner else None,
            session_id=session_id,
        )

        for chunk in chunks:
            if not chunk:
                continue

            if chunk.get('type') == 'function_call':
                function_name = chunk['function_call']['name']

                if self.tool_runner:
                    result = self.tool_runner.execute(function_name, chunk['function_call']['arguments'])
                    normalized = self._normalize_tool_result(function_name, result)
                    content = normalized.get('response', '')
                    yield {'content': content, 'status': normalized.get('status', 'success'), 'tools_used': normalized.get('tools_used', [function_name]), 'done': False}
                    continue

                if function_name in self.tools:
                    args_str = chunk['function_call']['arguments'] or '{}'
                    args = json.loads(args_str) if args_str.strip() else {}
                    args['session_id'] = session_id
                    result = self.tools[function_name](**args)
                    normalized = self._normalize_tool_result(function_name, result)
                    yield {'content': normalized.get('response', ''), 'status': normalized.get('status', 'success'), 'tools_used': normalized.get('tools_used', [function_name]), 'done': False}
                    continue

                logger.error(f"Unknown function requested: {function_name}")
                yield {'content': f"I don't have access to the function '{function_name}'.", 'status': 'error', 'done': True}
                return

            content = chunk.get('content', '')
            if content:
                accumulated_content.append(content)
                yield {'content': content, 'status': 'success', 'done': False}
            elif chunk.get('done'):
                final_response = ''.join(accumulated_content)
                self._store_conversation(session_id, user_message, final_response)
                yield {'content': final_response, 'status': 'success', 'done': True}
                return

    def _process_llm_response(
        self,
        response: Dict[str, Any],
        session_id: str,
        session_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Normalize synchronous tool responses."""

        tool_calls = response.get('tool_calls') or []
        if not tool_calls:
            text = response.get('response') or ''
            self._store_conversation(session_id, response.get('prompt', ''), text)
            return {'status': 'success', 'response': text, 'tools_used': []}

        for call in tool_calls:
            function_name = call.get('name')
            args = call.get('arguments') or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:  # pragma: no cover
                    args = {}
            args['session_id'] = session_id

            if function_name in self.tools:
                result = self.tools[function_name](**args)
            elif self.tool_runner:
                payload = json.dumps(args)
                result = self.tool_runner.execute(function_name, payload)
            else:
                continue

            normalized = self._normalize_tool_result(function_name, result)
            self._store_conversation(session_id, call.get('prompt', ''), normalized.get('response', ''))
            return normalized

        return {
            'status': 'error',
            'response': 'I attempted to execute a tool but could not complete the request.',
            'tools_used': [],
        }

    # ------------------------------------------------------------------
    # Interpretation helpers
    # ------------------------------------------------------------------
    def _interpret_raw_output(
        self,
        raw_output: str,
        user_message: str,
        session_context: Dict[str, Any],
        session_id: str,
    ) -> str:
        """Optional hook for generating human-friendly explanations."""
        return ''

__all__ = ['StreamingMixin']
