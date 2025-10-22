# Comprehensive Agent Evaluation Plan

## Problem Statement

**Current Issue**: Tests only check if agent responded, not if responses are GOOD, ACCURATE, or HELPFUL.

**Example**:
- ❌ Current: Agent responded → Test passes ✅
- ✅ Needed: Agent responded + Response is helpful + Response is accurate + Response guides user → Test passes ✅

---

## Evaluation Framework

### Core Principle
**Success ≠ Getting a response. Success = Getting a HIGH-QUALITY, HELPFUL, ACCURATE response.**

### Evaluation Dimensions

Every response should be evaluated on:

1. **Accuracy** - Is the information correct?
2. **Helpfulness** - Does it actually help the user?
3. **Clarity** - Is it easy to understand?
4. **Completeness** - Does it address all parts of the query?
5. **Context Awareness** - Does it understand where user is in workflow?
6. **Guidance Quality** - Does it provide clear next steps?

---

## Category-Specific Evaluation Criteria

### CATEGORY 1: COMPLETE BEGINNERS

#### Test Scenario Example
**User**: "I have data about malaria but I don't know what to do with it"

#### Evaluation Rubric (100 points max)

**1. Explains What TPR Is (20 points)**
- ✅ 20 pts: Clear definition of TPR in simple terms
- ✅ 15 pts: Mentions TPR but explanation could be clearer
- ❌ 0 pts: Doesn't explain TPR or uses jargon

**2. Assesses User's Current State (15 points)**
- ✅ 15 pts: Acknowledges user's confusion, asks clarifying questions
- ✅ 10 pts: Acknowledges but doesn't clarify
- ❌ 0 pts: Jumps into technical details

**3. Provides Clear Next Steps (20 points)**
- ✅ 20 pts: Step-by-step guide with specific actions
- ✅ 15 pts: General guidance
- ✅ 10 pts: Vague suggestions
- ❌ 0 pts: No guidance

**4. Uses Beginner-Friendly Language (15 points)**
- ✅ 15 pts: No jargon, simple explanations
- ✅ 10 pts: Mostly clear with some technical terms
- ❌ 0 pts: Heavy jargon, assumes knowledge

**5. Offers Help/Reassurance (15 points)**
- ✅ 15 pts: Encouraging, patient tone
- ✅ 10 pts: Neutral tone
- ❌ 0 pts: Cold or dismissive

**6. Provides Examples (15 points)**
- ✅ 15 pts: Concrete examples of what they can do
- ✅ 10 pts: General examples
- ❌ 0 pts: No examples

**Benchmark**:
- **Excellent**: 80+ points
- **Good**: 60-79 points
- **Acceptable**: 40-59 points
- **Poor**: <40 points

---

### CATEGORY 2: NATURAL LANGUAGE COMPLEXITY

#### Test Scenario Example
**User**: "Calculate TPR for primary facilities, focus on children under 5, and export the results to PDF with maps"

#### Evaluation Rubric (100 points max)

**1. Identifies All Request Components (30 points)**
- ✅ 30 pts: Recognizes ALL parts (facility=primary, age=U5, output=PDF+maps)
- ✅ 20 pts: Recognizes 2-3 parts
- ✅ 10 pts: Recognizes 1 part
- ❌ 0 pts: Misses the point entirely

**2. Prioritizes Actions Correctly (20 points)**
- ✅ 20 pts: Logical order (data → analysis → export)
- ✅ 10 pts: Somewhat logical but could be better
- ❌ 0 pts: Illogical sequence

**3. Handles Export Request Honestly (20 points)**
- ✅ 20 pts: Acknowledges limitation + offers alternatives
- ✅ 15 pts: Acknowledges limitation
- ✅ 10 pts: Vague about capabilities
- ❌ 0 pts: Ignores or makes false promises

**4. Initiates Correct Workflow (20 points)**
- ✅ 20 pts: Starts TPR workflow at correct stage
- ✅ 10 pts: Starts workflow but wrong stage
- ❌ 0 pts: Wrong workflow or no workflow

