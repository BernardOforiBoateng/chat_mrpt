# Canary Plan — Universal Interpreter

Env vars (instance-level):
- `CHATMRPT_INTENT_ROUTER=1`
- `CHATMRPT_ROUTER_OBS=1`
- `CHATMRPT_CHOICE_RESOLVER=1`\r

Prompts to replay:
- TPR Facility: “go with primary”, “second one”, “let's do tertiary”, “all of them”
- TPR Age: “children under five”, “pregnant women”, “over five”, “everyone”
- ITN: “plan ITN with 200k nets”, “half a million nets”, “use pca”
- Vulnerability map: “compare both methods”, “use composite”, “let’s go pca”
- Variable map: “map rainfall”, “map tpr”, “map the population density”
- Risk: “risk with rainfall and elevation”; “run risk”
- Analyze-data: “top 10 wards by rainfall”, “show histogram of TPR”

Acceptance:
- Choice accuracy = 95%
- Clarify rate = 10% (one concise question)
- Latency within budget

Observability:
- `[ROUTER_OBS] choice_event` with `{tool, args, confidence, matched_by, user_text}`
- `router_event` for classifier; `tool_event` for execution
