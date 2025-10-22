"""Shared helpers for Arena streaming and preview responses."""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict

from flask import Response, current_app

logger = logging.getLogger(__name__)


class ArenaSetupError(RuntimeError):
    """Raised when Arena preloading fails for the current request."""


def _ensure_arena_manager():
    """Return the shared Arena manager, initialising it if needed."""
    from app.web.routes.arena_routes import (  # deferred import to avoid cycles
        arena_manager as _shared_arena_manager,
        init_arena_system as _init_arena,
    )

    if _shared_arena_manager is None:
        _init_arena(current_app)
    return _shared_arena_manager


@dataclass
class ArenaPreload:
    """Container describing a preloaded Arena battle."""

    manager: Any
    battle: Any
    battle_id: str
    model_a: str
    model_b: str
    responses: Dict[str, str]
    latencies: Dict[str, float]

    _TOOL_NEED_INDICATORS = [
        "i need to see",
        "upload",
        "provide the",
        "i would need",
        "cannot analyze without",
        "don't have access",
        "no data available",
        "please share",
        "i require",
        "unable to access",
        "can't see your",
    ]

    def both_models_need_tools(self) -> bool:
        """Return True when both Arena responses request access to tools/data."""
        response_a = (self.responses.get("a") or "").lower()
        response_b = (self.responses.get("b") or "").lower()
        needs_a = any(indicator in response_a for indicator in self._TOOL_NEED_INDICATORS)
        needs_b = any(indicator in response_b for indicator in self._TOOL_NEED_INDICATORS)
        return needs_a and needs_b

    def ensure_current_pair(self) -> None:
        """Persist the current model pair on the battle record."""
        if self.battle is None:
            return
        self.battle.current_pair = (self.model_a, self.model_b)
        self.manager.storage.update_progressive_battle(self.battle)

    def build_preview_payload(self) -> Dict[str, Any]:
        """Return a JSON payload for non-streaming Arena previews."""
        return {
            "status": "success",
            "arena_mode": True,
            "battle_id": self.battle_id,
            "response_a": self.responses.get("a", ""),
            "response_b": self.responses.get("b", ""),
            "model_a": self.model_a,
            "model_b": self.model_b,
            "round": 1,
            "total_rounds": 3,
        }

    def stream_response(self) -> Response:
        """Return an SSE response that streams the current Arena battle."""
        self.ensure_current_pair()

        def format_response(text: str) -> str:
            content = (text or "").replace("\r\n", "\n").replace("\r", "\n")
            content = re.sub(r"^(\s*)\*\s+", r"\1- ", content, flags=re.MULTILINE)
            content = re.sub(r"^(\s*)[\u2022•]\s+", r"\1- ", content, flags=re.MULTILINE)
            content = re.sub(r"^•\s*", "- ", content, flags=re.MULTILINE)
            content = re.sub(r"^-\s+", "- ", content, flags=re.MULTILINE)
            content = re.sub(r"\n{3,}", "\n\n", content)
            return content

        response_a_fmt = format_response(self.responses.get("a", ""))
        response_b_fmt = format_response(self.responses.get("b", ""))

        def generate():
            logger.info("\u26a0\ufe0f ARENA: Initializing battle %s: %s vs %s", self.battle_id, self.model_a, self.model_b)

            init_payload = {
                "arena_mode": True,
                "battle_id": self.battle_id,
                "round": 1,
                "model_a": self.model_a,
                "model_b": self.model_b,
                "response_a": response_a_fmt,
                "response_b": response_b_fmt,
                "done": False,
                "stream": True,
            }
            yield json.dumps(init_payload)

            chunk_size = 60
            a_idx = 0
            b_idx = 0
            while a_idx < len(response_a_fmt) or b_idx < len(response_b_fmt):
                if a_idx < len(response_a_fmt):
                    a_chunk = response_a_fmt[a_idx : a_idx + chunk_size]
                    a_idx += len(a_chunk)
                    yield json.dumps(
                        {
                            "arena_mode": True,
                            "battle_id": self.battle_id,
                            "stream": True,
                            "side": "a",
                            "delta": a_chunk,
                            "done": False,
                        }
                    )
                    time.sleep(0.08)

                if b_idx < len(response_b_fmt):
                    b_chunk = response_b_fmt[b_idx : b_idx + chunk_size]
                    b_idx += len(b_chunk)
                    yield json.dumps(
                        {
                            "arena_mode": True,
                            "battle_id": self.battle_id,
                            "stream": True,
                            "side": "b",
                            "delta": b_chunk,
                            "done": False,
                        }
                    )
                    time.sleep(0.08)

            final_payload = {
                "arena_mode": True,
                "battle_id": self.battle_id,
                "round": 1,
                "arena_complete": True,
                "latency_a": self.latencies.get("a", 0),
                "latency_b": self.latencies.get("b", 0),
                "remaining_models": self.battle.remaining_models[2:] if len(self.battle.remaining_models) > 2 else [],
                "eliminated_models": [],
                "winner_chain": [],
                "response_a": response_a_fmt,
                "response_b": response_b_fmt,
                "responses_ready": True,
                "done": True,
            }
            logger.info("\u2705 ARENA: Streaming complete for battle %s", self.battle_id)
            yield json.dumps(final_payload)

        response = Response((f"data: {chunk}\n\n" for chunk in generate()), mimetype="text/event-stream")
        response.headers["Cache-Control"] = "no-cache"
        response.headers["Connection"] = "keep-alive"
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response


