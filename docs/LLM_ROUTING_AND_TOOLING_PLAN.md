# LLM‑First Routing and Tooling Plan

This document specifies a robust, LLM‑first routing design that fully leverages GPT‑4o for intent understanding and tool selection, while enforcing workflow gates (TPR → Risk → ITN), guaranteeing data‑first answers for data‑centric questions, and preserving consistent visualization UX. It replaces brittle keyword heuristics with an intent classifier and deterministic router policies.

## Objectives
- Maximize LLM intelligence for intent and entity extraction; avoid rigid keyword logic.
- Strict workflow gates: no Risk before TPR; no ITN before Risk; consistent maps.
- Data‑first for data questions: never free‑text lists; always compute on user data.
- Preserve UX consistency for maps/ITN and reduce latency via clear routing.

## Architecture Overview
- LLM Intent Classifier (primary)
  - Dedicated GPT‑4o function call returns a structured decision:
    - `intent`: {tpr, risk, itn, map_variable, map_vulnerability, data_analysis, concept_help, off_domain}
    - `entities`: {variables, N, ward/state names, method, visualization type}
    - `confidence`: 0–1
    - `gating`: {requires_tpr_complete, requires_risk_complete}
    - `action`: {specialized_tool_id | analyze_data | ask_clarify}
    - `reasoning_summary`: short rationale
  - Inputs: user message, session state (TPR/Risk/ITN flags), memory summary, canonical column list + aliases, tool catalog metadata.

- Tool Catalog & Capabilities
  - Each tool annotated with:
    - `capabilities`: e.g., tpr_flow, risk_pipeline, vulnerability_map, itn_plan, variable_distribution_map, data_analysis_generic
    - `gates`: e.g., risk requires tpr_complete; itn requires risk_complete
    - `outputs`: tables/charts/maps/download links; theme notes

- Router Policy (deterministic)
  1. Invoke LLM classifier with session context & tool catalog.
  2. Enforce gates:
     - If requested intent violates a gate, return one concise fork:
       - “Finish TPR with defaults” OR “Continue TPR at step X” (no silent bypass)
  3. Select tool/action:
     - Specialized intents → specialized tools (TPR, Risk, vulnerability map, ITN, variable distribution map)
     - `data_analysis` → LangGraph analyze‑data tool with entity hints
     - `concept_help` → LLM direct answer (domain‑scoped)
     - `off_domain` → polite malaria‑focused redirect
  4. Execute; include memory/context; for maps, always use visualization tools (consistent theme/UX)
  5. Validate outputs (placeholders, top‑N count, percentage bounds)
  6. Log: intent, confidence, selected tool, outcome (for learning)

- Heuristic Fallback (last resort)
  - Only if classifier fails or returns low confidence and a single clarification is declined.
  - If the model responds without tools to a clearly data‑centric question, auto‑fallback to analyze‑data once.

## Workflow Gates
- TPR required before Risk; Risk required before ITN.
- “Map” resolves to:
  - Risk complete → vulnerability map (composite only if PCA skipped; else side‑by‑side)
  - Only TPR complete → TPR map
  - Neither → variable distribution map if explicitly named; otherwise propose next step
- “Top 10 wards” before Risk → guided fork to finish TPR (defaults) then run Risk and respond.

## Memory & Context
- Redis‑backed per‑session memory:
  - Last N turns, rolling summary, workflow facts (data_loaded, tpr_complete, risk_complete, selected state, last tool/visualization)
- Classifier & tools receive memory and available columns to resolve pronouns (“same as before”), ellipsis (“again”), and follow‑ups.

## Analyze‑Data (LangGraph) Scope
- Default for non‑specialized, data‑centric queries:
  - “which/top N/list/rank/table”, “what/how/why/compare/correlation/trend/summary”, filter/group/aggregate; non‑map charts.
- Phase 1 readiness: ColumnResolver (case‑insensitive + aliases + mild typos), session df fallback, output validation (block placeholders; enforce top‑N), Plotly capture, pandas/numpy/sklearn/geopandas/plotly.
- Phase 2 hardening: execution timeout & restricted imports; helper utilities (top_n, ensure_numeric, column suggestions); better agent memory across turns.

## Prompts (High Level)
- Intent Classifier Prompt
  - Provide: tool catalog (capabilities/gates), session state, memory summary, available columns (canonical names + aliases), task examples (typos, abbreviations, terse asks)
  - Output schema: {intent, entities, confidence, gating, action, reasoning_summary}
  - Rules: choose a single action; ask one concise clarification if low confidence; never bypass gates

