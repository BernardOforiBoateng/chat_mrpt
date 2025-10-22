# Test Plan — Local & Instance

Local (dev box):
- Ensure venv with required deps (LangChain/LangGraph installed).
- Set flags (`CHOICE_RESOLVER`, `INTENT_ROUTER`, `ROUTER_OBS`).
- Run subset tests or manual prompts; watch for `[ROUTER_OBS] choice_event`.

Instances (post-deploy):
- Repeat canary prompts (see CANARY_PLAN.md).
- Verify logs, service status, and CloudFront endpoint.

Troubleshooting:
- If interpreter returns low confidence with no args, expect a clarifier; respond naturally or use chips.
- If long analyzes hang: check timeout flag; executor should return a timeout error instead of hanging.
