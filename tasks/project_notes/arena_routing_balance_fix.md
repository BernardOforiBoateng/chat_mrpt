# Arena Routing Balance Fix

## Issue Identified
After the initial fix, ALL questions were routing to Arena mode after data upload, including data-specific operations like:
- "summarise the data" → Arena (should be Tools)
- "make an analysis" → Arena (should be Tools)
- "who are you" → Arena (correct)

## Root Cause
The initial fix was too aggressive in defaulting everything to Arena mode. It didn't recognize that certain command verbs (analyze, summarize, plot) typically mean "work with my uploaded data" when data is present.

## Solution: Balanced Routing

### 1. Smart Pre-Routing Filter
- Skip pre-routing for data operation verbs when data is uploaded
- Data operation verbs: summarize, analyze, plot, visualize, map, chart, etc.
- These go to Mistral for proper evaluation instead of being pre-routed to Arena

### 2. Updated Mistral Prompt
- New decision tree that recognizes implicit data operations
- When data is uploaded, commands like "analyze" or "summarize" default to NEEDS_TOOLS
- General knowledge questions still route to Arena correctly

### 3. Refined Logic Flow
```
With Uploaded Data:
- "who are you?" → Arena (identity question)
- "what is malaria?" → Arena (general knowledge)
- "summarize" → Tools (data operation command)
- "analyze" → Tools (data operation command)
- "make an analysis" → Tools (analysis command)
- "plot" → Tools (visualization command)
```

## Testing Results Expected

### Questions that should use Arena (even with data):
✅ "hello"
✅ "who are you?"
✅ "what is malaria?"
✅ "explain TPR"
✅ "how does PCA work?"

### Questions that should use Tools (with data):
✅ "summarize the data"
✅ "summarise"
✅ "analyze"
✅ "make an analysis"
✅ "plot"
✅ "run analysis"
✅ "show my data"

## Deployment Status
- ✅ Deployed to both AWS production instances
- ✅ Services restarted
- Ready for testing on CloudFront

## Key Improvement
The system now understands context:
- Data uploaded + general question = Arena mode
- Data uploaded + data operation verb = Tools/OpenAI
- Proper balance between Arena and Tools usage