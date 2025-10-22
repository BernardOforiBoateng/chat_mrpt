# Router Observability and Feature Flags

This guide explains how to enable the LLM-first intent router, read router logs, and control feature flags during canary and rollout.

## Feature Flags
- `CHATMRPT_INTENT_ROUTER`
  - `1` (default): Enable LLM intent classification + deterministic routing and gates.
  - `0`: Disable and fall back to legacy orchestration.
- `CHATMRPT_ROUTER_OBS`
  - `1` (default): Emit structured router observability logs.
  - `0`: Disable router logs.
 - `CHATMRPT_ANALYZE_TIMEOUT_MS`
   - Default `25000` (25s): Maximum execution time for analyze-data Python code. If exceeded, the tool returns a timeout error and the process is terminated.
 - `CHATMRPT_CHOICE_RESOLVER`
   - `1` (default for canary): Enable the universal LLM-based argument interpreter with `choice_event` logging.
   - `0`: Disable and fall back to existing keyword/fuzzy paths.

## Router Log Format
Logs are emitted with the marker `[ROUTER_OBS]` from `app/core/request_interpreter.py`.

Fields:
- `type`: always `router_event`
- `session_id`: current session id
- `intent`: classifier’s intent (e.g., `data_analysis`, `risk`, `itn`, `map_variable`, `map_vulnerability`, `concept_help`, `off_domain`)
- `confidence`: 0–1
- `action`: routed action (e.g., `analyze_data`, `risk`)
- `entities`: variables, N, method, map_variable
- `gating`: `{requires_tpr_complete, requires_risk_complete}`
- `classification_latency_ms`: LLM classifier latency in ms
- `tpr_complete`, `risk_complete`, `itn_complete`: session flags

Example:
```
[ROUTER_OBS] {"type":"router_event","session_id":"abc...","intent":"data_analysis","confidence":0.82,"action":"analyze_data","entities":{"variables":["rainfall"],"N":10},"gating":{},"classification_latency_ms":123,"tpr_complete":true,"risk_complete":true,"itn_complete":false}
```

### Tool Event Logs
When tools execute (e.g., analyze-data), an additional `tool_event` is logged to capture execution latency and errors.

Fields:
- `type`: `tool_event`
- `session_id`: current session id
- `tool`: executed tool id (e.g., `analyze_data_with_python`)
- `status`: `success` | `error`
- `tool_latency_ms`: execution latency in ms
- `errors`: array of error messages (optional)

Example:
```
[ROUTER_OBS] {"type":"tool_event","session_id":"abc...","tool":"analyze_data_with_python","status":"success","tool_latency_ms":8450}
```

## Canary Checklist
1. Set env vars on one instance:
   - `CHATMRPT_INTENT_ROUTER=1`
   - `CHATMRPT_ROUTER_OBS=1`
2. Replay representative prompts:
   - “top 10 wards by rainfall” → analyze_data (table)
   - “vulnerability map” (after Risk) → side-by-side map (or composite-only if PCA skipped)
   - “plan ITN with 200k nets” (after Risk) → ITN distribution results
   - “rank wards” mid-TPR → receive gate message with “finish TPR” fork
3. Monitor logs:
   - Routing accuracy & gate adherence
   - Classification latency (target sub-300ms typical)
4. Iterate examples if misroutes occur (update classifier prompt few-shots).

## Troubleshooting
- No logs? Ensure `CHATMRPT_ROUTER_OBS=1` and logger level includes INFO.
- Repeated gate prompts? Verify session flags (`tpr_complete`, `risk_complete`) and cookie session affinity.
- Data questions answered without tables? Confirm `CHATMRPT_INTENT_ROUTER=1` and that analyze-data tool is available.

## Notes
- The router enforces workflow gates; it never runs Risk before TPR or ITN before Risk.
- Data-centric asks always route to the analyze-data tool (LangGraph) to guarantee data-first answers.

### Choice Event Logs (Universal Argument Resolution)
When the universal argument interpreter resolves free‑form user input into schema‑valid tool arguments, a `choice_event` is emitted.

Fields:
- `type`: `choice_event`
- `session_id`: current session id
- `tool`: target tool id
- `args`: resolved arguments (must validate against tool schema)
- `confidence`: 0–1
- `matched_by`: `llm` | `ordinal` | `regex` | `fuzzy`
- `user_text`: original user input

Example:
```
[ROUTER_OBS] {"type":"choice_event","session_id":"abc...","tool":"run_tpr_step","args":{"facility_level":"primary"},"confidence":0.91,"matched_by":"llm","user_text":"go with primary"}
```
