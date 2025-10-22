# TPR Context Timing Correction

## Date: 2025-08-13

## Important Correction
User correctly pointed out that enhanced TPR information should NOT appear on file upload, but rather DURING the TPR workflow when users need to make decisions.

## Correct Information Flow

### 1. After File Upload (Keep Simple)
```
📊 **Data Successfully Loaded!**

**Dataset Overview:**
• 10,452 rows × 21 columns
• Memory usage: 5.1 MB

**Column Types:**
• 15 numeric columns
• 5 text columns
• 1 datetime columns

**Data Quality:**
• 21 columns have missing values (68.4% complete)
• 4 duplicate rows found (0.1%)

**What would you like to do with your data?**

1️⃣ **Calculate Test Positivity Rate (TPR)**
   If your data contains test and positive results, I can guide you through TPR calculation

2️⃣ **Explore & Analyze Data**
   Examine patterns, create visualizations, and understand your data

3️⃣ **Generate Summary Statistics**
   Get detailed descriptive statistics and correlations

4️⃣ **Data Quality Report**
   Detailed analysis of missing values, duplicates, and data integrity

Just type 1, 2, 3, or 4 (or describe what you'd like to do)
```

### 2. User Chooses TPR (Option 1)

**THEN** start analyzing the data for TPR-specific context:

```
Great! I'll guide you through the TPR calculation process.

Let me analyze your data to understand what's available...

[Brief pause while analyzing]

I've detected that your data contains test results for multiple age groups. 
Let me show you what's available for each:
```

### 3. Age Group Selection (WITH Context)

**NOW** show the rich statistics:

```
**Which age group would you like to analyze?**

Based on your data, here's what I found:

1. **All Age Groups Combined** ⭐ Recommended
   - 15,234 tests available (100% coverage)
   - Most comprehensive view for planning
   - Current overall positivity: 26.5%

2. **Under 5 Years** 
   - 6,093 tests available (40% of total)
   - Higher risk group with 34.2% positivity
   - Data from 687 facilities

3. **5 Years and Older**
   - 7,156 tests available (47% of total)
   - Lower positivity at 21.8%
   - Data from 695 facilities

4. **Pregnant Women**
   - 1,985 tests available (13% of total)
   - Special vulnerable group: 28.7% positivity
   - Limited to 423 ANC facilities

💡 Tip: "All Age Groups" gives the most complete picture

Which would you like to analyze?
```

### 4. Test Method Selection (WITH Context)

After user selects age group:

```
You selected "Under 5 Years". 

**Which test method should I use for the analysis?**

Your data contains:

1. **RDT Tests** (Recommended)
   - 4,874 tests for under-5s (80% of U5 tests)
   - Available at 652 facilities
   - Better rural coverage

2. **Microscopy Tests**
   - 1,219 tests for under-5s (20% of U5 tests)
   - Available at 178 facilities
   - Mostly urban/secondary facilities

3. **Combined (RDT + Microscopy)**
   - All 6,093 tests included
   - Most comprehensive but mixes methodologies

Which method would you prefer?
```

## Key Principle: Progressive Disclosure

1. **File Upload**: Generic data summary (no TPR specifics)
2. **User Chooses TPR**: Begin TPR-specific analysis
3. **Each TPR Step**: Provide relevant statistics for that decision
4. **Final Results**: Comprehensive TPR analysis

## Benefits of This Approach

✅ **Not Overwhelming**: Users only see TPR info if they choose TPR
✅ **Contextual**: Information appears when needed for decisions
✅ **Flexible**: Users doing other analysis aren't confused by TPR stats
✅ **Guided**: Each step provides just enough info to make that choice

## Implementation Notes

### When to Calculate TPR Statistics

```python
def analyze(self, user_query: str):
    # File just uploaded - show generic summary
    if self.first_interaction:
        return self.data_summary  # Generic, no TPR stats
    
    # User chooses option 1 (TPR)
    if user_selected_tpr(user_query):
        # NOW calculate TPR-specific statistics
        self.tpr_stats = self._analyze_for_tpr(self.uploaded_data)
        self.current_stage = ConversationStage.TPR_AGE_GROUP
        return self._show_age_group_options()  # WITH stats
    
    # During TPR workflow
    if self.current_stage == ConversationStage.TPR_AGE_GROUP:
        # Show test method options WITH stats for selected age group
        return self._show_test_method_options(selected_age_group)
```

### Lazy Loading of Statistics

```python
class TPRWorkflowHandler:
    def __init__(self):
        self.tpr_stats = None  # Don't calculate until needed
    
    def start_tpr_workflow(self, df):
        # Only NOW calculate TPR-specific statistics
        self.tpr_stats = TPRDataAnalyzer().analyze_all_options(df)
        return self.show_age_group_options()
    
    def show_age_group_options(self):
        # Use pre-calculated stats to show context
        return format_age_group_options(self.tpr_stats['age_groups'])
```

## What NOT to Show on Upload

❌ State-level TPR percentages
❌ Age group breakdowns
❌ Test method distributions
❌ Ward-level analysis
❌ Facility type statistics
❌ TPR thresholds or WHO standards

## What TO Show on Upload

✅ Basic file metrics (rows, columns)
✅ Data types (numeric, text, date)
✅ Overall data quality (completeness)
✅ Generic options menu (1-4)
✅ Simple column list if asked

## Summary

The enhanced information should be:
1. **Hidden initially** - Not shown on file upload
2. **Triggered by choice** - Only when user selects TPR
3. **Progressive** - More detail at each workflow step
4. **Contextual** - Relevant to the current decision
5. **Actionable** - Helps make informed choices