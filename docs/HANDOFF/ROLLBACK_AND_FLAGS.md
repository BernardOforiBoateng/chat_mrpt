# Rollback & Flags

Flags:
- `CHATMRPT_INTENT_ROUTER=1|0`
- `CHATMRPT_ROUTER_OBS=1|0`
- `CHATMRPT_CHOICE_RESOLVER=1|0`
- `CHATMRPT_ANALYZE_TIMEOUT_MS=<ms>`
- `CHATMRPT_USE_REDIS_MEMORY=1|0` (+ Redis envs)

Rollback guidance:
- Universal interpreter off: set `CHATMRPT_CHOICE_RESOLVER=0`. Non-TPR flows will fall back to existing behavior. Note: TPR fuzzy/keyword fallback has been removed per plan; to restore legacy TPR parsing, revert the changes to `app/data_analysis_v3/core/tpr_workflow_langgraph_tool.py` via VCS.
- To disable observability: set `CHATMRPT_ROUTER_OBS=0`.
- To relax analyze-data timeouts: increase `CHATMRPT_ANALYZE_TIMEOUT_MS`.
