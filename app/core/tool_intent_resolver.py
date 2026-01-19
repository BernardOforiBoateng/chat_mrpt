"""Centralized natural language → tool resolver for the main chat flow.

This module analyses user utterances, combines lightweight semantic
scoring with dataset context, and proposes concrete tool invocations when
confidence is sufficient. It replaces ad-hoc keyword checks with a
structured resolver that is aware of available tools, dataset schema, and
recent interaction history.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .tool_capabilities import TOOL_CAPABILITIES

try:
    # Shared fuzzy resolver for dataset columns
    from app.services.variable_resolution_service import variable_resolver
except Exception:  # pragma: no cover - service may be absent in some envs
    variable_resolver = None  # type: ignore


_TOKEN_PATTERN = re.compile(r"[a-z0-9_]+", re.IGNORECASE)


@dataclass
class ToolResolution:
    """Represents a proposed tool invocation."""

    tool: str
    score: float
    confidence: float
    reason: str
    matched_terms: Sequence[str]
    inferred_args: Dict[str, Any]
    requires_args: bool
    supports_choice_interpreter: bool = True


class ToolIntentResolver:
    """Resolve natural language requests into concrete tool invocations."""

    #: Mapping between registry/tool-runner function names and capability keys
    _CAPABILITY_MAP: Dict[str, str] = {
        "run_malaria_risk_analysis": "run_malaria_risk_analysis",
        "create_vulnerability_map": "create_vulnerability_map",
        "create_pca_map": "create_pca_map",
        "create_variable_distribution": "variable_distribution",
        "create_urban_extent_map": "createurbanextentmap",
        "create_decision_tree": "createdecisiontree",
        "create_composite_score_maps": "create_vulnerability_map_comparison",
        "create_composite_vulnerability_map": "create_vulnerability_map",
        "create_settlement_map": "create_settlement_map",
        "show_settlement_statistics": "show_settlement_statistics",
        "run_itn_planning": "plan_itn_distribution",
        "analyze_data_with_python": "execute_data_query",
        "list_dataset_columns": "describe_data",
    }

    _DEFAULT_THRESHOLD: float = 1.8

    def __init__(self, llm_manager: Any = None) -> None:
        self.llm_manager = llm_manager

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
    def resolve(
        self,
        message: str,
        session_context: Dict[str, Any],
        session_state: Optional[Dict[str, Any]] = None,
    ) -> Optional[ToolResolution]:
        """Return the most likely tool resolution or ``None``.

        Args:
            message: Raw user utterance.
            session_context: Context dictionary from SessionContextService.
            session_state: Mutable per-session scratchpad maintained by the
                interpreter (tracks recent tool usage/variables).
        """
        text = (message or "").strip()
        if not text:
            return None

        text_lower = text.lower()
        tokens = self._tokenise(text_lower)
        bigrams = self._build_bigrams(tokens)

        # Bail out early if this is clearly conversational/small-talk
        if self._looks_like_smalltalk(text_lower):
            return None

        candidates: List[ToolResolution] = []
        available_tools = set(self._CAPABILITY_MAP.keys())

        for tool_name in available_tools:
            capability_key = self._CAPABILITY_MAP[tool_name]
            capability = TOOL_CAPABILITIES.get(capability_key, {})
            base_score, matched_terms = self._score_with_capability(capability, text_lower, tokens, bigrams)

            extra_score, inferred_args, requires_args, extra_terms, supports_choice = self._apply_tool_specific_logic(
                tool_name,
                text_lower,
                tokens,
                bigrams,
                session_context,
                session_state or {},
            )

            total_score = base_score + extra_score
            if total_score <= 0:
                continue

            matched = list(dict.fromkeys(list(matched_terms) + list(extra_terms)))

            if not self._preconditions_met(tool_name, session_context):
                # Penalise heavily when prerequisites missing (e.g. no data uploaded)
                total_score *= 0.4

            confidence = self._score_to_confidence(total_score)
            reason = self._build_reason(tool_name, matched, total_score, inferred_args)

            candidates.append(
                ToolResolution(
                    tool=tool_name,
                    score=total_score,
                    confidence=confidence,
                    reason=reason,
                    matched_terms=matched,
                    inferred_args=inferred_args,
                    requires_args=requires_args,
                    supports_choice_interpreter=supports_choice,
                )
            )

        if not candidates:
            return None

        # Choose highest-scoring candidate
        best = max(candidates, key=lambda c: c.score)
        if best.score < self._DEFAULT_THRESHOLD:
            return None
        return best

    # ------------------------------------------------------------------
    # scoring helpers
    # ------------------------------------------------------------------
    def _score_with_capability(
        self,
        capability: Dict[str, Any],
        text: str,
        tokens: Iterable[str],
        bigrams: Iterable[str],
    ) -> Tuple[float, List[str]]:
        score = 0.0
        matched: List[str] = []

        execution_verbs = capability.get("execution_verbs") or []
        for verb in execution_verbs:
            if self._phrase_in_text(verb, text):
                score += 1.0
                matched.append(verb)

        # Reward textual overlap with example queries (lightweight semantic hint)
        example_queries = capability.get("example_queries") or []
        for example in example_queries:
            example_lower = example.lower()
            if self._phrase_in_text(example_lower, text):
                score += 1.2
                matched.append(example)
            else:
                # Partial overlap via bigrams
                for gram in self._build_bigrams(self._tokenise(example_lower)):
                    if gram in bigrams:
                        score += 0.4
                        matched.append(gram)
                        break

        return score, matched

    def _apply_tool_specific_logic(
        self,
        tool_name: str,
        text: str,
        tokens: Sequence[str],
        bigrams: Sequence[str],
        session_context: Dict[str, Any],
        session_state: Dict[str, Any],
    ) -> Tuple[float, Dict[str, Any], bool, List[str], bool]:
        """Return (score_bonus, inferred_args, requires_args, matched_terms, supports_choice)."""
        if tool_name == "create_variable_distribution":
            return self._handle_variable_distribution(text, tokens, session_context, session_state)
        if tool_name == "run_malaria_risk_analysis":
            return self._handle_risk_analysis(text, tokens, session_context)
        if tool_name == "create_vulnerability_map":
            return self._handle_vulnerability_map(text, tokens)
        if tool_name == "create_pca_map":
            return self._handle_pca_map(text, tokens)
        if tool_name == "create_composite_score_maps":
            return self._handle_composite_maps(text, tokens)
        if tool_name == "create_composite_vulnerability_map":
            return self._handle_composite_vulnerability(text, tokens)
        if tool_name == "create_decision_tree":
            return self._handle_decision_tree(text, tokens)
        if tool_name == "create_urban_extent_map":
            return self._handle_urban_extent(text, tokens)
        if tool_name == "create_settlement_map":
            return self._handle_settlement_map(text, tokens)
        if tool_name == "show_settlement_statistics":
            return self._handle_settlement_stats(text, tokens)
        if tool_name == "run_itn_planning":
            return self._handle_itn_planning(text, tokens)
        if tool_name == "analyze_data_with_python":
            return self._handle_data_queries(text, tokens)
        if tool_name == "list_dataset_columns":
            return self._handle_list_columns(text, tokens)

        # Default: no extra info
        return 0.0, {}, False, [], True

    # ------------------------------------------------------------------
    # per-tool handlers
    # ------------------------------------------------------------------
    def _handle_variable_distribution(
        self,
        text: str,
        tokens: Sequence[str],
        session_context: Dict[str, Any],
        session_state: Dict[str, Any],
    ) -> Tuple[float, Dict[str, Any], bool, List[str], bool]:
        keywords = {"map", "plot", "visualize", "distribution", "heatmap", "choropleth", "surface", "spatial"}
        matched = [word for word in keywords if word in tokens]
        score = 0.0
        if matched:
            score += 1.4
        if "distribution" in tokens:
            score += 0.6
        if "map" in tokens:
            score += 0.6

        # Guard against vulnerability/risk intents being misclassified as raw-variable requests
        conflict_terms = {"vulnerability", "vulnerable", "risk", "assessment", "compare", "comparison"}
        conflicting = sorted(conflict_terms.intersection(tokens))
        if conflicting:
            matched.extend(conflicting)
            # Strongly penalise so the resolver defers to vulnerability-specific tools
            return -2.5, {}, True, matched, False

        columns = session_context.get("columns") or []
        inferred_args: Dict[str, Any] = {}
        requires_args = True
        resolved_variable: Optional[str] = None
        additional_reason_terms: List[str] = []

        if variable_resolver and columns:
            resolution = variable_resolver.resolve_variable(
                text,
                columns,
                threshold=0.55,
                return_suggestions=True,
            )
            if resolution.get("matched"):
                resolved_variable = resolution["matched"]
                inferred_args = {"variable_name": resolved_variable}
                score += 1.6 * max(resolution.get("confidence", 0.6), 0.4)
                additional_reason_terms.append(resolved_variable)

        if not resolved_variable:
            # fall back to last variable the user saw (if pronoun referenced)
            last_var = (session_state or {}).get("last_variable_distribution")
            pronoun_trigger = {"it", "them", "those", "these", "this", "that"}
            if last_var and pronoun_trigger.intersection(tokens):
                inferred_args = {"variable_name": last_var}
                score += 0.8
                additional_reason_terms.append(f"context:{last_var}")
                resolved_variable = last_var

        if resolved_variable:
            requires_args = False

        return score, inferred_args, requires_args, matched + additional_reason_terms, False

    def _handle_risk_analysis(
        self,
        text: str,
        tokens: Sequence[str],
        session_context: Dict[str, Any],
    ) -> Tuple[float, Dict[str, Any], bool, List[str], bool]:
        matched = []
        if "risk" in tokens:
            matched.append("risk")
        if "analysis" in tokens or "assess" in tokens:
            matched.append("analysis")
        if "rank" in tokens and ("ward" in tokens or "wards" in tokens):
            matched.extend(["rank", "ward"])
        score = 1.0 * len(matched)

        # detect variable hints so we can seed args (optional)
        inferred_args: Dict[str, Any] = {}
        if variable_resolver and session_context.get("columns"):
            resolution = variable_resolver.resolve_variable(
                text,
                session_context["columns"],
                threshold=0.65,
                return_suggestions=True,
                allow_multiple=True,
            )
            variables = resolution.get("matched_variables") or []
            if variables:
                inferred_args["variables"] = variables
                score += 0.8
                matched.extend(variables)

        return score, inferred_args, False, matched, True

    def _handle_vulnerability_map(self, text: str, tokens: Sequence[str]) -> Tuple[float, Dict[str, Any], bool, List[str], bool]:
        matched = []
        if "vulnerability" in tokens:
            matched.append("vulnerability")
        if "map" in tokens or "choropleth" in tokens:
            matched.append("map")
        score = 0.9 * len(matched)

        comparison_terms = {"compare", "comparison", "both", "side", "versus", "vs"}
        if comparison_terms.intersection(tokens):
            matched.extend(sorted(comparison_terms.intersection(tokens)))
            score += 1.2

        # recognise method hints
        inferred_args: Dict[str, Any] = {}
        for method in ("composite", "pca", "both"):
            if method in tokens:
                inferred_args["method"] = method
                score += 0.5
                matched.append(method)
                break

        return score, inferred_args, False, matched, True

    def _handle_pca_map(self, text: str, tokens: Sequence[str]) -> Tuple[float, Dict[str, Any], bool, List[str], bool]:
        matched = []
        if "pca" in tokens or "principal" in tokens:
            matched.append("pca")
            score = 1.4
        else:
            score = 0.0
        if "map" in tokens:
            matched.append("map")
            score += 0.6
        return score, {}, False, matched, True

    def _handle_composite_maps(self, text: str, tokens: Sequence[str]) -> Tuple[float, Dict[str, Any], bool, List[str], bool]:
        matched = []
        score = 0.0
        if "composite" in tokens:
            matched.append("composite")
            score += 1.2
        if "map" in tokens or "breakdown" in tokens or "layers" in tokens:
            matched.append("map")
            score += 0.6
        return score, {}, False, matched, True

    def _handle_composite_vulnerability(self, text: str, tokens: Sequence[str]) -> Tuple[float, Dict[str, Any], bool, List[str], bool]:
        matched = []
        score = 0.0
        if "composite" in tokens:
            matched.append("composite")
            score += 1.0
        if "vulnerability" in tokens:
            matched.append("vulnerability")
            score += 1.0
        if "map" in tokens:
            matched.append("map")
            score += 0.6
        return score, {}, False, matched, True

    def _handle_decision_tree(self, text: str, tokens: Sequence[str]) -> Tuple[float, Dict[str, Any], bool, List[str], bool]:
        if "decision" in tokens and "tree" in tokens:
            return 2.2, {}, False, ["decision", "tree"], True
        return 0.0, {}, False, [], True

    def _handle_urban_extent(self, text: str, tokens: Sequence[str]) -> Tuple[float, Dict[str, Any], bool, List[str], bool]:
        matched = []
        score = 0.0
        if "urban" in tokens:
            matched.append("urban")
            score += 1.0
        if "extent" in tokens or "boundary" in tokens or "footprint" in tokens:
            matched.append("extent")
            score += 0.8
        if "map" in tokens:
            matched.append("map")
            score += 0.4
        return score, {}, False, matched, True

    def _handle_settlement_map(self, text: str, tokens: Sequence[str]) -> Tuple[float, Dict[str, Any], bool, List[str], bool]:
        matched = []
        if "settlement" in tokens or "settlements" in tokens:
            matched.append("settlement")
        if not matched:
            return 0.0, {}, False, [], True
        score = 1.2
        if "map" in tokens or "distribution" in tokens:
            matched.append("map")
            score += 0.6
        return score, {}, False, matched, True

    def _handle_settlement_stats(self, text: str, tokens: Sequence[str]) -> Tuple[float, Dict[str, Any], bool, List[str], bool]:
        if "settlement" in tokens and ("stats" in tokens or "statistics" in tokens or "numbers" in tokens or "counts" in tokens):
            return 1.8, {}, False, ["settlement", "statistics"], True
        return 0.0, {}, False, [], True

    def _handle_itn_planning(self, text: str, tokens: Sequence[str]) -> Tuple[float, Dict[str, Any], bool, List[str], bool]:
        matched = []
        score = 0.0
        trigger_words = {"itn", "bednet", "bed", "net", "nets", "mosquito"}
        if trigger_words.intersection(tokens):
            score += 1.4
            matched.append("itn")
        action_words = {"plan", "allocate", "distribution", "distribute", "deploy", "share"}
        if action_words.intersection(tokens):
            score += 1.0
            matched.append("plan")
        return score, {}, False, matched, True

    def _handle_data_queries(self, text: str, tokens: Sequence[str]) -> Tuple[float, Dict[str, Any], bool, List[str], bool]:
        # Broad catch-all for analytical requests (top N, correlations, summaries, etc.)
        ranking_words = {"top", "highest", "lowest", "rank", "sort", "order"}
        analysis_words = {"correlation", "trend", "summary", "statistics", "compare", "difference", "mean", "average"}
        matched = []
        score = 0.0
        if ranking_words.intersection(tokens):
            matched.append("ranking")
            score += 1.2
        if analysis_words.intersection(tokens):
            matched.append("analysis")
            score += 1.0
        if "python" in tokens or "code" in tokens:
            score += 0.5
            matched.append("python")
        return score, {"query": text}, False, matched, True

    def _handle_list_columns(self, text: str, tokens: Sequence[str]) -> Tuple[float, Dict[str, Any], bool, List[str], bool]:
        target_words = {"columns", "variables", "fields", "headers", "features", "schema"}
        question_words = {"what", "which", "show", "list", "available"}
        if target_words.intersection(tokens) and question_words.intersection(tokens):
            return 2.0, {}, False, list(target_words.intersection(tokens)), True
        return 0.0, {}, False, [], True

    # ------------------------------------------------------------------
    # misc helpers
    # ------------------------------------------------------------------
    def _preconditions_met(self, tool_name: str, session_context: Dict[str, Any]) -> bool:
        data_loaded = bool(session_context.get("data_loaded"))
        analysis_complete = bool(session_context.get("analysis_complete"))

        if tool_name in {"run_malaria_risk_analysis", "create_variable_distribution", "analyze_data_with_python", "list_dataset_columns", "run_itn_planning", "create_settlement_map", "show_settlement_statistics", "create_urban_extent_map"}:
            return data_loaded
        if tool_name in {"create_vulnerability_map", "create_pca_map", "create_composite_score_maps", "create_composite_vulnerability_map", "create_decision_tree"}:
            return analysis_complete
        return True

    def _score_to_confidence(self, score: float) -> float:
        if score <= 0:
            return 0.0
        # Asymptotic curve that approaches 0.95
        return max(0.0, min(0.95, 0.25 * score + 0.35))

    def _build_reason(self, tool_name: str, matched_terms: Iterable[str], score: float, inferred_args: Dict[str, Any]) -> str:
        terms_text = ", ".join(matched_terms) if matched_terms else "n/a"
        args_text = ", ".join(f"{k}={v}" for k, v in inferred_args.items()) if inferred_args else ""
        base = f"matched={terms_text}; score={score:.2f}"
        if args_text:
            base += f"; args={args_text}"
        return base

    def _looks_like_smalltalk(self, text: str) -> bool:
        smalltalk_phrases = [
            "thank", "thanks", "hello", "hi", "good morning", "good afternoon",
            "how are", "great", "awesome", "cool", "bye", "goodbye",
        ]
        return any(phrase in text for phrase in smalltalk_phrases)

    def _phrase_in_text(self, phrase: str, text: str) -> bool:
        phrase = phrase.strip().lower()
        if not phrase:
            return False
        if " " in phrase:
            return phrase in text
        return re.search(rf"\b{re.escape(phrase)}\b", text) is not None

    def _tokenise(self, text: str) -> List[str]:
        return _TOKEN_PATTERN.findall(text)

    def _build_bigrams(self, tokens: Sequence[str]) -> List[str]:
        return [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)] if len(tokens) >= 2 else []


__all__ = ["ToolIntentResolver", "ToolResolution"]