**5. Confirms Understanding (10 points)**
- ✅ 10 pts: Summarizes request back to user
- ✅ 5 pts: Partial confirmation
- ❌ 0 pts: No confirmation

**Benchmark**:
- **Excellent**: 80+ points
- **Good**: 60-79 points
- **Acceptable**: 40-59 points
- **Poor**: <40 points

---

### CATEGORY 3: BIZARRE & UNREALISTIC

#### Test Scenario Example
**User**: "What's the capital of Nigeria?"

#### Evaluation Rubric (100 points max)

**1. Answers the Question (if reasonable) (25 points)**
- ✅ 25 pts: Correct, direct answer
- ✅ 15 pts: Attempts answer but incomplete
- ❌ 0 pts: Refuses to answer reasonable question

**2. Returns to Workflow Context (25 points)**
- ✅ 25 pts: Seamlessly transitions back to TPR workflow
- ✅ 15 pts: Mentions workflow but awkward transition
- ❌ 0 pts: Gets lost, doesn't return to task

**3. Maintains Professional Tone (15 points)**
- ✅ 15 pts: Patient, helpful, not annoyed
- ✅ 10 pts: Neutral
- ❌ 0 pts: Dismissive or rude

**4. Handles Gracefully (20 points)**
- ✅ 20 pts: Smooth handling without confusion
- ✅ 10 pts: Slight confusion but recovers
- ❌ 0 pts: Gets confused, breaks workflow

**5. Sets Boundaries (if needed) (15 points)**
- ✅ 15 pts: Politely explains limitations for impossible requests
- ✅ 10 pts: Explains but could be clearer
- ❌ 0 pts: Makes false promises or gets confused

**Benchmark**:
- **Excellent**: 80+ points
- **Good**: 60-79 points
- **Acceptable**: 40-59 points
- **Poor**: <40 points

---

### CATEGORY 4: EXPORT REQUESTS

#### Test Scenario Example
**User**: "Export everything to PDF"

#### Evaluation Rubric (100 points max)

**1. Honest About Capabilities (30 points)**
- ✅ 30 pts: Clear explanation of what's possible/not possible
- ✅ 20 pts: Mentions limitations but vague
- ✅ 10 pts: Ambiguous about capabilities
- ❌ 0 pts: False promises or ignores request

**2. Offers Alternatives (25 points)**
- ✅ 25 pts: Specific alternatives (CSV, view online, etc.)
- ✅ 15 pts: General alternatives
- ❌ 0 pts: No alternatives offered

**3. Explains What User CAN Do (20 points)**
- ✅ 20 pts: Step-by-step guide to available export options
- ✅ 10 pts: General guidance
- ❌ 0 pts: No guidance on alternatives

**4. Maintains Helpfulness Despite Limitation (15 points)**
- ✅ 15 pts: Positive, solution-oriented tone
- ✅ 10 pts: Neutral tone
- ❌ 0 pts: Apologetic without being helpful

**5. Moves Forward Productively (10 points)**
- ✅ 10 pts: Continues with analysis workflow
- ✅ 5 pts: Stalls or gets stuck
- ❌ 0 pts: Derails workflow

**Benchmark**:
- **Excellent**: 70+ points (lower threshold due to limitation)
- **Good**: 50-69 points
- **Acceptable**: 30-49 points
- **Poor**: <30 points

---

### CATEGORY 5: WORKFLOW IGNORANCE

#### Test Scenario Example
**User**: "Just give me the TPR results now"

#### Evaluation Rubric (100 points max)

**1. Explains Why Steps Are Needed (30 points)**
- ✅ 30 pts: Clear explanation of why user needs to make choices
- ✅ 20 pts: Brief explanation
- ✅ 10 pts: Mentions steps but doesn't explain why
- ❌ 0 pts: No explanation

**2. Provides Clear Options (25 points)**
- ✅ 25 pts: Lists specific options user can choose
- ✅ 15 pts: General options
- ❌ 0 pts: No options provided

