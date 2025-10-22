# Universal Natural-Language Choices & Phase B Safety — Implementation Summary

This document summarizes what was implemented to enable natural-language choices everywhere in ChatMRPT and to harden analyze-data execution (Phase B), plus related observability and cleanup.

## Outcomes
- Universal, LLM-first argument interpreter across flows (TPR, Risk, ITN, Maps, Analyze-data hints).
- Clarifiers for low-confidence input with concise, one-turn prompts and UI-friendly chips.
- Central schemas for tool arguments; no scattered keyword/synonym parsing.
- Safer analyze-data execution (timeouts, restricted imports) with helper utilities.
- Memory persistence across turns/workers (file with optional Redis) used by router/agent.
- Observability extended with `choice_event`, plus `router_event` and `tool_event` coverage.
- Removed redundant TPR fuzzy/keyword parsing.

## Key Changes (by file)
- app/core/choice_interpreter.py
  - New LLM-first Universal Arg Interpreter. Resolves free-text into `{tool, args, confidence, reason}` with small fallback helpers.
  - Numeric coercion (e.g., `200k` ? `200000`).

- app/core/tool_schema_registry.py
  - New centralized schemas for tool args (ITN, vulnerability map, variable map, risk, analyze-data hints, TPR facility/age).

- app/core/request_interpreter.py
  - Universal integration points for analyze-data, risk, ITN, map variable/method (calls ChoiceInterpreter when `CHATMRPT_CHOICE_RESOLVER=1`).
  - Clarifiers for low-confidence/missing: ITN `total_nets`, map method, map variable (columns hints from session context).
  - Emits `[ROUTER_OBS] choice_event` with `{tool, args, confidence, matched_by, user_text}`.

- app/data_analysis_v3/core/tpr_workflow_langgraph_tool.py
  - Facility level and age group now resolved LLM-first; concise clarifier on low confidence.
  - Removed legacy fuzzy/keyword parsing methods and fallbacks.
  - Emits `[ROUTER_OBS] choice_event` for TPR selections.

- app/data_analysis_v3/core/agent.py
  - Accepts normalized args (hints) in `workflow_context` for analyze-data so generated code follows user intent without exact keywords.

- app/data_analysis_v3/core/executor.py
  - Phase B hardening: subprocess timeouts via `CHATMRPT_ANALYZE_TIMEOUT_MS`, restricted imports (allowlist), safe builtins, injected helpers `top_n`, `ensure_numeric`, `suggest_columns`.

- app/data_analysis_v3/tools/python_tool.py
  - ColumnResolver injection `(df_norm, resolve_col)` and output validation/sanitization.

- app/services/memory_service.py
  - File-based memory with optional Redis (`CHATMRPT_USE_REDIS_MEMORY=1`), compact summaries for router/agent.

- docs/UNIVERSAL_CHOICE_INTERPRETER_PLAN.md
  - Design document for the universal interpreter: objectives, architecture, prompts/schema, observability, rollout, success metrics.

- docs/ROUTER_OBSERVABILITY_AND_FLAGS.md
  - Added `choice_event` format and `CHATMRPT_CHOICE_RESOLVER` flag.

- tests/CHOICE_INTERPRETER_PARAPHRASE_TESTS.md
  - Manual canary paraphrase tests for TPR, ITN, vulnerability/variable maps, risk, analyze-data hints.

## Feature Flags
- `CHATMRPT_CHOICE_RESOLVER=1`
  - Enables universal LLM-based argument interpreter; emits `choice_event`.
- `CHATMRPT_INTENT_ROUTER=1`
  - LLM-first router & gates.
- `CHATMRPT_ROUTER_OBS=1`
  - Emit structured observability logs.
- `CHATMRPT_ANALYZE_TIMEOUT_MS=25000`
  - Analyze-data safety timeout (ms).
- `CHATMRPT_USE_REDIS_MEMORY=1` (optional)
  - Persist conversation memory in Redis; file fallback.

## Observability
- `router_event` — classification intent/action/gates/latency.
- `tool_event` — tool execution latency/errors.
- `choice_event` — universal argument resolution: `{tool, args, confidence, matched_by, user_text}`.

## Safety Hardening (Phase B)
- Analyze-data executes in a sandbox subprocess with timeouts and restricted imports.
- No OS/network/subprocess access; safe builtins only.
- ColumnResolver and helpers reduce KeyErrors and typo friction.
- Output validator and sanitization reduce hallucinations and bad values.

## Memory & Coherence
- File or Redis-backed message history across turns/workers.
- Router and agent receive compact summaries and normalized args (hints) for coherence.

## Cleanup / Deletions
- Removed legacy fuzzy/keyword parsing for TPR facility/age, replaced by choice interpreter + clarifiers.
- Avoided duplicating keyword logic elsewhere; interpreter is the source of truth.

## Canary & Validation
- Enable flags on one instance: `CHOICE_RESOLVER=1`, `INTENT_ROUTER=1`, `ROUTER_OBS=1`.
- Replay `tests/CHOICE_INTERPRETER_PARAPHRASE_TESTS.md`.
- Targets:
  - Choice accuracy = 95%
  - Clarify rate = 10%
  - Latency within budget
- Monitor `[ROUTER_OBS] choice_event`, `tool_event`, `router_event`.

## Rollback Plan
- Set `CHATMRPT_CHOICE_RESOLVER=0` to return to legacy paths (for canary only; not recommended longer-term).
- `CHATMRPT_ROUTER_OBS=0` to silence logs if needed.

## Notes & Next
- Extend clarifiers to any additional parameters as they are schema-ized (e.g., risk method variants).
- After stable canary, the legacy keyword/matching code paths are removed; current status: TPR fuzzy removed, others already avoided.
