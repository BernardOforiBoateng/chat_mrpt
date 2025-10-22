# File Changelog — Key Modifications

- app/core/choice_interpreter.py — NEW universal LLM-based arg resolver
- app/core/tool_schema_registry.py — NEW schemas for ITN/maps/risk/analyze-data hints/TPR
- app/core/request_interpreter.py — Integrates resolver; adds choice_event; clarifiers; passes normalized_args to agent
- app/data_analysis_v3/core/tpr_workflow_langgraph_tool.py — Uses resolver for facility/age; removed fuzzy matching; emits choice_event
- app/data_analysis_v3/core/agent.py — Accept normalized_args in workflow_context
- app/data_analysis_v3/core/executor.py — Timeouts; restricted imports; helpers injected
- app/data_analysis_v3/tools/python_tool.py — ColumnResolver; validation/sanitization
- app/services/memory_service.py — File/Redis memory; compact summaries
- docs/ROUTER_OBSERVABILITY_AND_FLAGS.md — Added choice_event; flags updated
- docs/UNIVERSAL_CHOICE_INTERPRETER_PLAN.md — Design overview
- docs/UNIVERSAL_INTERPRETER_IMPLEMENTATION_SUMMARY.md — Implementation summary
- tests/CHOICE_INTERPRETER_PARAPHRASE_TESTS.md — Canary prompts
