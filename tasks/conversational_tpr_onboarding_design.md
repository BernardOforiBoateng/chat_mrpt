# Conversational TPR Onboarding - Design Document

**Date**: 2025-09-30
**Objective**: Create truly conversational TPR workflow with education, confirmation, and guided steps
**Status**: DESIGN PHASE

---

## Vision

Transform TPR workflow from **rigid automation** to **conversational guidance**:

**Old Way** (Broken):
```
User uploads → Auto-detect → Start workflow → Force through steps
```

**New Way** (Conversational):
```
User uploads → Ask what they want → Show data overview → Explain TPR workflow
→ Answer questions → Confirm readiness → Guide through steps
```

---

## Complete Conversational Flow

### Stage 1: Initial Upload (Existing)

```
[User uploads kaduna_tpr_cleaned.csv]

System: ✓ File uploaded successfully
```

**State**: `uploaded`, no workflow active

---

### Stage 2: User Intent Detection

```
User: "calculate tpr"
       OR "run tpr analysis"
       OR "analyze test positivity"
       OR "I want to do tpr"
```

**System Response** (Stage 2a - Acknowledge & Ask):

```
Great! I can help you with Test Positivity Rate (TPR) analysis.

First, let me understand your data better. What kind of analysis are you looking to do?

• TPR Analysis - Calculate malaria test positivity rates by facility and age group
• General Data Exploration - Summary statistics and visualizations
• Custom Analysis - Tell me what you're interested in

Or just say "show me my data" to see an overview first.
```

**State**: `intent_gathering`

---

### Stage 3: Data Overview (Regardless of Answer)

```
User: "tpr analysis"
       OR "show me my data"
       OR "what do I have?"
```

**System Response** (Stage 3a - Data Overview):

```
# Your Dataset Overview

**File**: kaduna_tpr_cleaned.csv
**Size**: 4,890 rows × 25 columns

### What You Have:

**Geographic Coverage**:
• State: Kaduna
• LGAs: 23 local government areas
• Wards: 255 wards
• Facilities: 489 health facilities

**Facility Breakdown**:
• Primary facilities: 312 (63.8%)
• Secondary facilities: 156 (31.9%)
• Tertiary facilities: 21 (4.3%)

**Test Data**:
• Total tests conducted: 89,456
• RDT tests: 67,234
• Microscopy tests: 22,222
• Coverage period: January - December 2024

**Age Groups**:
• Children under 5 years (U5)
• People 5 years and older (O5)
• Pregnant women (PW)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

This looks like **malaria test data** suitable for TPR analysis!

Would you like me to explain what TPR analysis involves?
```

**State**: `data_overview_shown`

---

### Stage 4: TPR Explanation (If User Confirms)

```
User: "yes, explain"
       OR "what is tpr?"
       OR "tell me more"
       OR "yes"
```

**System Response** (Stage 4a - TPR Explanation):

```
# What is Test Positivity Rate (TPR) Analysis?

**TPR Definition**:
The percentage of malaria tests that come back positive. It's a key indicator for:
• Disease burden in the population
• Targeting intervention resources
• Monitoring malaria trends

**Example**:
If 100 people are tested and 15 test positive, TPR = 15%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**What We'll Calculate Together**:

1. **By Facility Type**: TPR for primary, secondary, and tertiary facilities
2. **By Age Group**: TPR for children <5, people ≥5, and pregnant women
3. **Geographic Patterns**: Which wards/LGAs have highest TPR

**The Process** (3-5 minutes):

**Step 1**: Choose facility type (primary, secondary, tertiary, or all)
**Step 2**: Choose age group (under 5, over 5, pregnant women, or all)
**Step 3**: System calculates TPR for your selection
**Step 4**: View results with visualizations
**Step 5**: Ready for risk analysis!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Questions?**
Feel free to ask me anything about:
• What TPR means
• Why we need facility and age group selections
• What the results will look like
• How this connects to risk analysis

Or say **"let's start"** when you're ready to begin!
```

**State**: `tpr_explained`, `awaiting_confirmation`

---

### Stage 4b: Handle User Questions (Optional)

```
User: "why do we need to select facility type?"
```

**System Response**:

