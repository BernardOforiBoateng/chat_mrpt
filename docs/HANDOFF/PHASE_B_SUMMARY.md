# Phase B — Analyze-Data Safety, Helpers, Memory (Completed)

Safety & Helpers:
- Secure executor timeouts + restricted imports:
  - `app/data_analysis_v3/core/executor.py:288` — subprocess with kill on timeout; allowlist of imports; safe builtins
  - Helpers injected: `top_n`, `ensure_numeric`, `suggest_columns`
- ColumnResolver & validation (data-first):
  - `app/data_analysis_v3/tools/python_tool.py:100` — `df_norm`, `resolve_col`, output validation/sanitization
- Memory for router and agent:
  - `app/services/memory_service.py:1` — file backed, optional Redis (`CHATMRPT_USE_REDIS_MEMORY=1`)
  - Router uses compact summaries; agent persists/loads chat history across turns/workers
- Observability extension:
  - `tool_event` latency + error logs from RequestInterpreter; docs updated

Flags:
- `CHATMRPT_ANALYZE_TIMEOUT_MS=25000` (default)
- `CHATMRPT_USE_REDIS_MEMORY=1` (optional)
