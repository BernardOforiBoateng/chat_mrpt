# TPR Workflow UX Improvement Plan

**Date**: 2025-09-28
**Priority**: High
**Timeline**: Phase 1 (Immediate), Phase 2 (Next Sprint), Phase 3 (Future)

## Problem Statement
Users experience information overload during TPR workflow, receiving all data and visualizations immediately without context or progressive disclosure. This causes confusion, reduces completion rates, and creates a poor user experience.

## Solution Overview
Implement progressive disclosure pattern with user-controlled information depth, clear workflow orientation, and smart defaults based on expertise level.

---

## PHASE 1: Quick Wins (2-3 hours implementation)

### 1.1 Add Workflow Introduction
**File**: `tpr_workflow_handler.py` → `start_workflow()`

**Current**: Jumps directly to state/facility selection
**Proposed**: Add orientation message

```python
def start_workflow(self):
    # NEW: Add orientation
    intro_message = """
    ## Welcome to TPR Analysis! 🎯

    I'll guide you through 3 simple steps:
    1️⃣ Select State (if multiple states in data)
    2️⃣ Choose Facility Level
    3️⃣ Pick Age Group

    The analysis will calculate Test Positivity Rates to identify high-burden areas.

    Let's begin!
    """
```

### 1.2 Defer Visualizations
**File**: `tpr_workflow_handler.py`

**Current**: Auto-generate and display visualizations
**Proposed**: Show only on request

```python
def handle_facility_selection(self, user_query):
    # Check if user wants to see data
    if "show data" in user_query.lower() or "compare" in user_query.lower():
        # Generate visualizations
        facility_viz = self._build_facility_level_visualizations(facility_analysis)
    else:
        facility_viz = None  # Don't generate unless requested
```

### 1.3 Add Progress Indicators
**File**: `formatters.py`

**Add to each stage message**:
```python
def format_facility_selection(self, state, analysis):
    message = f"**Step 2 of 3: Select Facility Level**\n\n"
    # Rest of formatting...
```

### 1.4 Simplify Initial Prompts
**File**: `formatters.py`

**Current**: Shows all data immediately
**Proposed**: Start with simple choices

```python
def format_facility_selection_simple(self, state, analysis):
    return f"""
    Which health facilities would you like to analyze?

    1️⃣ **Primary** - Community health centers
    2️⃣ **Secondary** - District hospitals
    3️⃣ **Tertiary** - Specialist hospitals
    4️⃣ **All** - Combined analysis

    💡 Type 'help' for guidance or 'show data' for statistics
    """
```

---

## PHASE 2: Medium Improvements (1-2 days)

### 2.1 User Expertise Detection
**New Method**: `_determine_user_expertise()`

Logic:
- Check session history for previous TPR runs
- Count interactions in current session
- Look for expertise indicators (technical terms used)
- Return: 'novice', 'intermediate', 'expert'

### 2.2 Conditional Information Display
**Enhance**: All format methods

```python
def format_with_expertise(self, base_message, expertise_level):
    if expertise_level == 'novice':
        # Add explanations and recommendations
        message += "\n💡 Tip: Secondary facilities usually provide best coverage"
    elif expertise_level == 'expert':
        # Add shortcuts
        message += "\n⚡ Quick select: Press 2 for your usual choice"
    return message
```

### 2.3 Interactive Help System
**New Commands**:
- "help" - General guidance
- "why" - Explain current choice importance
- "compare" - Show comparison data
- "example" - Show sample selection

### 2.4 Preference Storage
**File**: `state_manager.py`

Add user preferences:
```python
preferences = {
    'display_mode': 'progressive',  # or 'full', 'minimal'
    'show_tips': True,
    'auto_show_viz': False,
    'expertise_level': 'auto'
}
```

---

## PHASE 3: Advanced Features (Future)

### 3.1 Truly Interactive Visualizations
- Make charts clickable for selection
- Hover for details
- Drill-down capabilities

### 3.2 Natural Language Navigation
- "Show me urban facilities only"
- "Compare primary and secondary"
- "What's the difference between age groups?"

### 3.3 Adaptive Interface
- Learn from user behavior
- Auto-adjust information depth
- Personalized recommendations

---

## Implementation Priority Matrix

| Feature | Impact | Effort | Priority |
|---------|--------|--------|----------|
| Workflow Introduction | High | Low | P0 - Immediate |
| Defer Visualizations | High | Low | P0 - Immediate |
| Progress Indicators | Medium | Low | P0 - Immediate |
| Simplified Prompts | High | Low | P0 - Immediate |
| Expertise Detection | Medium | Medium | P1 - Next Sprint |
| Interactive Help | Medium | Medium | P1 - Next Sprint |
| Preference Storage | Low | Medium | P2 - Future |
| Interactive Viz | High | High | P2 - Future |

---

## Success Metrics

### Immediate Measures (Phase 1)
- Completion rate increases from ~60% to >70%
- Average time per stage reduces by 30%
- User questions during workflow reduce by 50%

### Long-term Measures (Phase 2-3)
- User satisfaction score >4.5/5
- 90%+ workflow completion rate
- <15 seconds average decision time
- <5% error rate in selections

---

## Risk Mitigation

### Potential Issues:
1. **Users skip important information**
   - Mitigation: Require acknowledgment for critical data

2. **Expert users find it too slow**
   - Mitigation: Add "express mode" option

3. **Visualizations needed for decision**
   - Mitigation: Auto-show for certain scenarios

---

## Testing Plan

### Phase 1 Testing (Before Deploy):
1. Internal team testing (30 mins)
2. Check all pathways work
3. Verify no breaking changes
4. Test with/without visualizations

### Phase 2 Testing:
1. A/B test with user groups
2. Collect completion metrics
3. Survey for satisfaction
4. Iterate based on feedback

---

## Rollback Plan
If issues arise:
1. Keep original methods as fallback
2. Add feature flag for progressive disclosure
3. Can revert via config without code change

---

## Code Changes Summary

### Files to Modify:
1. `tpr_workflow_handler.py` (4 methods)
2. `formatters.py` (3 methods)
3. `system_prompt.py` (1 update)
4. `state_manager.py` (1 addition)

### New Files:
- None for Phase 1

### Estimated Lines Changed:
- Phase 1: ~150 lines
- Phase 2: ~400 lines
- Phase 3: ~800 lines

---

## Approval Checklist

- [ ] Review with team
- [ ] Confirm Phase 1 scope
- [ ] Approve testing approach
- [ ] Set success metrics
- [ ] Schedule deployment

---

## Next Steps
1. Get approval on Phase 1 approach
2. Implement quick wins (2-3 hours)
3. Test internally
4. Deploy to staging
5. Monitor metrics
6. Plan Phase 2 based on results