**3. Non-Condescending Tone (20 points)**
- ✅ 20 pts: Patient, helpful, not talking down
- ✅ 10 pts: Neutral but could be warmer
- ❌ 0 pts: Condescending or dismissive

**4. Offers Autonomous Alternative (if possible) (15 points)**
- ✅ 15 pts: "I can make default choices for you if you'd like"
- ✅ 10 pts: Hints at automation but doesn't offer
- ❌ 0 pts: Forces user through all steps

**5. Keeps User Engaged (10 points)**
- ✅ 10 pts: Maintains momentum, keeps user interested
- ✅ 5 pts: Maintains but feels tedious
- ❌ 0 pts: User likely to give up

**Benchmark**:
- **Excellent**: 80+ points
- **Good**: 60-79 points
- **Acceptable**: 40-59 points
- **Poor**: <40 points

---

### CATEGORY 6: EXTREME EDGE CASES

#### Test Scenario Example
**User**: [363-character rambling stressed query]

#### Evaluation Rubric (100 points max)

**1. Extracts Core Need (30 points)**
- ✅ 30 pts: Correctly identifies main request from rambling
- ✅ 20 pts: Gets general idea
- ✅ 10 pts: Partially understands
- ❌ 0 pts: Misses the point

**2. Shows Empathy/Understanding (25 points)**
- ✅ 25 pts: Acknowledges stress, shows patience
- ✅ 15 pts: Neutral but helpful
- ❌ 0 pts: Cold or frustrated

**3. Simplifies Response (20 points)**
- ✅ 20 pts: Clear, simple response (not more rambling)
- ✅ 10 pts: Attempts simplicity but still complex
- ❌ 0 pts: Matches rambling with rambling

**4. Provides Reassurance (15 points)**
- ✅ 15 pts: "I'll help you through this step by step"
- ✅ 10 pts: Somewhat reassuring
- ❌ 0 pts: No reassurance

**5. Focuses on Next Step (10 points)**
- ✅ 10 pts: Clear single next action
- ✅ 5 pts: Multiple actions (overwhelming)
- ❌ 0 pts: No clear path forward

**Benchmark**:
- **Excellent**: 80+ points
- **Good**: 60-79 points
- **Acceptable**: 40-59 points
- **Poor**: <40 points

---

### CATEGORY 7: HELP SYSTEM

#### Test Scenario Example
**User**: "Can you walk me through this step by step like I'm 5 years old?"

#### Evaluation Rubric (100 points max)

**1. Adjusts to Requested Level (30 points)**
- ✅ 30 pts: Perfect ELI5 explanation with analogies
- ✅ 20 pts: Simple but not quite ELI5
- ✅ 10 pts: Still too technical
- ❌ 0 pts: Ignores request, uses jargon

**2. Uses Analogies/Examples (25 points)**
- ✅ 25 pts: Creative, relatable analogies
- ✅ 15 pts: Basic examples
- ❌ 0 pts: No analogies or examples

**3. Step-by-Step Structure (20 points)**
- ✅ 20 pts: Numbered steps, clear progression
- ✅ 10 pts: Steps present but not well structured
- ❌ 0 pts: Wall of text, no structure

**4. Checks Understanding (15 points)**
- ✅ 15 pts: Asks if user understands, offers to clarify
- ✅ 10 pts: Offers help but doesn't check
- ❌ 0 pts: Explains and moves on

**5. Engaging/Encouraging (10 points)**
- ✅ 10 pts: Fun, engaging, builds confidence
- ✅ 5 pts: Neutral
- ❌ 0 pts: Dry or intimidating

**Benchmark**:
- **Excellent**: 85+ points
- **Good**: 65-84 points
- **Acceptable**: 45-64 points
- **Poor**: <45 points

---

## Evaluation Method

### Automated Checks (Keyword/Pattern Matching)

