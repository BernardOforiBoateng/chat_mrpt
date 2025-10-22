# Choice Interpreter Paraphrase Test Pack (Manual)

Run these prompts with `CHATMRPT_CHOICE_RESOLVER=1` and `CHATMRPT_ROUTER_OBS=1`.
Validate that `choice_event` logs show correct `args` and `confidence ≥ 0.7`.
If confidence < 0.5 and missing required args, verify a concise clarifier appears.

## TPR — Facility Level
- "go with primary"
- "second one"
- "let's do tertiary"
- "all of them"

Expected: facility_level = primary|secondary|tertiary|all

## TPR — Age Group
- "children under five"
- "pregnant women"
- "over five"
- "everyone"

Expected: age_group = u5|pw|o5|all_ages

## ITN — Nets + Method
- "plan ITN with 200k nets"
- "half a million nets"
- "use pca"

Expected: total_nets parsed (200000, 500000), method optional; clarifier if nets missing + low confidence

## Vulnerability Map — Method
- "compare both methods"
- "use composite"
- "let's go pca"

Expected: method = both|composite|pca or clarifier when ambiguous

## Variable Map — Variable
- "map rainfall"
- "map tpr"
- "map the population density"

Expected: map_variable set; if not sure, clarifier lists sample columns

## Risk — Variables (optional)
- "risk with rainfall and elevation"
- "run risk"

Expected: variables parsed when present, empty otherwise (no clarifier required)

## Analyze-Data — Hints
- "top 10 wards by rainfall"
- "show histogram of TPR"

Expected: normalized_args includes N / variable / chart hints in agent workflow_context

---

During the canary, monitor `[ROUTER_OBS] choice_event` logs and measure:
- Choice accuracy ≥ 95%
- Clarify rate ≤ 10%
- Latency within budget
