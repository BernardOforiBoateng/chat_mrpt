# TPR LLM-First - Investigation Findings

**Date**: 2025-10-10
**Status**: Investigation Complete
**Next Step**: Get approval for fixes

---

## Executive Summary

Completed comprehensive investigation into why agent doesn't use data context when asked "what variables do I have?"

**ROOT CAUSE IDENTIFIED**: System prompt tells agent to ALWAYS call `analyze_data` tool for ANY "what/why/how" questions, even simple ones that could be answered from context.

**Impact**: HIGH - Core user deviation scenario (asking about data) doesn't work smoothly

**Solution**: Refine system prompt to distinguish between:
- Simple context questions → Answer from context directly (fast)
- Complex analysis questions → Use tool (accurate)

---

## Investigation Process

### 1. System Prompt Analysis ✅

**File**: `app/data_analysis_v3/prompts/system_prompt.py`

**Finding**:
```python
## UNIVERSAL RULE: Data-First Responses (CRITICAL)

### When to Use analyze_data Tool (MUST):
Whenever a question requires actual calculations, comparisons, or evidence from the dataset, call the tool—even if the user phrases it casually.
- Prompts that start with **Why**, **What**, **How**, **Which**, **Explain**, **Show**, **Compare**.
```

**Analysis**:
- Prompt says to use tool for **ANY** question starting with "What/Why/How"
- "What variables do I have?" triggers tool call
- Tool is NOT needed for this - columns are already in context

**Conclusion**: Prompt is too aggressive about tool usage

---

### 2. Agent Response Analysis ✅

**File**: `tasks/project_notes/2025_10_10_live_test_results.md`

**Test Case**: "what variables do I have?"

**Results**:
```
→ success: True
→ message length: 404 characters
→ columns mentioned: 0/12  ❌

Tool Execution Warnings:
⚙️ [EXECUTOR] ⚠️ Process still alive after 25000ms, terminating
Analysis code timed out after 25000ms

Observation: Agent might be trying to execute Python tool unnecessarily
```

**Analysis**:
- Agent called `analyze_data` tool
- Tool execution timed out after 25 seconds
- Agent gave generic 404-character response
- Response didn't mention ANY of the 12 column names

**Conclusion**: Agent tried to use tool, failed, gave generic response

---

### 3. Data Flow Verification ✅

**File**: `app/data_analysis_v3/core/agent.py`

**Finding 1: Data Loading** (lines 311-427):
```python
def _get_input_data(self) -> List[Dict[str, Any]]:
    """Load most comprehensive dataset available for data-aware responses."""
    # ... loads CSV files ...

    data_obj = {
        'variable_name': 'df',
        'data_description': f"Dataset with {len(df)} rows and {len(df.columns)} columns",
        'data': df,  # CRITICAL: Actual DataFrame
        'columns': df.columns.tolist()  # ✅ COLUMNS ARE HERE
    }
    input_data_list.append(data_obj)
```

**Finding 2: Data Summary Creation** (lines 195-225):
```python
def _create_data_summary(self, state: DataAnalysisState) -> str:
    """Create summary of available data - enhanced for data-aware responses."""
    # ...
    if 'columns' in data_obj and data_obj['columns']:
        cols = data_obj['columns']
        if len(cols) <= 10:
            summary += f"Columns: {', '.join(cols)}"  # ✅ COLUMNS LISTED
        else:
            summary += f"Columns ({len(cols)} total): {', '.join(cols[:10])}..."

    # Add reminder about data-first approach
    if summary:
        summary += "\n\n**Remember: Use analyze_data tool to examine this data for ANY 'why/what/how/which/explain' questions!**"
        # ⚠️ THIS TELLS AGENT TO USE TOOL FOR "WHAT" QUESTIONS!
```

**Finding 3: Data Summary Added to Messages** (lines 227-247):
```python
def _agent_node(self, state: DataAnalysisState):
    """Agent node - calls GPT-4o with tools."""
    # Create data context message
    data_summary = self._create_data_summary(state)
    current_data_message = HumanMessage(
        content=current_data_template.format(data_summary=data_summary)
    )

    # Prepend data context to messages
    state["messages"] = [current_data_message] + state.get("messages", [])
    # ✅ DATA SUMMARY WITH COLUMNS IS ADDED
```

