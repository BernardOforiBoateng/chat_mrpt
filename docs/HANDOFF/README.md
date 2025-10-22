# ChatMRPT — Universal Natural-Language Interpreter Handoff (Phase A + B)

This folder is a compact, developer-ready handoff for review and deployment. It covers:
- Phase A (LLM-first routing + gates) summary
- Phase B (analyze-data safety + helpers) summary
- Universal argument interpreter (LLM-first slot filling) across all flows
- Observability (router/tool/choice events), canary plan, rollback, and deployment steps

Artifacts in this folder:
- PHASE_A_SUMMARY.md — What shipped in Phase A (router/gates, flags, logs)
- PHASE_B_SUMMARY.md — Analyze-data safety, helpers, memory
- UNIVERSAL_INTERPRETER_OVERVIEW.md — Design + scope for the universal arg interpreter
- DEPLOYMENT_GUIDE.md — How to deploy to AWS (from CLAUDE.md) + flags
- CANARY_PLAN.md — Test prompts + accept criteria + how to read logs
- ROLLBACK_AND_FLAGS.md — Flags + short rollback guidance
- TEST_PLAN.md — What/where to test locally and on instances
- FILE_CHANGELOG.md — Files changed/added and why

Refer to root docs for deeper background:
- docs/UNIVERSAL_CHOICE_INTERPRETER_PLAN.md (design)
- docs/UNIVERSAL_INTERPRETER_IMPLEMENTATION_SUMMARY.md (full summary)
- docs/ROUTER_OBSERVABILITY_AND_FLAGS.md (events + flags)