- Analyze‑Data (LangGraph) Prompt
  - Data‑first mandates:
    - Always compute for “which/top N/show/compare/correlation/table”
    - Use `to_markdown` tables; no free‑text lists
    - Use `df_norm` and `resolve_col` with aliasing; provide suggestions if miss

## Rollout Plan
- Phase A (LLM Router, 2–3 days)
  - Add intent classifier (function-calling) + tool catalog metadata + router integration
  - Remove keyword heuristics (retain hidden fallback for failures)
  - Enforce gates deterministically
- Phase B (Analyze‑Data Safety & Memory, 2–3 days)
  - Add execution timeout & restricted imports; helper utilities
  - Integrate conversation memory into classifier and analyze‑data agent
- Phase C (Observability & Canary, 1–2 days)
  - Log intent/confidence/tool/outcome; replay 10 key sessions; canary rollout; feature flags; rollback

## Success Metrics
- Routing accuracy: ≥95% of non‑specialized, data‑centric requests → analyze‑data; specialized intents → specialized tools
- Gate adherence: 100% (no Risk without TPR; no ITN without Risk)
- Zero “No data available” after upload acknowledgement
- Zero placeholder leakage; 100% top‑N tables with exact N items
- Clarification turns per task: median ≤1
- Time‑to‑first result: within target for typical datasets

## Risks & Pitfalls (and Mitigations)
- Misclassification → One concise clarification; fallback to analyze‑data; log for continual refinement
- Gate bypass risk → Hard policy in router (post‑classifier checks)
- Latency/cost → Cache tool catalog prompt, keep classifier concise, enforce analyze‑data timeouts
- Inconsistent maps if routed via generic tool → Never render maps in analyze‑data; map intents always go to visualization tools
- Memory drift across workers → Redis/cookie affinity; restore memory on request
- Tool metadata stale → Centralize metadata; add health check for tool availability
- Prompt token bloat → Compact memory summary; cap column list; use examples sparingly

## Files to Modify
- `app/core/request_interpreter.py`
  - Integrate intent classifier call; remove keyword heuristics; enforce gates; route per policy; add logging
- `app/core/tool_registry.py`
  - Add tool capability and gate metadata; expose catalog to classifier
- `app/services/memory_service.py`
  - Ensure fast retrieval of memory summary for classifier and tools
- `app/data_analysis_v3/core/executor.py`
  - Add execution timeout & restricted imports; inject helper utilities (Phase B)
- `app/data_analysis_v3/tools/python_tool.py`
  - Ensure ColumnResolver & session fallback are used; minor refactor to expose helper funcs (Phase B)
- `app/data_analysis_v3/prompts/system_prompt.py`
  - Align wording with data‑first and routing expectations

## Files to Create
- `app/core/intent_classifier.py`
  - Classifier interface: builds classifier prompt, calls GPT‑4o function, validates JSON schema
- `app/core/intent_prompt.py`
  - Prompt template and few‑shot examples; tool catalog injection; output schema definition
- `app/core/tool_metadata.py` (or extend tool_registry)
  - Declarative tool descriptors: capabilities, gates, outputs, usage notes
- `docs/LLM_ROUTING_AND_TOOLING_PLAN.md`
  - This document

## Files to Archive/Remove (after verification)
- Remove or archive keyword‑based pre/post fallbacks in `request_interpreter.py`
- Remove legacy/deprecated routing helpers that duplicate classifier behavior
- Keep a minimal emergency fallback behind a feature flag for initial canary

## Feature Flags
- `CHATMRPT_INTENT_ROUTER=1` (enable classifier‑based routing)
- `CHATMRPT_ANALYZE_TIMEOUT_MS` (default 20–30s)
- `CHATMRPT_STRICT_GATES=1` (hard enforce TPR→Risk→ITN)

## Observability & QA
- Log: `{timestamp, session_id, user_text, classifier.intent, confidence, selected_tool, gate_status, outcome, latency}`
- Replay 10 canonical sessions (typos, abbreviations, terse asks, mid‑workflow jumps)
- Canary on 1 instance; monitor routing accuracy, latency, errors; rollback via feature flags

## Non‑Goals
- Replacing specialized tools with generic Python analysis (keep them)
- Free‑text data answers without code (always data‑first for data questions)

## Acceptance Checklist
- Classifier correctly routes: TPR/Risk/ITN/maps vs data_analysis vs concept_help/off_domain
- Gates enforced; fork offered when user jumps ahead
- Data questions always produce tables/charts from real data; no placeholders
- Maps use visualization tools with consistent theme
- Memory respected for pronouns and follow‑ups