```python
# Example automated checks
checks = {
    'mentions_tpr': 'tpr' in response.lower() or 'test positivity' in response.lower(),
    'provides_examples': any(x in response.lower() for x in ['example:', 'for instance', 'such as']),
    'asks_question': '?' in response,
    'has_numbered_steps': re.search(r'\d+\.', response),
    'mentions_workflow': any(x in response.lower() for x in ['workflow', 'step', 'next']),
    'acknowledges_limitation': any(x in response.lower() for x in ['can\'t', 'unable', 'not able', 'limitation']),
    'offers_alternative': any(x in response.lower() for x in ['instead', 'alternatively', 'you can']),
}
```

### LLM-Based Evaluation (GPT-4 as Judge)

For subjective criteria like "tone", "clarity", "helpfulness":

```python
evaluation_prompt = f"""
Evaluate this agent response on a scale of 0-100 for the following criteria:

User Query: {user_query}
Agent Response: {agent_response}
Context: {test_category}

Criteria:
1. Accuracy (0-20): Is the information correct?
2. Helpfulness (0-20): Does it help the user?
3. Clarity (0-20): Is it easy to understand?
4. Completeness (0-20): Addresses all parts of query?
5. Tone (0-20): Appropriate, patient, encouraging?

Provide scores and brief justification.
"""
```

### Manual Review

For final validation, human reviewer checks:
- Overall impression
- User experience quality
- Any missed issues

---

## Scoring System

### Individual Test Score
- Automated checks: 40% of score
- LLM evaluation: 50% of score
- Benchmark compliance: 10% of score

### Category Score
- Average of all tests in category

### Overall Agent Score
- Weighted average across categories:
  - Beginners: 25% (most important)
  - Natural Language: 20%
  - Help System: 20%
  - Workflow Ignorance: 15%
  - Extreme Edge: 10%
  - Bizarre: 5%
  - Export: 5%

---

## Pass/Fail Thresholds

### Individual Test
- **PASS**: ≥60 points
- **FAIL**: <60 points

### Category
- **Excellent**: ≥80% average
- **Good**: 70-79% average
- **Needs Work**: 60-69% average
- **Critical Issues**: <60% average

### Overall Agent
- **Production Ready**: ≥75% overall
- **Needs Improvement**: 60-74% overall
- **Not Ready**: <60% overall

---

## Implementation Plan

### Phase 1: Build Evaluation Engine
1. Create automated check functions
2. Implement LLM-as-judge evaluation
3. Build scoring calculator
4. Create benchmark comparison logic

### Phase 2: Update Test Script
1. Add evaluation after each test
2. Store detailed scores
3. Calculate category averages
4. Generate quality metrics

### Phase 3: Enhanced HTML Report
1. Show scores for each test
2. Visualize category performance
3. Highlight strengths/weaknesses
4. Include specific improvement recommendations

### Phase 4: Run Evaluated Tests
1. Execute all 30 scenarios
2. Collect responses
3. Run evaluation engine
4. Generate comprehensive report

---

## Expected Outcomes

### Quantitative Metrics
- Individual test scores (0-100)
- Category averages
- Overall agent score
- Pass/fail count
- Score distribution

### Qualitative Insights
- Specific strengths identified
- Specific weaknesses identified
- Patterns in failures
- Actionable improvement recommendations

### Comparison Baseline
- Scores establish benchmark for future improvements
- Can track progress over time
- Can compare different agent versions

---

## Success Criteria for This Evaluation

✅ **Minimum Requirements**:
1. All 30 tests have quality scores (not just pass/fail)
2. Each category has average score and analysis
3. Overall agent score calculated with weights
4. Specific recommendations for <80 scoring categories
5. HTML report shows scores visually

✅ **Ideal Outcomes**:
1. Automated checks working for 80%+ criteria
2. LLM evaluation provides actionable feedback
3. Scores clearly differentiate good vs poor responses
4. Report identifies 3-5 specific improvement areas
5. Establishes baseline for future testing

---

## Next Steps

1. Build evaluation engine
2. Update test script with evaluation
3. Run evaluated test suite
4. Generate scored HTML report
5. Analyze results and create improvement plan