def prepare_arena_preload(
    session_id: str,
    user_message: str,
    run_async: Callable[[Any], Any],
    *,
    num_models: int = 4,
) -> ArenaPreload:
    """Preload Arena responses for a given message.

    Raises:
        ArenaSetupError: when the Arena system cannot provide preloaded responses.
    """

    manager = _ensure_arena_manager()

    try:
        battle_info = run_async(
            manager.start_progressive_battle(
                user_message,
                num_models=num_models,
                session_id=session_id,
            )
        )
    except Exception as exc:  # pragma: no cover - defensive
        raise ArenaSetupError(f"Error initialising Arena battle: {exc}") from exc

    battle_id = battle_info.get("battle_id")
    if not battle_id:
        raise ArenaSetupError("Arena did not return a battle identifier")

    try:
        all_responses = run_async(manager.get_all_model_responses(battle_id))
    except Exception as exc:  # pragma: no cover - defensive
        raise ArenaSetupError(f"Error loading Arena responses: {exc}") from exc

    error_message = all_responses.get("error") if isinstance(all_responses, dict) else None
    if error_message:
        raise ArenaSetupError(error_message)

    battle = manager.storage.get_progressive_battle(battle_id)
    if not battle:
        raise ArenaSetupError("Arena battle could not be found after preload")

    model_a = all_responses.get("model_a") if isinstance(all_responses, dict) else None
    model_b = all_responses.get("model_b") if isinstance(all_responses, dict) else None

    if not model_a and battle.all_models:
        model_a = battle.all_models[0]
    if not model_b and len(battle.all_models) > 1:
        model_b = battle.all_models[1]

    if not model_a or not model_b:
        raise ArenaSetupError("Arena did not provide model identifiers")

    responses = {
        "a": battle.all_responses.get(model_a, ""),
        "b": battle.all_responses.get(model_b, ""),
    }
    latencies = {
        "a": battle.all_latencies.get(model_a, 0),
        "b": battle.all_latencies.get(model_b, 0),
    }

    return ArenaPreload(
        manager=manager,
        battle=battle,
        battle_id=battle_id,
        model_a=model_a,
        model_b=model_b,
        responses=responses,
        latencies=latencies,
    )


__all__ = [
    "ArenaPreload",
    "ArenaSetupError",
    "prepare_arena_preload",
]
