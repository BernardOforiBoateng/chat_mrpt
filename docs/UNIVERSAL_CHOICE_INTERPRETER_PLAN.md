# Universal Natural-Language Choice & Argument Interpreter (Design Doc)

This document specifies a universal, LLM‑first argument interpreter for ChatMRPT that enables users to speak naturally in any flow (TPR, Risk, ITN, Maps, Data Analysis) without exact keywords. It replaces scattered keyword parsing with a centralized, schema‑driven resolver, improving accuracy, observability, and maintainability.

## Objectives
- Natural language everywhere: Users can say “go with primary”, “rapid tests please”, “make it 200k nets”, “second one”, “same as before”.
- LLM‑first slot filling: Map free text → canonical tool + validated arguments (enums, numbers, strings) with confidence and brief rationale.
- Guardrails intact: Router gates (TPR→Risk→ITN) still enforced regardless of phrasing.
- No brittle synonym lists: Few compact examples (few‑shots) + JSON schema constraints; minimal heuristics only as safety net.

## Architecture Overview
- Universal Arg Interpreter (LLM)
  - Inputs: `user_text`, `tool_schema` (JSON), `memory_summary`, `context` (session flags, column hints), optional `active_tool_hint`.
  - Output (strict JSON): `{ tool, args, confidence, reason }`, where `args` validates against the tool’s JSON schema.
  - Confidence gating: `≥0.7` auto‑run; `0.4–0.7` ask one concise clarifier (with UI chips); `<0.4` ask to rephrase.
  - Deterministic fallbacks (only if LLM output invalid): ordinals (“first/second/third”), light regex for obvious phrases, mild fuzzy.

- Tool Schema Registry (central)
  - Single source of truth for all tool argument schemas (enums, numeric ranges, required/optional, defaults, soft constraints, compact examples).
  - Examples are representative, not synonym lists.

- Integration points
  - Router: After intent selection and gate checks, call the Arg Interpreter for the selected tool to resolve parameters; then execute tool.
  - LangGraph Agent: Add normalized args to agent state (as hints), so generated code uses correct columns/limits without exact phrasing.
  - Memory: Persist resolved choices and relevant args; support references like “same as before/again/second one”.

## Prompt & Schema
- Prompt
  - Provide: `user_text`, compact `memory_summary`, `tool_schema` (allowed enums/fields), session flags, columns (canonical/aliases), and a strict output JSON schema.
  - Few‑shots: 3–5 diverse examples per argument category (e.g., facility_level, age_group, test_method, method=pca, N=10, variable=rainfall). Avoid synonym lists.
  - Output: strict JSON only; no additional text.

- Output Schema (example)
```
{
  "tool": "run_tpr_step",
  "args": {
    "facility_level": "primary|secondary|tertiary|all",
    "age_group": "u5|o5|pw|all",
    "test_method": "rdt|microscopy|both",
    "N": 10,
    "map_variable": "rainfall"
  },
  "confidence": 0.0,
  "reason": "short justification"
}
```

## Observability
- Add `choice_event` (universal) alongside existing `router_event` and `tool_event` logs.
- Payload:
```
{
  "type": "choice_event",
  "session_id": "...",
  "tool": "...",
  "args": { ... },
  "confidence": 0.82,
  "matched_by": "llm|ordinal|regex|fuzzy",
  "user_text": "..."
}
```
- Metrics: choice acceptance rate, clarify rate, latency; dashboards for tuning.

## Feature Flags
- `CHATMRPT_CHOICE_RESOLVER=1` (enable universal interpreter; canary first)
- Reuse existing flags for routing/observability/timeouts as needed.

## Rollout Plan
1. Scaffolding
   - New: `app/core/tool_schema_registry.py` — declarative schemas.
   - New: `app/core/choice_interpreter.py` — LLM prompt + validation + safety net.
   - Update: `app/core/request_interpreter.py` — invoke interpreter pre‑tool; emit `choice_event`.
   - Update: `app/data_analysis_v3/core/agent.py` — accept normalized args as hints in state.

2. Convert flows (behind flag)
   - TPR: facility_level, age_group, test_method → remove keyword parsing.
   - Risk: method selection (composite|pca|both), proceed intents.
   - ITN: total_nets and thresholds (numbers + units; confirm if ambiguous).
   - Maps: variable + method selection.

3. Cleanup (post‑canary)
   - Archive/remove legacy keyword parsers in TPR/Risk/ITN/Maps.
   - Ensure tools accept only schema‑valid args from the interpreter.

4. Validation & Canary
   - Paraphrase test set: 8–12 phrasings per argument/tool (ordinals, references, synonyms).
   - Success targets: ≥95% choice accuracy; ≤10% clarify rate; sub‑budget latency.
   - Monitor `choice_event` and refine few‑shots; then enable broadly.

## Pitfalls & Mitigations
- Ambiguous inputs → Confidence gating + one concise clarifier + UI chips.
- Hallucinated values → JSON schema validation; reject and clarify.
- Ordinal ambiguity → Deterministic mapping to visible option order.
- Token bloat → Compact memory summary; pass only active tool schema; brief few‑shots.
- Drift & duplication → Central registry; remove scattered keyword logic.
- Gate bypass attempts → Router gates enforced deterministically; interpreter cannot override policy.

## Success Metrics
- Natural language everywhere (no exact keywords needed) across all flows.
- High accuracy (≥95%) with low clarify rate (≤10%).
- Consistent tool execution with schema‑valid args.
- Universal `choice_event` telemetry for continuous improvement.
- Clean code: single interpreter + registry; legacy parsing removed.

## Non‑Goals
- Building exhaustive synonym dictionaries.
- Allowing the interpreter to bypass workflow gates or safety rules.

## Ownership & Touchpoints
- Core: `app/core/choice_interpreter.py`, `app/core/tool_schema_registry.py`, `app/core/request_interpreter.py`
- Agent: `app/data_analysis_v3/core/agent.py`
- Tools (convert): `app/data_analysis_v3/core/tpr_workflow_langgraph_tool.py`, Risk/ITN/Map tools
- Docs: `docs/ROUTER_OBSERVABILITY_AND_FLAGS.md` (add `choice_event`), this design doc