```
Great question!

**Why Facility Type Matters**:

Different facility types serve different populations and have different capacities:

• **Primary facilities** (health centers):
  - Serve local communities
  - First point of contact
  - Higher patient volume, lower complexity

• **Secondary facilities** (district hospitals):
  - Referral centers for LGAs
  - Handle more complex cases
  - More diagnostic capacity

• **Tertiary facilities** (specialist hospitals):
  - Serve entire states/regions
  - Handle severe/complicated cases
  - Highest diagnostic accuracy

**Impact on TPR**:
Tertiary facilities often show HIGHER TPR because they receive referred cases
(people already suspected of having malaria). Primary facilities show the
"community baseline" TPR.

Analyzing them separately gives you a **complete picture** of disease burden
across the health system.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Any other questions, or ready to start?
```

**State**: Still `tpr_explained`, `awaiting_confirmation`

---

### Stage 5: Workflow Confirmation

```
User: "let's start"
       OR "I'm ready"
       OR "begin"
       OR "start the analysis"
```

**System Response** (Stage 5a - Workflow Start):

```
Perfect! Let's calculate Test Positivity Rates for your Kaduna malaria data.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Step 1 of 2: Select Facility Type

Which health facilities should we analyze?

**Your options**:

• **primary** (312 facilities) - Community health centers
• **secondary** (156 facilities) - District hospitals
• **tertiary** (21 facilities) - Specialist centers
• **all** (489 facilities) - Combined analysis across all levels

💡 *Tip: Start with 'all' to see overall patterns, then drill down into
   specific facility types for targeted insights.*

Which would you like to analyze?
```

**State**: `TPR_FACILITY_LEVEL` (workflow active)

---

### Stage 6: Facility Selection

```
User: "all"
       OR "all facilities"
       OR "combined"
       OR "4"
```

**System Response** (Stage 6a - Facility Confirmed):

```
✓ Selected: **All facilities** (489 facilities across primary, secondary, and tertiary)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# Step 2 of 2: Select Age Group

Which population group should we analyze?

**Your options**:

• **u5** - Children under 5 years (highest risk group)
• **o5** - People 5 years and older (excluding pregnant women)
• **pw** - Pregnant women (vulnerable group)
• **all** - All age groups combined

💡 *Tip: Children under 5 have the highest malaria burden in most regions.*

Which age group?
```

**State**: `TPR_AGE_GROUP` (workflow active, facility selected)

---

### Stage 7: Age Selection & Calculation

```
User: "u5"
       OR "children under 5"
       OR "kids"
```

**System Response** (Stage 7a - Calculating):

```
✓ Selected: **Children under 5 years (U5)**

Calculating Test Positivity Rate for:
• Facilities: All (489 facilities)
• Age Group: Children under 5 years
• Coverage: 255 wards across 23 LGAs

[Processing...]
```

**System Response** (Stage 7b - Results):

```
# TPR Analysis Results

## Overall Test Positivity Rate: 18.7%

**What this means**: Out of every 100 children under 5 tested for malaria,
about 19 tested positive.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

### Key Findings:

**Tests Conducted**: 34,567 children under 5 tested
**Positive Cases**: 6,464 confirmed malaria cases
**Test Positivity Rate**: 18.7%

**Breakdown by Facility Type**:
• Primary facilities: 17.2% TPR (lower - community baseline)
• Secondary facilities: 21.3% TPR (moderate - referral cases)
• Tertiary facilities: 28.9% TPR (higher - severe cases)

**Geographic Hotspots** (Top 5 Wards by TPR):
1. Tudun Wada North - 34.2% TPR
2. Barnawa - 31.8% TPR
3. Kakuri - 29.4% TPR
4. Sabon Gari - 27.1% TPR
5. Rigasa - 25.6% TPR

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Visualization**: [Interactive map showing TPR by ward]

**Downloads Available**:
• TPR_results_by_ward.csv
• TPR_results_by_facility.csv

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Next Steps**:

Your TPR data is now ready for **risk analysis**!

The risk analysis will:
• Combine TPR with environmental factors
• Identify high-risk areas for intervention
• Prioritize resource allocation

Say **"start risk analysis"** to continue, or ask me questions about these results.
```

**State**: `TPR_COMPLETE`, `ready_for_risk_analysis`

---

## Implementation Strategy

### Phase 1: Core Conversational States

Add new conversation stages to state manager:

