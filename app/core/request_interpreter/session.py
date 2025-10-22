"""Session and memory helpers for RequestInterpreter."""

from __future__ import annotations

import logging
import math
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SessionMixin:
    """Provide conversation storage and session context helpers."""

    def _store_conversation(self, session_id: str, user_message: str, assistant_response: str = "") -> None:
        """Persist conversation turns to in-memory cache and optional memory service."""
        if not session_id:
            return

        history = self.conversation_history.setdefault(session_id, [])
        if user_message:
            history.append({"role": "user", "content": user_message})
        if assistant_response:
            history.append({"role": "assistant", "content": assistant_response})
        if len(history) > 40:
            self.conversation_history[session_id] = history[-40:]

        if not getattr(self, "memory", None):
            return

        try:
            memory = self.memory
            last_messages = memory.get_messages(session_id)
            last_role = last_messages[-1]['role'] if last_messages else None
            last_content = last_messages[-1]['content'] if last_messages else None

            if user_message and not (last_role == 'user' and (last_content or '') == user_message):
                memory.append_message(session_id, "user", user_message)

            if assistant_response:
                last_messages = memory.get_messages(session_id)
                last_role = last_messages[-1]['role'] if last_messages else None
                last_content = last_messages[-1]['content'] if last_messages else None
                if not (last_role == 'assistant' and (last_content or '') == assistant_response):
                    memory.append_message(session_id, "assistant", assistant_response)

            self._ensure_memory_summary(session_id)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(f"Memory append failed for session {session_id}: {exc}")

    def _ensure_memory_summary(self, session_id: str) -> None:
        """Maintain a concise LLM-generated summary for the session."""
        memory = getattr(self, "memory", None)
        llm_manager = getattr(self, "llm_manager", None)
        if not memory or not llm_manager:
            return

        tracker = self._memory_summary_tracker.get(session_id, {})
        last_count = tracker.get('count', 0)
        last_ts = tracker.get('ts', 0.0)

        try:
            messages = memory.get_messages(session_id)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(f"Could not read memory messages for {session_id}: {exc}")
            return

        if not messages:
            return

        if len(messages) - last_count < 2 and (time.time() - last_ts) < 60:
            return

        transcript: List[str] = []
        for msg in messages[-8:]:
            role = (msg.get('role') or 'user').upper()
            content = (msg.get('content') or '').strip()
            if content:
                transcript.append(f"{role}: {content}")

        if not transcript:
            return

        summary_prompt = "\n".join(transcript)
        system_message = (
            "You maintain a concise memory for an AI malaria analysis assistant. "
            "Summarise the key facts, data selections, results, outstanding questions, "
            "and user goals from the conversation transcript below. "
            "Limit to 5 short bullet points (<= 120 words total)."
        )

        try:
            summary_text = llm_manager.generate_response(
                prompt=f"Conversation transcript:\n{summary_prompt}\n\nProvide bullet points:",
                system_message=system_message,
                temperature=0.2,
                max_tokens=200,
                session_id=session_id,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(f"Memory summary generation failed for {session_id}: {exc}")
            return

        if not summary_text or summary_text.lower().startswith("error"):
            return

        summary_trimmed = summary_text.strip()
        if len(summary_trimmed) > 800:
            summary_trimmed = summary_trimmed[:800]

        try:
            memory.set_fact(session_id, 'conversation_summary', summary_trimmed)
            tracker.update({'count': len(messages), 'ts': time.time()})
            self._memory_summary_tracker[session_id] = tracker
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(f"Failed to persist memory summary for {session_id}: {exc}")

    def _enrich_session_context_with_memory(self, session_id: str, session_context: Dict[str, Any]) -> Dict[str, Any]:
        """Augment session context with stored memory artefacts."""
        if not isinstance(session_context, dict):
            return session_context

        memory = getattr(self, "memory", None)
        if not memory:
            return session_context

        enriched = dict(session_context)

        try:
            summary = memory.get_fact(session_id, 'conversation_summary')
            if summary:
                enriched['memory_summary'] = summary

            messages = memory.get_messages(session_id)
            if messages:
                recent: List[str] = []
                for msg in messages[-4:]:
                    role = (msg.get('role') or 'user').title()
                    content = (msg.get('content') or '').strip()
                    if content:
                        recent.append(f"{role}: {content}")
                if recent:
                    enriched['recent_conversation'] = "\n".join(recent)
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning(f"Failed to enrich session context with memory for {session_id}: {exc}")

        return enriched

    def _list_dataset_columns(self, session_id: str, page: int = 1, page_size: int = 15) -> Dict[str, Any]:
        """Provide a clean paginated summary of dataset columns for the LLM."""
        if page_size <= 0:
            page_size = 15
        if page <= 0:
            page = 1

        column_details: List[Dict[str, Any]] = []
        memory = getattr(self, "memory", None)
        if memory:
            try:
                stored = memory.get_fact(session_id, 'dataset_schema_columns')
                if isinstance(stored, list):
                    column_details = stored
            except Exception:  # pragma: no cover - defensive logging
                column_details = []

        if not column_details:
            try:
                context_snapshot = self._get_session_context(session_id)
                column_details = context_snapshot.get('schema_columns', []) if context_snapshot else []
            except Exception:  # pragma: no cover - defensive logging
                column_details = []

        if not column_details:
            return {
                'response': 'I could not find any dataset columns yet. Please upload data or run the analysis first.',
                'status': 'error',
                'tools_used': ['list_dataset_columns'],
            }

        total = len(column_details)
        total_pages = max(1, math.ceil(total / page_size))
        page = min(page, total_pages)
        start = (page - 1) * page_size
        end = start + page_size
        chunk = column_details[start:end]

        lines = [f"Dataset columns (page {page}/{total_pages}, {total} total):"]
        for col in chunk:
            name = col.get('name', 'unknown')
            dtype = col.get('dtype', 'object')
            non_null = col.get('non_null', 'n/a')
            unique = col.get('unique', 'n/a')
            sample_values = col.get('sample_values') or []
            sample = ', '.join(sample_values) if sample_values else '–'
            lines.append(f"• {name} [{dtype}] – non-null: {non_null}, unique: {unique}, sample: {sample}")

        if page < total_pages:
            lines.append(f"\nTo see more columns, call list_dataset_columns with page={page + 1}.")

        return {
            'response': "\n".join(lines),
            'status': 'success',
            'tools_used': ['list_dataset_columns'],
        }

__all__ = ['SessionMixin']
