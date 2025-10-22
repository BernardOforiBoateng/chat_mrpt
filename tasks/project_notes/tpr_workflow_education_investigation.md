# TPR Workflow Education Investigation - Project Notes

## Date: 2025-09-24

### User Request
User asked to investigate adding explanations to the TPR calculation workflow so users understand why they need to follow the 3-step process and what each selection means.

### Investigation Approach

#### Files Examined
1. `app/data_analysis_v3/core/tpr_workflow_handler.py` - Main workflow logic
2. `app/data_analysis_v3/core/formatters.py` - User-facing messages
3. `app/data_analysis_v3/tools/tpr_analysis_tool.py` - TPR calculation tool
4. `app/survey/questions.py` - Cognitive assessment questions about TPR

### Key Findings

#### Current Implementation
- **Workflow**: State → Facility Level → Age Group → Calculate
- **Messages**: Focus on statistics and options, not explanations
- **Recommendations**: System marks certain options as "recommended" but doesn't explain why

#### Educational Gaps
1. **No TPR definition** - Users don't know what Test Positivity Rate means
2. **No process rationale** - Why 3 steps? Why not all at once?
3. **No context for choices** - What do facility levels represent?
4. **No interpretation guide** - What does 20% TPR mean for intervention?

### User Psychology Insights

#### Why Users Get Frustrated
- Forced to follow rigid process without understanding purpose
- Multiple steps feel arbitrary without context
- Technical terms (TPR, Primary/Secondary/Tertiary) undefined
- Results given without interpretation framework

#### What Users Need
- **Context before process** - Explain TPR importance first
- **Rationale for each step** - Why this matters for their goals
- **Decision support** - Help choosing between options
- **Actionable insights** - What to do with results

### Brainstormed Solutions

#### 1. Progressive Disclosure Pattern
```
Step 1: "Let me explain what we're calculating..."
Step 2: "Here's why we need your state..."
Step 3: "Facility levels matter because..."
Step 4: "Age groups are critical because..."
Result: "Here's what these numbers mean for you..."
```

#### 2. Interactive Education
- Detect "why" questions and provide contextual explanations
- Offer "Learn More" options at each step
- Include epidemiological context without overwhelming

#### 3. Visual Aids
- Already have bar charts for facility/age selection
- Could add infographics explaining TPR concept
- Show transmission intensity scales with results

### Implementation Strategy

#### Quick Wins
1. Add 2-3 sentence explanation at each step
2. Define TPR when workflow starts
3. Include interpretation scale with results

#### Medium-term
1. Create help system for "why" questions
2. Add tooltips for technical terms
3. Build knowledge base of common questions

#### Long-term
1. Interactive tutorial mode
2. Case studies from real interventions
3. Integration with WHO guidelines

### Technical Considerations

#### Where to Add Explanations
1. **formatters.py** - Embed in existing message templates
2. **New module** - `tpr_education.py` with explanation constants
3. **Workflow handler** - Detect educational queries

#### Maintaining User Flow
- Keep explanations concise (2-3 sentences)
- Make detailed explanations optional
- Use progressive disclosure
- Preserve existing workflow for experienced users

### Lessons for Product Design

#### Balance Between
- **Efficiency vs Education** - Power users want speed, new users need context
- **Simplicity vs Completeness** - Too much info overwhelms, too little confuses
- **Guidance vs Autonomy** - Recommendations help but shouldn't feel forced

#### Best Practices
1. **Explain the "why" before the "what"**
2. **Use domain language with definitions**
3. **Provide escape hatches for experts**
4. **Build trust through transparency**

### Cognitive Load Management

#### Current Issues
- All choices presented equally (no hierarchy)
- Technical terms without context
- Multiple decisions in sequence without breaks

#### Proposed Improvements
- Visual hierarchy (recommended prominently)
- Inline definitions for technical terms
- Checkpoint summaries between steps
- "Why this matters" context boxes

### Related Findings

#### Survey Module Integration
The survey asks users to explain TPR implications, but the workflow doesn't teach these concepts. This gap between assessment and education needs addressing.

#### Risk Analysis Connection
TPR feeds into risk analysis, but users don't understand this pipeline. Explaining TPR's role in the broader analysis would increase buy-in.

### Next Steps
1. Create `tpr_explanations.py` module with educational content
2. Modify formatters to include brief explanations
3. Add "why" question detection to workflow handler
4. Test with users to validate understanding

### Metrics for Success
- Fewer "why" questions in support
- Increased completion rate of TPR workflow
- Better user choices (selecting recommended options)
- Improved scores on TPR-related survey questions

### Risk Mitigation
- Keep core workflow unchanged (add education, don't modify flow)
- Make explanations optional/collapsible
- Test with both new and experienced users
- Maintain performance (don't slow down workflow)