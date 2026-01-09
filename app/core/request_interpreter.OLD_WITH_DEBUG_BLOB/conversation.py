"""Conversation history and memory helpers for the request interpreter."""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from flask import session

logger = logging.getLogger(__name__)

class ConversationMixin:
    def _store_conversation(self, session_id: str, user_message: str, assistant_response: str = "") -> None:
        """Persist conversation turns to in-memory cache and optional MemoryService."""
        if not session_id:
            return

        # Update lightweight in-memory cache for quick lookups
        history = self.conversation_history.setdefault(session_id, [])
        if user_message:
            history.append({"role": "user", "content": user_message})
        if assistant_response:
            history.append({"role": "assistant", "content": assistant_response})
        if len(history) > 40:
            self.conversation_history[session_id] = history[-40:]

        if not self.memory:
            return

        try:
            last_messages = self.memory.get_messages(session_id)
            last_role = last_messages[-1]['role'] if last_messages else None
            last_content = last_messages[-1]['content'] if last_messages else None
            if user_message:
                if not (last_role == 'user' and (last_content or '') == user_message):
                    self.memory.append_message(session_id, "user", user_message)
            if assistant_response:
                last_messages = self.memory.get_messages(session_id)
                last_role = last_messages[-1]['role'] if last_messages else None
                last_content = last_messages[-1]['content'] if last_messages else None
                if not (last_role == 'assistant' and (last_content or '') == assistant_response):
                    self.memory.append_message(session_id, "assistant", assistant_response)
            self._ensure_memory_summary(session_id)
        except Exception as exc:
            logger.warning(f"Memory append failed for session {session_id}: {exc}")

    def _ensure_memory_summary(self, session_id: str) -> None:
        """Use LLM to maintain a compact memory summary after new messages."""
        if not self.memory or not self.llm_manager:
            return

        tracker = self._memory_summary_tracker.get(session_id, {})
        last_count = tracker.get('count', 0)
        last_ts = tracker.get('ts', 0.0)

        try:
            messages = self.memory.get_messages(session_id)
        except Exception as exc:
            logger.warning(f"Could not read memory messages for {session_id}: {exc}")
            return

        if not messages:
            return

        # Avoid excessive summarisation: require at least 2 new messages or 60s elapsed
        if len(messages) - last_count < 2 and (time.time() - last_ts) < 60:
            return

        transcript = []
        for msg in messages[-8:]:
            role = (msg.get('role') or 'user').upper()
            content = (msg.get('content') or '').strip()
            if not content:
                continue
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
            summary_text = self.llm_manager.generate_response(
                prompt=f"Conversation transcript:\n{summary_prompt}\n\nProvide bullet points:",
                system_message=system_message,
                temperature=0.2,
                max_tokens=200,
                session_id=session_id
            )
        except Exception as exc:
            logger.warning(f"Memory summary generation failed for {session_id}: {exc}")
            return

        if not summary_text or summary_text.lower().startswith("error"):
            return

        summary_trimmed = summary_text.strip()
        if len(summary_trimmed) > 800:
            summary_trimmed = summary_trimmed[:800]

        try:
            self.memory.set_fact(session_id, 'conversation_summary', summary_trimmed)
            tracker.update({'count': len(messages), 'ts': time.time()})
            self._memory_summary_tracker[session_id] = tracker
        except Exception as exc:
            logger.warning(f"Failed to persist memory summary for {session_id}: {exc}")

    def _enrich_session_context_with_memory(self, session_id: str, session_context: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(session_context, dict):
            return session_context

        if not self.memory:
            return session_context

        enriched = dict(session_context)

        try:
            summary = self.memory.get_fact(session_id, 'conversation_summary')
            if summary:
                enriched['memory_summary'] = summary

            messages = self.memory.get_messages(session_id)
            if messages:
                recent = []
                for msg in messages[-4:]:
                    role = (msg.get('role') or 'user').title()
                    content = (msg.get('content') or '').strip()
                    if content:
                        recent.append(f"{role}: {content}")
                if recent:
                    enriched['recent_conversation'] = "\n".join(recent)
        except Exception as exc:
            logger.warning(f"Failed to enrich session context with memory for {session_id}: {exc}")

        return enriched

