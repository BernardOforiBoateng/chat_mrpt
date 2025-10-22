# Clear Requirements Analysis

## What We Have (2 Parts)

### Part 1: General Data Analysis Agent
- Should work for ANY data (not just health)
- Users want to explore, correlate, do statistical analysis
- Needs to be EFFICIENT like the original
- BUT needs interpretation (not raw output)

### Part 2: TPR Analysis Module ✅ 
- **THIS IS PERFECT - DON'T TOUCH**
- Leads to risk analysis
- Working well

## What's Working Well

1. **Column Sanitization** ✅
   - Needed for messy data with special characters
   - Keep this

2. **TPR Module** ✅
   - Perfect as is
   - Keep separate

3. **Interpretation Concept** ✅
   - Users need explanations, not raw numbers
   - Keep but simplify

## Current Problems with Agent

1. **Hallucination**: Agent makes up "Facility A, B, C" instead of real names
2. **Incomplete Results**: "Top 10" only shows 1-3 items
3. **Over-Complex**: 3000+ lines when original is 200 lines
4. **Too Domain-Specific**: Hardcoded for health data

## The Real Question

**How can we achieve the simplicity/effectiveness of the original WHILE keeping interpretation?**

The original:
- Simple: Execute code → Return output
- Always works because it's just running Python

Our needs:
- Execute code → Return output → **Interpret for users**
- The interpretation layer is where problems happen

## Key Insight

The original doesn't fail because:
- It ONLY executes code
- The code directly prints results
- No room for hallucination

We fail because:
- We execute code
- Then LLM tries to "rewrite" the results
- LLM makes things up during rewriting

## What I Should Analyze

1. **Can we trim down the agent to be simple like original?**
   - What's essential vs bloat?
   - What's causing complexity?

2. **How to keep interpretation without hallucination?**
   - Can interpretation be based on actual output?
   - How to prevent LLM from inventing?

3. **How to make it general (not health-specific)?**
   - Remove hardcoded patterns
   - Make domain-agnostic

4. **What exactly to keep vs remove?**
   - Core execution (keep)
   - Interpretation (keep but fix)
   - Complex validation (remove?)
   - Response formatting (simplify?)

## Questions for Clarification

1. **Interpretation Level**: When you say interpretation, do you mean:
   - Explaining what the numbers mean?
   - Providing context and insights?
   - Suggesting next steps?
   - All of the above?

2. **User Types**: The agent should work for:
   - Data analysts?
   - Business users?
   - Researchers?
   - Anyone with data?

3. **Output Format**: Should the output be:
   - Natural language explanation with embedded results?
   - Results first, then explanation?
   - Interactive Q&A style?

## Proposed Approach (for discussion)

### Option A: Structured Output + Simple Interpretation
```
Code executes → Structured output (JSON-like) → Simple template-based interpretation
```
- Pros: No hallucination possible
- Cons: Less flexible interpretation

### Option B: Enhanced Code Output + LLM Interpretation
```
Code prints detailed results → LLM explains what it sees (not generates)
```
- Pros: Flexible interpretation
- Cons: Still risk of hallucination

### Option C: Hybrid Approach
```
Code returns data + metadata → Interpretation uses metadata → No invention
```
- Pros: Safe and flexible
- Cons: Slightly more complex

## What Needs Agreement

Before implementing anything, we need to agree on:

1. **How much to simplify?**
   - Remove 50% of code?
   - Remove 80% of code?
   - Just fix critical parts?

2. **Interpretation approach**
   - Template-based (safe but rigid)?
   - LLM-based (flexible but risky)?
   - Hybrid (balanced)?

3. **General vs Specific**
   - Completely generic agent?
   - Health-aware but not health-only?
   - Plugin architecture?

4. **Priority**
   - Fix hallucination first?
   - Fix "top 10" issue first?
   - Simplify first?

## My Understanding

You want:
1. A simple, efficient agent (like original)
2. That provides interpretation (unlike original)
3. That works for any data analysis (not just health)
4. That doesn't hallucinate or truncate results
5. Keep TPR module separate and untouched
6. Keep column sanitization for messy data

Is this correct? What am I missing?