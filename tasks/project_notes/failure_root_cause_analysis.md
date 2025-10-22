# Root Cause Analysis: Why LangGraph Agent Fails

**Date**: 2025-01-18
**Critical Finding**: Agent generates text instead of executing code

## The Core Problem

**THE AGENT IS NOT USING TOOLS AT ALL**

Despite our fixes:
- ✅ Tools are bound correctly
- ✅ System prompt says "use analyze_data tool"
- ✅ ToolNode is integrated
- ❌ BUT model still chooses text-only responses

## Why Each Type Fails

### Type 1: Simple Queries (Appear to Work but Don't)
**Examples**: "What columns?", "How many wards?", "Show summary"

**Why they "succeed"**:
- Model has context from initial data load
- Can infer reasonable answers from column names
- Returns plausible text without computation

**Why this is bad**:
- Numbers may be wrong
- No actual data access
- User thinks it's working when it's not

### Type 2: Complex Calculations (Admit Failure or Hallucinate)
**Examples**: "Calculate TPR", "Compare LGAs", "Which LGA highest TPR?"

**What happens**:
- Model either:
  a) Admits it can't do it ("persistent issues")
  b) Hallucinates numbers (961K tests from 10K records!)
  c) Returns wrong response type (greeting)

**Why this happens**:
- Can't generate plausible numbers without computation
- Falls back to various failure modes
- Sometimes loses context entirely

### Type 3: Visualizations (Timeout)
**Examples**: "Create heatmap", "Plot scatter", "Time series"

**What happens**:
- These actually DO trigger tool attempts!
- But exceed 60-second ALB timeout
- Never complete

**Why only these trigger tools**:
- Model knows it can't fake a visualization
- Forced to attempt actual code execution
- But implementation is inefficient

## The Tool Invocation Mystery

### Evidence Tools ARE Bound:
```python
# From our fix in agent.py
self.llm_with_tools = self.llm.bind_tools(self.tools)
self.model = self.chat_template | self.llm_with_tools
```

### But Model Doesn't Use Them Because:

1. **Weak System Prompt**
   - Current: "Execute python code using analyze_data tool"
   - Not strong enough to override model's preference
   - Model interprets as optional suggestion

2. **Tool Choice Setting**
   - Currently: `tool_choice: "auto"` (implicit)
   - Means: Model decides whether to use tools
   - Model chooses: Text responses (easier/faster)

3. **Message History Pattern**
   - Initial overview is text-only
   - Sets precedent for text responses
   - Model continues pattern

4. **Missing Reinforcement**
   - No error when tools aren't used
   - No feedback loop to correct behavior
   - Model learns text is acceptable

## Why Response #6 Returns a Greeting

**Query**: "Which LGA in Adamawa has the highest malaria test positivity rate?"
**Response**: "Hello! I'm here to help you analyze malaria data..."

**Root Cause**: STATE MANAGEMENT FAILURE
- Session state not properly maintained
- Worker possibly lost context
- Reverted to initial greeting mode
- Suggests state isolation issue between requests

## Why Timeouts Only Happen on Visualizations

### Pattern:
- Text responses: 3-5 seconds ✅
- Simple calculations: 5-8 seconds ✅
- Visualizations: 60+ seconds ⏱️

### Root Cause:
```python
# When model finally tries to use tool:
1. Attempts to load all 10,452 records
2. Performs complex aggregations
3. Generates Plotly visualization
4. Converts to HTML
5. Times out at ALB (60 seconds)
```

### Why So Slow:
- No data caching
- No query optimization
- Full dataset processing each time
- Plotly rendering overhead
- No streaming/chunking

## The Hallucination Problem

### Case Study: Response #7
**Claims**:
- 961,604 total tested (impossible!)
- 536,198 positive cases
- Bako ward: 100% TPR

**How This Happens**:
1. Model needs specific numbers
2. Can't compute without tools
3. Generates "plausible" values
4. Uses training data patterns
5. Creates impossible statistics

**Why 961,604?**
- Likely from training on Nigerian health data
- National-level statistics bleeding through
- Not from actual dataset (10,452 records)

## Critical Design Flaws

### 1. No Execution Verification
- Responses don't indicate tool use
- No code blocks shown
- No execution confirmation
- User can't distinguish real vs fake

### 2. Optional Tool Usage
- Model can choose not to use tools
- No penalty for text-only responses
- Easier path is always taken

### 3. Weak Prompt Engineering
- System prompt too gentle
- Doesn't force tool usage
- Allows interpretation as suggestion

### 4. Missing Feedback Loop
- No error on non-execution
- No retry mechanism
- No user notification of failure

## Why Our Fixes Didn't Work

### What We Fixed:
1. ✅ Tool binding order (correct now)
2. ✅ System prompt (simplified but not forceful)
3. ✅ ToolNode integration (working)
4. ✅ Option 1 handler (triggers analysis mode)

### What We Missed:
1. ❌ Forcing tool choice
2. ❌ Query preprocessing
3. ❌ Execution verification
4. ❌ Response validation
5. ❌ State persistence across workers

## The Solution Path

### Must Fix:
```python
# 1. Force tool usage
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0,
    tool_choice="required"  # or specific function
)

# 2. Preprocess queries
if in_analysis_mode:
    query = f"You MUST use analyze_data tool. {query}"

# 3. Validate responses
if not response.get("tool_calls"):
    raise Error("No tool execution detected")

# 4. Show code in response
response["show_code"] = True
response["code_executed"] = tool_calls[0].code
```

## Conclusion

**The agent architecture is correct, but the model is not being forced to use it.**

The tool binding works, the infrastructure exists, but the model takes the path of least resistance - generating text instead of executing code.

This is not a complex technical failure but a simple prompt engineering and configuration issue. The model CAN use tools (as evidenced by timeout attempts on visualizations) but CHOOSES not to for most queries.

**Bottom Line**: Users think they're getting data analysis but are receiving sophisticated fiction.