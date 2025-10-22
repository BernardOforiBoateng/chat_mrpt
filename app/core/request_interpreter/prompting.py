"""Prompt building helpers for RequestInterpreter."""

from __future__ import annotations

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class PromptMixin:
    """Expose thin wrapper around PromptBuilder with safe fallback."""

    def _build_system_prompt_refactored(self, session_context: Dict[str, Any], session_id: str | None = None) -> str:
        try:
            if hasattr(self, 'prompt_builder') and self.prompt_builder is not None:
                scoped = dict(session_context) if isinstance(session_context, dict) else session_context
                if session_id and isinstance(scoped, dict):
                    scoped.setdefault('session_id', session_id)
                return self.prompt_builder.build(scoped, session_id)
        except Exception as exc:  # pragma: no cover - logging only
            logger.warning(f"PromptBuilder failed, falling back to minimal prompt: {exc}")

        return (
            "You are ChatMRPT, an AI assistant for malaria risk analysis. "
            "Be accurate, concise, and action-oriented."
        )

__all__ = ['PromptMixin']