```python
class ConversationStage(Enum):
    INITIAL = "initial"

    # NEW: Conversational onboarding stages
    INTENT_GATHERING = "intent_gathering"
    DATA_OVERVIEW_SHOWN = "data_overview_shown"
    TPR_EXPLAINED = "tpr_explained"
    AWAITING_WORKFLOW_CONFIRMATION = "awaiting_workflow_confirmation"

    # Existing workflow stages
    TPR_FACILITY_LEVEL = "tpr_facility_level"
    TPR_AGE_GROUP = "tpr_age_group"
    TPR_CALCULATING = "tpr_calculating"
    TPR_COMPLETE = "tpr_complete"
```

### Phase 2: Intent Detection System

Replace hard "calculate tpr" keyword matching with intent classifier:

```python
def detect_user_intent(user_query: str, current_stage: ConversationStage) -> str:
    """
    Detect user intent based on query and current conversation stage.

    Returns:
        - "start_tpr_workflow" - User wants to begin TPR
        - "show_data_overview" - User wants to see data summary
        - "ask_question" - User has questions about TPR/process
        - "confirm_ready" - User confirms ready to start workflow
        - "select_facility" - User selecting facility type
        - "select_age" - User selecting age group
    """
    query_lower = user_query.lower()

    # Intent: Start TPR workflow
    if any(kw in query_lower for kw in [
        'calculate tpr', 'run tpr', 'tpr analysis', 'test positivity'
    ]):
        return "start_tpr_workflow"

    # Intent: Show data overview
    if any(kw in query_lower for kw in [
        'show data', 'what do i have', 'data overview', 'summary'
    ]):
        return "show_data_overview"

    # Intent: Confirm readiness (context-dependent)
    if current_stage == ConversationStage.AWAITING_WORKFLOW_CONFIRMATION:
        if any(kw in query_lower for kw in [
            'start', 'begin', 'ready', "let's go", "let's start", 'yes'
        ]):
            return "confirm_ready"

    # Intent: Ask question
    if '?' in user_query or any(kw in query_lower for kw in [
        'what is', 'why', 'how', 'explain', 'tell me'
    ]):
        return "ask_question"

    return "unknown"
```

### Phase 3: Data Overview Generator

```python
def generate_data_overview(self, df: pd.DataFrame) -> str:
    """
    Generate comprehensive, conversational data overview.
    """
    overview = "# Your Dataset Overview\n\n"

    # Basic stats
    overview += f"**File**: {self.filename}\n"
    overview += f"**Size**: {len(df):,} rows × {len(df.columns)} columns\n\n"

    # Geographic coverage
    if 'State' in df.columns:
        overview += "### What You Have:\n\n"
        overview += "**Geographic Coverage**:\n"
        overview += f"• State: {df['State'].iloc[0]}\n"

        if 'LGA' in df.columns:
            overview += f"• LGAs: {df['LGA'].nunique()} local government areas\n"

        if 'WardName' in df.columns:
            overview += f"• Wards: {df['WardName'].nunique()} wards\n"

        if 'HealthFacility' in df.columns:
            overview += f"• Facilities: {df['HealthFacility'].nunique()} health facilities\n"

    # Facility breakdown
    if 'FacilityLevel' in df.columns or 'FacilityType' in df.columns:
        fac_col = 'FacilityLevel' if 'FacilityLevel' in df.columns else 'FacilityType'
        facility_counts = df[fac_col].value_counts()

        overview += "\n**Facility Breakdown**:\n"
        total_facilities = len(df)
        for level, count in facility_counts.items():
            pct = (count / total_facilities) * 100
            overview += f"• {level.capitalize()} facilities: {count} ({pct:.1f}%)\n"

    # Test data detection
    test_cols = [col for col in df.columns if any(kw in col.lower() for kw in ['test', 'rdt', 'microscopy'])]
    if test_cols:
        overview += "\n**Test Data**:\n"

        # Calculate total tests
        for col in test_cols:
            if 'tested' in col.lower() and 'positive' not in col.lower():
                try:
                    total_tests = df[col].sum()
                    overview += f"• Total tests conducted: {int(total_tests):,}\n"
                    break
                except:
                    pass

        overview += "• Test types: "
        if any('rdt' in col.lower() for col in test_cols):
            overview += "RDT, "
        if any('microscopy' in col.lower() for col in test_cols):
            overview += "Microscopy"
        overview += "\n"

    # Age groups
    age_indicators = ['<5', '5yrs', 'pw', 'preg']
    if any(any(ind in col.lower() for ind in age_indicators) for col in df.columns):
        overview += "\n**Age Groups**:\n"
        if any('<5' in col or 'u5' in col.lower() for col in df.columns):
            overview += "• Children under 5 years (U5)\n"
        if any('≥5' in col or '>5' in col or 'o5' in col.lower() for col in df.columns):
            overview += "• People 5 years and older (O5)\n"
        if any('pw' in col.lower() or 'preg' in col.lower() for col in df.columns):
            overview += "• Pregnant women (PW)\n"

    # Assessment
    overview += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"

    # Determine data type
    has_facility = any('facility' in col.lower() for col in df.columns)
    has_test = any(kw in ' '.join(df.columns).lower() for kw in ['test', 'rdt', 'microscopy'])

    if has_facility and has_test:
        overview += "This looks like **malaria test data** suitable for TPR analysis!\n\n"
        overview += "Would you like me to explain what TPR analysis involves?"
    else:
        overview += "I can help you explore this data. What would you like to know?"

    return overview
```

