# Updated TPR Workflow Plan - Simplified 3-Step Process

## Date: 2025-08-13

## Overview
Simplified TPR workflow based on production system - only 3 questions, no test method selection.

## Correct TPR Workflow (3 Steps)

### Step 1: State Selection
**When:** After user chooses option 1 (TPR) from initial menu
**What to show:**
```
Great! I'll guide you through the TPR calculation process.

**Which state would you like to analyze?**

Based on your data, I found:

1. **Adamawa**
   - 834 health facilities
   - 15,234 total tests recorded
   - Data completeness: 89%

2. **Kwara**
   - 785 health facilities  
   - 14,567 total tests recorded
   - Data completeness: 82%

3. **Osun**
   - 837 health facilities
   - 15,877 total tests recorded
   - Data completeness: 86%

Please select a state (1, 2, or 3):
```

### Step 2: Facility Level Selection
**When:** After state is selected
**What to show:**
```
You selected Adamawa State.

**Which facility level would you like to analyze?**

1. **All Facilities** ⭐ Recommended
   - 834 total facilities
   - Complete geographic coverage
   - Mix of urban (23%) and rural (77%)

2. **Primary Health Centers**
   - 687 facilities (82% of total)
   - Community-level care
   - Predominantly rural

3. **Secondary Facilities**
   - 125 facilities (15% of total)
   - General hospitals
   - District-level care

4. **Tertiary Facilities**
   - 22 facilities (3% of total)
   - Teaching hospitals
   - Specialized care

Which level? (1-4):
```

### Step 3: Age Group Selection
**When:** After facility level is selected
**What to show:**
```
Analyzing All Facilities in Adamawa State.

**Which age group should I calculate TPR for?**

Based on your data:

1. **All Age Groups Combined** ⭐ Recommended
   - 15,234 tests available (100% coverage)
   - Most comprehensive view for planning
   - Overall positivity: 26.5%

2. **Under 5 Years** 👶
   - 6,093 tests available (40% of total)
   - Highest risk group: 34.2% positivity
   - Critical for child health programs

3. **Over 5 Years**
   - 7,156 tests available (47% of total)
   - Lower risk: 21.8% positivity
   - Important for community transmission

4. **Pregnant Women** 🤰
   - 1,985 tests available (13% of total)
   - Special vulnerable group: 28.7% positivity
   - Data from 423 ANC facilities only

Which age group? (1-4):
```

### Step 4: Automatic TPR Calculation (NO USER INPUT)
**What happens:**
```
✅ Calculating TPR for Adamawa State...
   Settings: All Facilities, Under 5 Years

Analyzing test data:
- RDT tests found: 4,874 (80% of U5 tests)
- Microscopy tests found: 1,219 (20% of U5 tests)
- Total tests: 6,093

📊 Using maximum TPR approach (WHO standard):
- Calculating TPR for each test method separately
- Taking maximum value to capture worst-case scenario
- This ensures no high-burden areas are missed

Processing 226 wards...
[Progress indicator]

✅ Calculation complete!
```

## Key Changes from Previous Plan

### Removed:
- ❌ Test method question (Step 4)
- ❌ User confusion about RDT vs Microscopy
- ❌ Extra decision point

### Added:
- ✅ Automatic intelligent test method handling
- ✅ Clear explanation of methodology in results
- ✅ Transparency about data sources used

## Implementation Details

### Conversation Stage Enum Update
```python
class ConversationStage(Enum):
    INITIAL = "initial"
    TPR_STATE_SELECTION = "tpr_state_selection"
    TPR_FACILITY_LEVEL = "tpr_facility_level"
    TPR_AGE_GROUP = "tpr_age_group"
    TPR_CALCULATING = "tpr_calculating"  # Automatic, no user input
    TPR_COMPLETE = "tpr_complete"
    DATA_EXPLORING = "data_exploring"
```

### State Progression Logic
```python
def _handle_tpr_workflow(self, user_message: str):
    if self.current_stage == ConversationStage.TPR_STATE_SELECTION:
        # Extract state from user message
        selected_state = self._extract_state(user_message)
        self.tpr_selections['state'] = selected_state
        self.current_stage = ConversationStage.TPR_FACILITY_LEVEL
        return self._show_facility_options(selected_state)
    
    elif self.current_stage == ConversationStage.TPR_FACILITY_LEVEL:
        # Extract facility level
        selected_level = self._extract_facility_level(user_message)
        self.tpr_selections['facility_level'] = selected_level
        self.current_stage = ConversationStage.TPR_AGE_GROUP
        return self._show_age_group_options()
    
    elif self.current_stage == ConversationStage.TPR_AGE_GROUP:
        # Extract age group and START CALCULATION
        selected_age = self._extract_age_group(user_message)
        self.tpr_selections['age_group'] = selected_age
        self.current_stage = ConversationStage.TPR_CALCULATING
        
        # Automatically calculate TPR with both methods
        return self._calculate_tpr_automatic()
```

### Automatic TPR Calculation
```python
def _calculate_tpr_automatic(self):
    """
    Automatically calculate TPR using best available data.
    Uses maximum TPR from RDT and Microscopy (WHO standard).
    """
    # Use existing tpr_utils function
    from app.core.tpr_utils import calculate_ward_tpr
    
    results = calculate_ward_tpr(
        df=self.uploaded_data,
        age_group=self.tpr_selections['age_group'],
        test_method='both',  # Always use both, take maximum
        facility_level=self.tpr_selections['facility_level']
    )
    
    # Generate comprehensive summary
    return self._format_tpr_results(results)
```

## Benefits of Simplified Workflow

### For Users:
1. **Fewer decisions** - 3 instead of 4 questions
2. **No technical confusion** - Don't need to know test differences
3. **Faster completion** - Less cognitive load
4. **Better outcomes** - Automatic best-practice approach

### For Analysis:
1. **WHO compliant** - Uses maximum TPR standard
2. **Complete coverage** - Uses all available data
3. **Handles gaps** - Works with any data combination
4. **Transparent** - Shows methodology in results

## Result Display Update

Show HOW the calculation was done:
```
📊 **TPR Calculation Complete!**

**Methodology:**
✓ Analyzed both RDT and Microscopy data where available
✓ Used maximum TPR approach (WHO standard practice)
✓ This captures the highest risk scenario for better planning

**Data Sources Used:**
- RDT: 4,874 tests from 652 facilities
- Microscopy: 1,219 tests from 178 facilities
- Combined coverage: 226 wards analyzed

**Why Maximum TPR?**
Taking the higher value between RDT and Microscopy ensures:
- No high-burden areas are missed
- Conservative estimates for intervention planning
- Accounts for test method variations
```

## Testing Scenarios

### Scenario 1: Complete Data
- User has both RDT and Microscopy
- System uses maximum automatically
- Shows both in results

### Scenario 2: RDT Only
- User only has RDT data
- System uses RDT
- Notes in results: "Microscopy data not available"

### Scenario 3: Microscopy Only
- User only has Microscopy
- System uses Microscopy
- Notes in results: "RDT data not available"

### Scenario 4: Mixed Coverage
- Some wards have both, some have one
- System handles per ward
- Shows coverage map in results

## Success Metrics

- **Completion rate**: Should increase (fewer steps)
- **Time to complete**: Should decrease by ~25%
- **User confusion**: Should decrease (no test method question)
- **Analysis quality**: Same or better (uses all data)

## Next Steps

1. Update ConversationStage enum
2. Remove test method from state tracking
3. Update stage progression logic
4. Enhance results to show methodology
5. Test all scenarios