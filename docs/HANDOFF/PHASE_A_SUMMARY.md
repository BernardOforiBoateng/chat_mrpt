# Phase A — LLM-First Router & Gates (Completed)

What shipped:
- LLM intent classifier and prompt:
  - `app/core/intent_classifier.py:1`
  - `app/core/intent_prompt.py:1`
- Router integration (classification before orchestration; hard gates; route actions):
  - `app/core/request_interpreter.py:331` — classification, gating, action selection
- Tool catalog for classifier:
  - `app/core/tool_registry.py` (exposes classifier catalog)
- Data-first tool (already hardened in Phase 1 architecture):
  - `app/data_analysis_v3/tools/python_tool.py:1` (ColumnResolver injection, validation)
- Observability:
  - `docs/ROUTER_OBSERVABILITY_AND_FLAGS.md` — feature flags and `router_event` spec
  - Router logs include: `intent`, `confidence`, `action`, `entities`, `gating`, `classification_latency_ms`
- Feature Flags:
  - `CHATMRPT_INTENT_ROUTER=1` (enable router)
  - `CHATMRPT_ROUTER_OBS=1` (emit logs)
- Cleanup:
  - Removed legacy/broken/backup routing code that competed with LLM routing (superseded by classifier + gates).

Canary prompts:
- “top 10 wards by rainfall” ? analyze_data tool (table)
- “vulnerability map” (post-Risk) ? expected vulnerability map
- “plan ITN with 200k nets” (post-Risk) ? ITN planning flow
- “rank wards” mid-TPR ? gate prompt shown