### Phase 4: TPR Explanation Templates

```python
TPR_EXPLANATION = """
# What is Test Positivity Rate (TPR) Analysis?

**TPR Definition**:
The percentage of malaria tests that come back positive. It's a key indicator for:
• Disease burden in the population
• Targeting intervention resources
• Monitoring malaria trends

**Example**:
If 100 people are tested and 15 test positive, TPR = 15%

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**What We'll Calculate Together**:

1. **By Facility Type**: TPR for primary, secondary, and tertiary facilities
2. **By Age Group**: TPR for children <5, people ≥5, and pregnant women
3. **Geographic Patterns**: Which wards/LGAs have highest TPR

**The Process** (3-5 minutes):

**Step 1**: Choose facility type (primary, secondary, tertiary, or all)
**Step 2**: Choose age group (under 5, over 5, pregnant women, or all)
**Step 3**: System calculates TPR for your selection
**Step 4**: View results with visualizations
**Step 5**: Ready for risk analysis!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Questions?**
Feel free to ask me anything about:
• What TPR means
• Why we need facility and age group selections
• What the results will look like
• How this connects to risk analysis

Or say **"let's start"** when you're ready to begin!
"""

# Q&A responses
TPR_QA_RESPONSES = {
    "what is tpr": """
    TPR (Test Positivity Rate) is the percentage of malaria tests that return positive.

    **Formula**: (Positive tests ÷ Total tests) × 100

    **What it tells us**:
    • High TPR (>20%) = High disease burden, more cases than testing capacity
    • Medium TPR (10-20%) = Moderate burden, adequate testing
    • Low TPR (<10%) = Low burden OR over-testing

    It helps health officials decide where to focus malaria control efforts.
    """,

    "why facility type": """
    Great question!

    **Why Facility Type Matters**:

    Different facility types serve different populations:

    • **Primary facilities** (health centers):
      - Community baseline TPR
      - First point of contact

    • **Secondary facilities** (district hospitals):
      - Referral cases (often higher TPR)
      - More diagnostic capacity

    • **Tertiary facilities** (specialist hospitals):
      - Severe cases (highest TPR)
      - Highest accuracy tests

    Analyzing separately gives you a **complete picture** across the health system.
    """,

    "why age group": """
    Excellent question!

    **Why Age Groups Matter**:

    Malaria affects different age groups differently:

    • **Children <5**: Highest risk, most vulnerable
    • **Adults ≥5**: Lower risk, better immunity
    • **Pregnant women**: Vulnerable, affects mother + baby

    Different interventions target different groups, so we need separate TPR for:
    • Targeting bed nets (children vs. pregnant women)
    • Drug distribution strategies
    • Vaccination priorities
    """
}
```

### Phase 5: Conversational State Machine