**Finding 4: Workflow Context Also Passes Columns** (lines 573-613):
```python
if workflow_context:
    # ...
    if data_columns:
        context_parts.append(f"\n⚠️  IMPORTANT - USER'S DATASET INFORMATION:")
        context_parts.append(f"Total columns: {len(data_columns)}")
        context_parts.append(f"\nColumn names:")
        context_parts.append(f"{', '.join(data_columns[:15])}")
        # ✅ COLUMNS ALSO IN WORKFLOW CONTEXT
```

**Conclusion**: Agent receives columns in **TWO** places:
1. Data summary message (from `_create_data_summary`)
2. Workflow context message (from workflow_context parameter)

**The data is definitely there!**

---

### 4. Tool Calling Behavior Analysis ✅

**Issue**: Agent calls `analyze_data` tool even for simple "list columns" questions

**Why**:
1. System prompt says: "Use analyze_data tool for ANY 'why/what/how/which/explain' questions"
2. "What variables do I have?" starts with "What"
3. Agent follows prompt and calls tool
4. Tool execution is slow/times out
5. Agent gives generic response instead of using context

**Evidence**:
- Test showed: "Process still alive after 25000ms, terminating"
- Agent tried to execute tool for 25 seconds
- Tool timed out, agent couldn't complete analysis
- Fallback response didn't use the context data

**Conclusion**: System prompt over-specifies tool usage

---

### 5. LLM Prompt Construction Review ✅

**Current Prompt Structure**:
```
1. System Prompt (MAIN_SYSTEM_PROMPT)
2. Data Summary Message (with columns + "use tool for what questions")
3. Workflow Context Message (with columns again)
4. User Query ("what variables do I have?")
```

**Problem**: Conflicting instructions!
- Data summary includes columns
- Data summary also says "use tool for what questions"
- Agent sees "what" question, uses tool
- Agent ignores the columns already in context

**Analysis**:
```
System Prompt:
"Use analyze_data tool for ANY 'why/what/how/which/explain' questions"
↓
Data Summary:
"Columns: State, LGA, Ward, ... (12 total)"
"**Remember: Use analyze_data tool for ANY 'why/what/how/which/explain' questions!**"
↓
User: "what variables do I have?"
↓
Agent: Sees "what" → Must use tool (per prompt)
Agent: Calls analyze_data → Times out
Agent: Gives generic response
```

**Conclusion**: Prompt needs to distinguish simple vs complex questions

---

## Root Cause Summary

**The Problem**: System prompt treats ALL "what" questions the same way

**Current Behavior**:
- "What variables do I have?" → Calls tool → Times out → Generic response
- "What is the average TPR?" → Calls tool → Calculates → Specific response

**Desired Behavior**:
- "What variables do I have?" → Reads context → Lists columns immediately
- "What is the average TPR?" → Calls tool → Calculates → Specific response

**Why This Matters**:
- Users asking "what columns/variables do I have?" is a COMMON deviation scenario
- Current behavior: 25-second wait → generic response → bad UX
- Desired behavior: Instant response with actual column names → good UX

---

## Proposed Fixes

### Fix #1: Refine System Prompt (HIGH PRIORITY)

**File**: `app/data_analysis_v3/prompts/system_prompt.py`

**Change**: Distinguish between context questions vs analysis questions

**Before**:
```
### When to Use analyze_data Tool (MUST):
Whenever a question requires actual calculations, comparisons, or evidence from the dataset, call the tool—even if the user phrases it casually.
- Prompts that start with **Why**, **What**, **How**, **Which**, **Explain**, **Show**, **Compare**.
```

**After**:
```
### When to Use analyze_data Tool (MUST):

**Use tool for analysis questions** (requires calculation/inspection):
- "What is the average/median/max/min TPR?" → TOOL NEEDED
- "Which wards have highest TPR?" → TOOL NEEDED
- "How many wards have TPR > 10%?" → TOOL NEEDED
- "Why are these wards ranked high?" → TOOL NEEDED (examine values)
- "Show me the distribution of..." → TOOL NEEDED (create viz)

**Answer from context directly** (metadata questions):
- "What variables/columns do I have?" → NO TOOL (just list columns from context)
- "How many rows/columns?" → NO TOOL (use dataset shape from context)
- "What is the dataset about?" → NO TOOL (describe from context)
- "What data is available?" → NO TOOL (list datasets from context)

**Key Distinction**:
- If answer is ALREADY in the context messages → Answer directly
- If answer requires LOOKING AT actual data values → Use tool
```

