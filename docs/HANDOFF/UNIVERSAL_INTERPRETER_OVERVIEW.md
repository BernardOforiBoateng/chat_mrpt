# Universal Argument Interpreter — Overview

Purpose:
- Natural-language slot filling everywhere (TPR, Risk, ITN, Maps, Analyze-data hints) without exact keywords.
- LLM-first JSON schema filling with confidence and one concise clarifier when needed.

Key files:
- `app/core/choice_interpreter.py:1` — LLM resolver `{tool, args, confidence, reason}` with numeric coercion and small fallback
- `app/core/tool_schema_registry.py:1` — schemas for ITN, vulnerability map, variable map, risk vars, analyze-data hints, TPR facility/age
- `app/core/request_interpreter.py:318` — universal integration; `choice_event`; clarifiers for ITN nets, map method, map variable
- `app/data_analysis_v3/core/tpr_workflow_langgraph_tool.py:1054` — TPR facility/age use interpreter; concise clarifiers

Observability:
- `choice_event` with `{tool, args, confidence, matched_by, user_text}` in `[ROUTER_OBS]` logs
- Docs: `docs/ROUTER_OBSERVABILITY_AND_FLAGS.md`

Flag:
- `CHATMRPT_CHOICE_RESOLVER=1` (enable universal interpreter)

Cleanup:
- Legacy TPR fuzzy/keyword matching removed; universal interpreter is the source of truth.