```python
async def handle_conversational_flow(
    self,
    user_query: str,
    current_stage: ConversationStage
) -> Dict[str, Any]:
    """
    Handle conversational TPR onboarding flow.
    """
    intent = detect_user_intent(user_query, current_stage)

    # STAGE: Initial or Intent Gathering
    if current_stage == ConversationStage.INITIAL:
        if intent == "start_tpr_workflow":
            # Show data overview first
            df = self.load_data()
            overview = self.generate_data_overview(df)

            self.state_manager.update_workflow_stage(
                ConversationStage.DATA_OVERVIEW_SHOWN
            )

            return {
                "response": overview,
                "status": "success",
                "stage": "DATA_OVERVIEW_SHOWN"
            }

    # STAGE: Data Overview Shown
    elif current_stage == ConversationStage.DATA_OVERVIEW_SHOWN:
        if intent == "ask_question" or "yes" in user_query.lower() or "explain" in user_query.lower():
            # User wants TPR explanation
            self.state_manager.update_workflow_stage(
                ConversationStage.TPR_EXPLAINED
            )

            return {
                "response": TPR_EXPLANATION,
                "status": "success",
                "stage": "TPR_EXPLAINED"
            }

    # STAGE: TPR Explained (Q&A or Ready)
    elif current_stage == ConversationStage.TPR_EXPLAINED:
        if intent == "ask_question":
            # Answer specific questions
            answer = self.answer_tpr_question(user_query)
            return {
                "response": answer + "\n\nAny other questions, or ready to start?",
                "status": "success",
                "stage": "TPR_EXPLAINED"
            }

        elif intent == "confirm_ready":
            # Start actual workflow
            return self.handle_facility_selection_prompt()

    # STAGE: Workflow Active (existing logic)
    elif current_stage == ConversationStage.TPR_FACILITY_LEVEL:
        # Use existing fuzzy matching
        matched_facility = self.fuzzy_match_facility(user_query)
        if matched_facility:
            return self.handle_facility_selection(matched_facility)

    # ... continue with existing workflow logic
```

---

## Key Benefits

### 1. Educational
- User learns WHAT TPR is
- User learns WHY selections matter
- User learns HOW process works

### 2. Conversational
- Feels like talking to expert
- Can ask questions anytime
- Natural language throughout

### 3. Flexible
- User can skip to overview
- User can ask questions before committing
- User controls pace

### 4. Transparent
- Clear expectations ("3-5 minutes")
- Shows data first
- Explains each step

### 5. Test-Friendly
- TEST 3 passes because overview always shown
- TEST 11 unaffected (still needs timeout fix)
- Actually IMPROVES test coverage (more robust)

---

## Implementation Timeline

| Phase | Task | Time | Cumulative |
|-------|------|------|------------|
| 1 | Add conversation stages | 10 min | 10 min |
| 2 | Implement intent detection | 15 min | 25 min |
| 3 | Build data overview generator | 20 min | 45 min |
| 4 | Add TPR explanation templates | 15 min | 60 min |
| 5 | Integrate conversational flow | 30 min | 90 min |
| 6 | Test locally | 15 min | 105 min |
| 7 | Deploy & validate | 15 min | 120 min |

**Total**: ~2 hours

---

## Testing Strategy

### Test Conversation 1: Full Onboarding

```
[Upload file]
User: "calculate tpr"
  → System: Data overview + "Would you like me to explain TPR?"

User: "yes"
  → System: Full TPR explanation + "Questions or ready to start?"

User: "why do we need age groups?"
  → System: Age group explanation + "Any other questions?"

User: "let's start"
  → System: Facility selection prompt

User: "all"
  → System: Age group selection prompt

User: "children under 5"
  → System: TPR results + visualizations
```

### Test Conversation 2: Quick Path

```
[Upload file]
User: "show me my data"
  → System: Data overview

User: "start tpr"
  → System: "Would you like explanation?" (implicitly offered in overview)

User: "no, let's begin"
  → System: Facility selection prompt

[Continue workflow]
```

### Test Conversation 3: Question-Heavy

```
[Upload file]
User: "what is tpr?"
  → System: TPR explanation

User: "why facility types?"
  → System: Facility type explanation

User: "ok I'm ready"
  → System: Facility selection prompt
```

---

## This Solves

✅ **TEST 3**: Overview ALWAYS shown, all keywords present
✅ **User Confusion**: Clear explanation of process
✅ **Auto-detection Issues**: No auto-detection needed!
✅ **Conversational Feel**: Truly interactive experience
✅ **Educational Value**: Users learn, not just click

**Next**: Implement this design?