**Impact**: Allows agent to answer simple questions instantly from context

---

### Fix #2: Remove Conflicting Reminder from Data Summary (MEDIUM PRIORITY)

**File**: `app/data_analysis_v3/core/agent.py`, lines 221-223

**Change**: Remove the reminder that tells agent to use tool for "what" questions

**Before**:
```python
if summary:
    summary += "\n\n**Remember: Use analyze_data tool to examine this data for ANY 'why/what/how/which/explain' questions!**"
```

**After**:
```python
if summary:
    summary += "\n\n**This data is loaded and available for analysis.**"
```

**Rationale**: System prompt already covers tool usage. Data summary shouldn't contradict the refined system prompt.

**Impact**: Removes conflicting instruction

---

### Fix #3: Add Explicit "Simple Questions" Example (LOW PRIORITY)

**File**: `app/data_analysis_v3/prompts/system_prompt.py`

**Change**: Add example showing how to answer "what columns" question

**Addition**:
```
### Example - Simple Context Question (NO TOOL):
User: "What variables do I have?"

**Correct Response:** ✅
Your dataset has 12 columns:
- State, LGA, Ward
- HealthFacility, FacilityLevel
- AgeGroup, TotalTests, PositiveTests
- TPR, Rainfall, NDWI, EVI

You're currently in the facility selection stage. Would you like to select primary, secondary, tertiary, or all facilities?

**Wrong Response:** ❌
Let me check the data...
[calls analyze_data tool]
[times out]
You have a dataset with various columns.
```

**Impact**: Shows agent the correct pattern for simple questions

---

## Alternative Approaches Considered

### Alternative 1: Always Answer from Context First, Then Elaborate with Tool

**Approach**:
- Agent always lists columns from context immediately
- Then optionally calls tool for deeper analysis

**Pros**:
- User gets fast response
- Can still get detailed analysis

**Cons**:
- Might be verbose
- Two-step response for simple questions

