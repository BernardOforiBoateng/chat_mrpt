# Actionable Phrases Boldify Plan - UX Improvement

**Date:** 2025-10-06
**Status:** 📋 PLANNING PHASE
**Purpose:** Make all user-actionable phrases **bold** to help users know what to type

---

## Problem Statement

Users need clear visual cues about what phrases they can type to trigger specific workflows. Currently, actionable phrases are mixed with regular text, making it unclear what commands are available.

**User Request:** "Make 'run malaria risk analysis' bold or stand out as that is one of the phrases for activating the risk analysis, you know, all these helps users know what to type."

---

## Investigation Results

### Files with Actionable Phrases

#### 1. `/app/data_analysis_v3/core/tpr_workflow_handler.py`

**Location 1: Line 458 - TPR Exit Command**
```python
"message": "You're at the beginning of the TPR workflow. Please make your selection or say 'exit' to leave."
```
**Fix:** Bold 'exit'
```python
"message": "You're at the beginning of the TPR workflow. Please make your selection or say **'exit'** to leave."
```

---

**Location 2: Line 935 - Risk Analysis Confirmation**
```python
"gentle_reminder": "\n\n💡 When you're ready to add environmental factors for comprehensive risk assessment, just say **'yes'** or **'continue'**."
```
**Status:** ✅ Already bold! No change needed.

---

**Location 3: Lines 1320-1326 - Post-TPR Menu (CRITICAL)**
```python
message += "## What would you like to do?\n\n"
message += "- I can help you map variable distribution\n"
message += "- Check data quality\n"
message += "- Explore specific variables\n"
message += "- Run malaria risk analysis to rank wards for ITN distribution\n"
message += "- Something else\n\n"
message += "Just tell me what you're interested in."
```

**Fix:** Bold key action phrases
```python
message += "## What would you like to do?\n\n"
message += "- **Map variable distribution** - Visualize how variables are spread across wards\n"
message += "- **Check data quality** - Validate your dataset\n"
message += "- **Explore specific variables** - Dive into individual indicators\n"
message += "- **Run malaria risk analysis** - Rank wards for ITN distribution\n"
message += "- **Something else** - Ask me anything\n\n"
message += "Just tell me what you're interested in."
```

---

#### 2. `/app/tools/complete_analysis_tools.py`

**Location 1: Lines 1097-1108 - Post-Risk Analysis Menu (CRITICAL)**
```python
## What would you like to do next?

- **Plan ITN/bed net distribution** - Allocate nets optimally based on these rankings
- View highest risk wards that need urgent intervention
- View lowest risk wards
{"- Compare methods visually - Create side-by-side vulnerability maps (say 'create vulnerability map comparison')" if not pca_result.get("pca_skipped") else ""}
{"- Create vulnerability map - Show both composite and PCA risk levels on maps (say 'create vulnerability map')" if not pca_result.get("pca_skipped") else "- Create composite vulnerability map - Show risk levels visually on a map (say 'create composite score maps')"}
- Export results

### To start ITN planning

Just say "I want to plan bed net distribution" or "Help me distribute ITNs".
```

**Fix:** Bold all actionable phrases consistently
```python
## What would you like to do next?

- **Plan ITN/bed net distribution** - Allocate nets optimally based on these rankings
- **View highest risk wards** - See wards that need urgent intervention
- **View lowest risk wards** - Identify control areas
{"- **Compare methods visually** - Create side-by-side vulnerability maps (say **'create vulnerability map comparison'**)" if not pca_result.get("pca_skipped") else ""}
{"- **Create vulnerability map** - Show both composite and PCA risk levels (say **'create vulnerability map'**)" if not pca_result.get("pca_skipped") else "- **Create composite vulnerability map** - Show risk levels visually (say **'create composite score maps'**)"}
- **Export results** - Download analysis data

### To start ITN planning

Just say **"I want to plan bed net distribution"** or **"Help me distribute ITNs"**.
```

---

**Location 2: Lines 1130-1135 - Fallback Next Steps**
```python
fallback_parts.append("### Next Steps\n")
fallback_parts.append("\n")
fallback_parts.append("- Review the generated maps and charts\n")
fallback_parts.append("- Ask for specific ward rankings\n")
fallback_parts.append("- Request additional visualizations\n")
```

**Fix:** Bold action verbs
```python
fallback_parts.append("### Next Steps\n")
fallback_parts.append("\n")
fallback_parts.append("- **Review** the generated maps and charts\n")
fallback_parts.append("- **Ask for specific ward rankings**\n")
fallback_parts.append("- **Request additional visualizations**\n")
```

---

**Location 3: Lines 1214-1217 - Summary Next Steps**
```python
summary_parts.append("### 💡 Next Steps")
summary_parts.append("- Review the generated visualizations above")
summary_parts.append("- Ask for specific ward comparisons")
summary_parts.append("- Request additional analysis or maps")
summary_parts.append("- Export results for intervention planning")
```

**Fix:** Bold action verbs
```python
summary_parts.append("### 💡 Next Steps\n")
summary_parts.append("\n")
summary_parts.append("- **Review** the generated visualizations above\n")
summary_parts.append("- **Ask for specific ward comparisons**\n")
summary_parts.append("- **Request additional analysis or maps**\n")
summary_parts.append("- **Export results** for intervention planning\n")
```

---

#### 3. `/app/data_analysis_v3/core/formatters.py`

**Location 1: Lines 40, 50 - State Selection**
```python
message += "**Which state would you like to analyze?**\n\n"
# ...
message += "Which state would you like to analyze? (Enter the number or state name)"
```
**Status:** ✅ Already bold! No change needed.

---

