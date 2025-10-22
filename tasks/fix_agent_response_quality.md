# Fix Data Analysis V3 Agent Response Quality Issues

## Problem Analysis
The agent has critical response quality issues despite technical infrastructure working:
1. **Top N queries** only showing 1 item instead of N requested
2. **Hallucinating facility names** (Facility A, B, C) instead of real data
3. **Impossible values** not validated (1168.4% positivity rate)
4. **Vague summaries** without actual data
5. **Response truncation** limiting insights

## Root Causes Identified
1. **Response formatter limiting output** - `insights[:5]` truncation in response_formatter.py
2. **No validation layer** for data sanity checks
3. **Agent not following prompt instructions** despite explicit rules
4. **Token limits** potentially truncating LLM responses
5. **No hallucination prevention** when data unavailable

## Implementation Plan

### Phase 1: Research & Analysis ✅
- [x] Research online solutions for LLM truncation issues
- [x] Research hallucination prevention techniques  
- [x] Research data validation best practices
- [x] Analyze codebase to find truncation points

### Phase 2: Fix Response Truncation
- [ ] Remove or increase insight limit in response_formatter.py
- [ ] Add explicit loop completion for "top N" queries
- [ ] Increase max_tokens in LLM configuration
- [ ] Add result completeness validation

### Phase 3: Implement Hallucination Prevention
- [ ] Add data grounding checks before output
- [ ] Implement "I don't know" responses when data unavailable
- [ ] Add facility name validation against actual data
- [ ] Create fallback for missing data scenarios

### Phase 4: Add Data Validation Layer
- [ ] Implement percentage validation (0-100% range)
- [ ] Add sanity checks for common metrics
- [ ] Create error flagging for impossible values
- [ ] Add automatic recalculation for erroneous data

### Phase 5: Strengthen Prompt Engineering
- [ ] Add stronger enforcement rules in system prompt
- [ ] Implement validation checklist before response
- [ ] Add explicit counting enforcement for "top N"
- [ ] Create structured output format requirements

### Phase 6: Testing & Validation
- [ ] Update user simulation with validation checks
- [ ] Test all 20 queries for completeness
- [ ] Verify no hallucinations occur
- [ ] Confirm data validation working

## Technical Solutions

### 1. Response Completeness Fix
```python
# In response_formatter.py
def _format_insights(insights: List[str]) -> str:
    # Remove limit or make configurable
    MAX_INSIGHTS = 100  # Was 5
    for insight in insights[:MAX_INSIGHTS]:
        ...
```

### 2. Top N Query Fix
```python
# In system prompt
"When executing 'top N' queries:
1. MUST use df.nlargest(N, column) or similar
2. MUST iterate through ALL N results
3. MUST format as numbered list 1 to N
4. If fewer than N exist, state exact count found"
```

### 3. Hallucination Prevention
```python
# Add to executor.py
def validate_facility_names(output, actual_facilities):
    if "Facility A" in output or "Facility B" in output:
        raise ValidationError("Generic facility names detected")
    # Verify all facility names exist in data
```

### 4. Data Validation
```python
# Add validation utility
def validate_percentages(value, metric_name):
    if 0 <= value <= 100:
        return value
    else:
        return f"ERROR: {metric_name} shows {value}% which is impossible"
```

### 5. LLM Configuration
```python
# In agent.py initialization
self.model = ChatOpenAI(
    model="gpt-4",
    temperature=0,
    max_tokens=4000,  # Increase from default
    model_kwargs={"top_p": 0.95}
)
```

## Success Criteria
- [ ] "Top 10" query returns exactly 10 items
- [ ] No hallucinated facility names (Facility A, B, C)
- [ ] Percentages validated to 0-100% range
- [ ] Summaries contain actual data, not descriptions
- [ ] Pattern analysis shows real patterns found
- [ ] 95%+ success rate on user simulation

## Files to Modify
1. `app/data_analysis_v3/formatters/response_formatter.py` - Remove truncation
2. `app/data_analysis_v3/prompts/system_prompt.py` - Strengthen rules
3. `app/data_analysis_v3/core/executor.py` - Add validation layer
4. `app/data_analysis_v3/core/agent.py` - Increase token limits
5. `app/data_analysis_v3/tools/python_tool.py` - Add grounding checks

## Testing Strategy
1. Fix one issue at a time
2. Test with quick_simulation_test.py after each fix
3. Run full simulation only after all fixes
4. Deploy to staging for final validation

## Risk Mitigation
- Create backups before modifying
- Test on local first
- Deploy to staging before production
- Monitor for performance impact