**Verdict**: Not as good as refined prompt (Fix #1)

---

### Alternative 2: Pre-Process Question to Route

**Approach**:
- Add router before agent that detects "metadata questions"
- Route to different handler that just returns context

**Pros**:
- Fast for simple questions
- No tool call overhead

**Cons**:
- Adds complexity
- More routing logic
- Harder to maintain

**Verdict**: Over-engineering, refined prompt is simpler

---

### Alternative 3: Add "lite" Tool for Metadata

**Approach**:
- Create lightweight `get_metadata` tool that just returns columns
- Separate from heavy `analyze_data` tool

**Pros**:
- Fast metadata retrieval
- Agent still uses tools (consistent pattern)

**Cons**:
- Unnecessary - context already has metadata
- Adds tool overhead
- Complicates architecture

**Verdict**: Solves wrong problem, context already has the data

---

## Testing Plan for Fixes

### Test 1: Simple Context Questions (NO TOOL)

**Questions**:
1. "what variables do I have?"
2. "how many columns?"
3. "what is the dataset about?"
4. "show me the column names"
5. "what data is available?"

**Expected Behavior**:
- Agent answers immediately from context (< 2s)
- Lists actual column names
- No tool execution
- No timeout warnings

**Success Criteria**:
- All 5 questions answered with actual column names
- Response time < 2 seconds
- No tool calls in logs

---

### Test 2: Analysis Questions (USE TOOL)

**Questions**:
1. "what is the average TPR?"
2. "which wards have highest TPR?"
3. "how many wards have TPR > 10%?"
4. "show me the distribution of TPR"
5. "why are these wards ranked high?"

**Expected Behavior**:
- Agent calls analyze_data tool
- Tool executes successfully
- Returns specific numbers from actual data
- Creates visualizations where appropriate

**Success Criteria**:
- All 5 questions trigger tool call
- Tool executes without timeout
- Responses include actual data values
- Visualizations created where relevant

---

### Test 3: Mixed Questions (COMBINATION)

**Questions**:
1. "what columns do I have and what is the average TPR?"
2. "show me the dataset info then plot TPR distribution"

**Expected Behavior**:
- Agent answers context part immediately
- Then calls tool for analysis part
- Both parts addressed in response

**Success Criteria**:
- Context questions answered from context
- Analysis questions use tool
- Complete response covering both parts

---

### Test 4: Regression Test (EXISTING FUNCTIONALITY)

**Questions**: Re-run all 113 realistic user tests

**Expected Behavior**:
- No regression in intent classification
- No regression in selection extraction
- Improved agent handoff (mentions columns)

**Success Criteria**:
- Pass rate ≥ 71.7% (current baseline)
- Agent handoff test now passes (mentions columns)
- No new failures introduced

---

## Implementation Plan

### Phase 1: Core Fixes (2 hours)

1. **Update system prompt** (Fix #1)
   - File: `app/data_analysis_v3/prompts/system_prompt.py`
   - Change: Refine "When to Use Tool" section
   - Add: Examples for simple vs complex questions
   - Test: Manual verification

2. **Remove conflicting reminder** (Fix #2)
   - File: `app/data_analysis_v3/core/agent.py`, line 222
   - Change: Update data summary reminder
   - Test: Check data summary output

3. **Add example** (Fix #3)
   - File: `app/data_analysis_v3/prompts/system_prompt.py`
   - Add: "Simple Context Question" example
   - Test: Visual inspection

### Phase 2: Testing (2 hours)

1. **Simple context questions test** (30 min)
2. **Analysis questions test** (30 min)
3. **Mixed questions test** (30 min)
4. **Regression test** (30 min)

### Phase 3: Other Fixes (2 hours)

1. **Negation detection** (30 min)
   - Add pre-LLM check for negations
   - Test: "not primary" → navigation

2. **Very short inputs** (30 min)
   - Add length-based mapping
   - Test: "ok", "k", "no" → correct intents

3. **Intent boundaries** (1 hour)
   - Update LLM prompt examples
   - Test: data_inquiry vs information_request

**Total Time**: 6 hours

---

## Risk Assessment

### Low Risk ✅

**Fix #1 (Refine System Prompt)**:
- Only changes how agent interprets questions
- Doesn't change data flow
- Doesn't change tools
- Easy to revert if needed

**Fix #2 (Remove Reminder)**:
- Small one-line change
- No functional impact
- Just removes conflicting instruction

**Fix #3 (Add Example)**:
- Additive change
- Doesn't modify existing behavior
- Helps agent learn pattern

### Mitigation

- Test thoroughly before deployment
- Keep backup of original prompts
- Monitor logs for tool call patterns
- Can revert individual fixes if needed

---

## Success Metrics

**Before Fixes**:
- "what variables do I have?" → 25s timeout → 0/12 columns mentioned
- Realistic tests: 71.7% (81/113)
- Negations: 20% (1/5)

**Target After Fixes**:
- "what variables do I have?" → <2s response → 12/12 columns mentioned
- Realistic tests: >85% (>96/113)
- Negations: >80% (>4/5)

---

## Deployment Checklist

- [ ] Fix #1 implemented (system prompt)
- [ ] Fix #2 implemented (remove reminder)
- [ ] Fix #3 implemented (add example)
- [ ] Simple context questions test passed
- [ ] Analysis questions test passed
- [ ] Mixed questions test passed
- [ ] Regression test passed (≥71.7%)
- [ ] Agent mentions columns when asked
- [ ] No tool call for simple metadata questions
- [ ] Tool call still works for analysis questions
- [ ] Ready for user approval

---

## Conclusion

**Investigation Complete**: ROOT CAUSE IDENTIFIED

**Problem**: System prompt tells agent to use tool for ALL "what" questions, even simple ones that could be answered from context.

**Solution**: Refine system prompt to distinguish:
- Simple metadata questions → Answer from context (fast)
- Complex analysis questions → Use tool (accurate)

**Confidence**: HIGH - Clear root cause, simple fix, low risk

**Next Step**: Get user approval to implement fixes

---

## Appendix: Investigation Timeline

1. ✅ Read system prompt → Found aggressive tool usage rule
2. ✅ Check test results → Found tool timeout evidence
3. ✅ Read agent.py → Verified data flow (columns ARE there)
4. ✅ Analyze prompt construction → Found conflicting instructions
5. ✅ Identify root cause → Prompt design issue
6. ✅ Design fixes → Refined system prompt + examples
7. ✅ Create testing plan → Comprehensive coverage
8. ⏳ **CURRENT**: Get approval before implementing

**Total Investigation Time**: ~2 hours
**Confidence Level**: 95% (clear evidence, reproducible issue, simple fix)