**Location 2: Lines 92-94 - Facility Selection Commands**
```python
message += "• Say **'show facility charts'** to see distribution and test volume graphs\n"
message += "• Or ask me to explain the differences\n\n"
message += "Type: **primary**, **secondary**, **tertiary**, or **all**"
```

**Fix:** Use proper markdown lists
```python
message += "- Say **'show facility charts'** to see distribution and test volume graphs\n"
message += "- Or **ask me to explain** the differences\n\n"
message += "Type: **primary**, **secondary**, **tertiary**, or **all**"
```

---

**Location 3: Lines 134-136 - Facility Selection (Auto-selected state)**
```python
message += "• Say **'show facility charts'** to see distribution and test volume graphs\n"
message += "• Or ask me to explain the differences\n\n"
message += "Type: **primary**, **secondary**, **tertiary**, or **all**"
```

**Fix:** Use proper markdown lists
```python
message += "- Say **'show facility charts'** to see distribution and test volume graphs\n"
message += "- Or **ask me to explain** the differences\n\n"
message += "Type: **primary**, **secondary**, **tertiary**, or **all**"
```

---

**Location 4: Lines 188-190 - Age Group Selection Commands**
```python
message += "• Say **'show age charts'** to see test volumes and positivity rates\n"
message += "• Or ask me to explain the differences\n\n"
message += "Type: **u5**, **o5**, **pw**, or **all**"
```

**Fix:** Use proper markdown lists
```python
message += "- Say **'show age charts'** to see test volumes and positivity rates\n"
message += "- Or **ask me to explain** the differences\n\n"
message += "Type: **u5**, **o5**, **pw**, or **all**"
```

---

**Location 5: Line 209 - TPR Completion Prompt**
```python
message += "Your TPR analysis is complete. Say **'continue'** or **'yes'** when you'd like to add environmental factors for comprehensive risk assessment."
```
**Status:** ✅ Already bold! No change needed.

---

## Pattern Analysis

### Current Inconsistencies

1. **Mixed bullet styles:** Some use `•` (unicode), some use `-` (markdown)
2. **Inconsistent boldness:** Some actionable phrases are bold, others are not
3. **Menu items:** Some menu items are bold, others are plain text
4. **Command examples:** Some are quoted + bold, some are just quoted

### Proposed Standards

#### 1. **Menu Items** (What would you like to do?)
- **Bold the main action phrase**
- Add brief description after `-`
- Example: `- **Run malaria risk analysis** - Rank wards for ITN distribution`

#### 2. **Command Hints** (say 'xyz' to do...)
- **Bold quoted commands**
- Example: `Say **'show facility charts'** to see graphs`

#### 3. **Type Instructions** (Type: primary, secondary...)
- **Bold each option**
- Example: `Type: **primary**, **secondary**, **tertiary**, or **all**`

#### 4. **Action Lists** (Next Steps, What's next)
- **Bold action verbs or full command phrases**
- Example: `- **Review** the generated maps`
- Example: `- **Ask for specific ward comparisons**`

---

## Summary of Changes

| File | Changes | Impact |
|------|---------|--------|
| `tpr_workflow_handler.py` | 2 sections | Post-TPR menu clarity + exit command |
| `complete_analysis_tools.py` | 3 sections | Post-risk menu + next steps |
| `formatters.py` | 3 sections | Facility/age selection commands + bullet fix |

**Total Changes:** 8 sections across 3 files

---

## Implementation Plan

### Phase 1: Quick Wins (15 mins)
1. Fix `tpr_workflow_handler.py` line 1320-1326 (Post-TPR menu) - **CRITICAL**
2. Fix `complete_analysis_tools.py` lines 1097-1108 (Post-risk menu) - **CRITICAL**
3. Fix `tpr_workflow_handler.py` line 458 (exit command)

### Phase 2: Consistency (15 mins)
4. Fix `complete_analysis_tools.py` lines 1130-1135 (fallback next steps)
5. Fix `complete_analysis_tools.py` lines 1214-1217 (summary next steps)

### Phase 3: Formatters (10 mins)
6. Fix `formatters.py` lines 92-94 (facility selection - unicode bullets)
7. Fix `formatters.py` lines 134-136 (facility selection auto-state)
8. Fix `formatters.py` lines 188-190 (age group selection)

### Phase 4: Deploy & Test (10 mins)
9. Upload to both AWS instances
10. Restart services
11. Verify in browser

**Total Time:** ~50 minutes

---

## Testing Checklist

After deployment, verify:

- [ ] **Post-TPR Menu:** "What would you like to do?" shows bold action phrases
  - "Map variable distribution"
  - "Check data quality"
  - "Explore specific variables"
  - "Run malaria risk analysis" ← **KEY PHRASE**

- [ ] **Post-Risk Menu:** "What would you like to do next?" shows bold action phrases
  - "Plan ITN/bed net distribution" ← **KEY PHRASE**
  - "View highest risk wards"
  - Command hints in parentheses are bold

- [ ] **Facility Selection:** Commands like "show facility charts" are bold

- [ ] **Age Group Selection:** Commands like "show age charts" are bold

- [ ] **Next Steps Sections:** Action verbs are bold throughout

---

## Expected User Benefits

1. **Faster Workflow Discovery** - Users immediately see what they can type
2. **Reduced Friction** - No guessing what commands are available
3. **Better Scanning** - Bold phrases pop out when reading
4. **Consistent UX** - Same pattern across all workflows
5. **Improved Onboarding** - New users learn faster

---

## Notes

- All phrase examples in parentheses (say 'xyz') should be bold
- Menu items should be bold at the start, with plain text descriptions
- Type: instructions should bold each option
- Already-bold phrases (lines 935, 40, 209) don't need changes
- Unicode bullets (•) found in formatters.py should be changed to markdown lists (-)

---

**Status:** Ready for user approval before implementation
