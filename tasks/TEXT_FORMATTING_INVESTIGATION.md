# Text Formatting Investigation - Hardcoded Assistant Responses

**Date:** 2025-10-06
**Status:** 🔍 INVESTIGATION COMPLETE - NO CODING YET

---

## Executive Summary

Investigated hardcoded text output from TPR workflow and risk analysis tools. **Found extensive use of bad formatting patterns** that prevent proper rendering in the React frontend.

**Root Cause:** These tools output text with bold markdown (`**`) and unicode bullets (`•`) instead of proper semantic Markdown (headings `##` and lists `-`).

---

## Reference: What Good Formatting Looks Like

From `/tasks/SSE_STREAMING_FORMAT_GUIDE.md`:

### ✅ GOOD (Works Perfectly)
```python
message = "## Step 1: Choose Facility Level\n\n"
message += "Select from the following options:\n\n"
message += "- Primary (1)\n"
message += "- Secondary (2)\n"
message += "- Tertiary (3)\n\n"
```

**Result:** Proper `<h2>`, `<ul>`, `<li>` HTML with vertical spacing via Tailwind `prose` classes.

---

### ❌ BAD (Doesn't Work)
```python
message = "**Step 1: Choose Facility Level**\n"
message += "• Primary (1)\n"
message += "• Secondary (2)\n"
```

**Result:** No semantic HTML, no vertical spacing, looks cramped and ugly.

---

## Files Analyzed

### 1. TPR Workflow Handler
**File:** `/home/ec2-user/ChatMRPT/app/data_analysis_v3/core/tpr_workflow_handler.py`

**Lines with Bad Patterns:**

| Line | Pattern | Issue |
|------|---------|-------|
| 464 | `"**Your TPR workflow status:**\n\n"` | Bold instead of `##` heading |
| 467 | `f"• **{key}**: {value}\n"` | Unicode bullet instead of `-` |
| 471 | `f"\n**Current stage**: {stage}"` | Bold for emphasis instead of heading |
| 535 | `"**The process has 3 simple steps:**\n\n"` | Bold instead of `##` heading |
| 582 | `"**The process has 3 simple steps:**\n\n"` | Bold instead of `##` heading |
| 627 | `f"You've selected **{state}**."` | Bold for emphasis (acceptable) |
| 657 | `"\n\n**Tip**: Secondary facilities..."` | Bold instead of `###` heading |
| 717 | `f"You've selected **{level}** facilities."` | Bold for emphasis (acceptable) |
| 803 | `"⚠️ **You've already selected...**\n\n"` | Bold instead of heading |
| 875 | `f"Analyzing **{age}** age group.\n\n"` | Bold for emphasis (acceptable) |
| 935 | `"just say **'yes'** or **'continue'**."` | Bold for emphasis (acceptable) |
| 987 | `f"✅ **Calculating TPR for {state}**"` | Bold instead of `##` heading |

**Total Issues:** ~12 bad patterns (bold as headings, unicode bullets)

---

### 2. Response Formatter
**File:** `/home/ec2-user/ChatMRPT/app/data_analysis_v3/formatters/response_formatter.py`

**Lines with Bad Patterns:**

| Line | Pattern | Issue |
|------|---------|-------|
| 191 | `f"• {insight}"` | Unicode bullet instead of `-` |

**Total Issues:** 1 bad pattern (minor, only one instance)

---

### 3. Risk Analysis Tool (MAJOR ISSUES)
**File:** `/home/ec2-user/ChatMRPT/app/tools/complete_analysis_tools.py`

**Lines with Bad Patterns:**

| Line Range | Pattern | Issue |
|------------|---------|-------|
| 1014 | `**Behind the Scenes - Statistical Testing:**` | Bold instead of `###` heading |
| 1017-1023 | `• **KMO Test Result**: ...\n• **Bartlett's Test**: ...` | Unicode bullets + bold |
| 1054-1063 | Same pattern repeated | Unicode bullets + bold |
| 1070-1072 | Same pattern repeated | Unicode bullets + bold |
| 1078 | `**Here's what I did:**` | Bold instead of `###` heading |
| 1079-1086 | `1. **Cleaned your data** - ...\n2. **Selected...` | Numbered list with bold (should be markdown list) |
| 1084-1085 | Nested `• **Composite Score**:` | Unicode bullets nested |
| 1090-1097 | `• **Plan ITN/bed net...**\n• View highest...` | Unicode bullets |
| 1097 | `**To start ITN planning**, just say...` | Bold instead of `###` heading |
| 1104-1127 | Multiple `**Analysis Complete**`, `**Analyzed:**` | Bold as section markers |
| 1137-1164 | `**Analyzed:** ...\n**Methods:** ...` | Bold as labels |
| 1162-1164 | `{i}. **{ward_name}** (Score: ...)` | Numbered list with bold |

**Total Issues:** ~50+ bad patterns throughout the file

**This is the worst offender!**

---

### 4. ITN Planning Tool
**File:** `/home/ec2-user/ChatMRPT/app/tools/itn_planning_tools.py`

**Lines with Bad Patterns:**

| Line | Pattern | Issue |
|------|---------|-------|
| 138 | `⚠️ **Ward Matching Notice**: ...` | Bold instead of `###` heading |
| 377-379 | `1. **Total number of nets**:\n2. **Average household**:` | Numbered list with bold |
| 394 | `✅ **ITN Distribution Plan Complete!**` | Bold instead of `##` heading |
| 396 | `**Allocation Summary:**` | Bold instead of `###` heading |
| 401 | `**Coverage Statistics:**` | Bold instead of `###` heading |
| 410 | `**Top 5 Highest Risk Wards...**` | Bold instead of `###` heading |
| 413 | `{i}. **{ward}** (Risk Rank ...)` | Numbered list with bold |

**Total Issues:** ~10 bad patterns

---

## Pattern Analysis

### Common Bad Patterns Found:

1. **Bold as Headings** (`**Title:**`)
   - Used instead of `##` or `###` headings
   - Doesn't create `<h2>` or `<h3>` elements
   - No vertical spacing

2. **Unicode Bullets** (`•`)
   - Used instead of `-` markdown lists
   - Doesn't create `<ul>` and `<li>` elements
   - No list styling

3. **Numbered Lists with Bold** (`1. **Item**`)
   - Markdown supports numbered lists: `1. Item`
   - Bold is redundant and breaks semantic structure

4. **Nested Bullets** (`• **Sub-item**`)
   - Should use proper markdown indentation:
   ```
   - Main item
     - Sub item
   ```

---

## Impact Assessment

### Where Users See Bad Formatting:

1. **TPR Workflow Messages:**
   - Status updates (cramped, no spacing)
   - Step instructions (unclear hierarchy)
   - Tips and acknowledgments (inconsistent)

2. **Risk Analysis Output:**
   - Statistical test results (wall of text)
   - "Here's what I did" explanations (no structure)
   - Next steps (bullets don't render as lists)
   - Summary tables (cramped)

3. **ITN Planning Output:**
   - Allocation summaries (no spacing)
   - Top wards list (poor formatting)
   - Coverage statistics (cramped)

### User Experience Problems:

- ❌ No vertical spacing → everything cramped together
- ❌ No visual hierarchy → hard to scan
- ❌ Lists don't look like lists → confusing
- ❌ Headings don't stand out → unclear structure
- ❌ Professional appearance suffers

**From transcript (Line 484-494):**
> "I don't understand why your texts are showing up. No spacing. Everything is all together. No bullet points. Nothing."

**This is exactly the problem we found!**

---

## Files That Need Fixing

### Priority 1 (High Impact):
1. ✅ `/app/tools/complete_analysis_tools.py` - **~50+ instances** (CRITICAL)
2. ✅ `/app/data_analysis_v3/core/tpr_workflow_handler.py` - **~12 instances** (HIGH)
3. ✅ `/app/tools/itn_planning_tools.py` - **~10 instances** (MEDIUM)

### Priority 2 (Low Impact):
4. `/app/data_analysis_v3/formatters/response_formatter.py` - **1 instance** (LOW)

---

## Fix Strategy (DO NOT IMPLEMENT YET)

### Transformation Rules:

1. **Bold Headings → Markdown Headings**
   ```python
   # BEFORE
   "**Section Title:**"

   # AFTER
   "## Section Title\n\n"  # or ### for subsections
   ```

2. **Unicode Bullets → Markdown Lists**
   ```python
   # BEFORE
   "• Item 1\n• Item 2"

   # AFTER
   "- Item 1\n- Item 2\n"
   ```

3. **Add Blank Lines Between Sections**
   ```python
   # BEFORE
   "Section 1\nSection 2"

   # AFTER
   "Section 1\n\nSection 2"
   ```

4. **Numbered Lists**
   ```python
   # BEFORE
   "1. **Item one**\n2. **Item two**"

   # AFTER
   "1. Item one\n2. Item two\n"
   ```

---

## Estimated Effort

| File | Lines to Change | Complexity | Time Estimate |
|------|----------------|------------|---------------|
| complete_analysis_tools.py | ~50 | Medium | 1.5-2 hours |
| tpr_workflow_handler.py | ~12 | Low | 30-45 mins |
| itn_planning_tools.py | ~10 | Low | 30 mins |
| response_formatter.py | 1 | Trivial | 5 mins |

**Total Time:** ~3-3.5 hours

---

## Testing Plan (After Fixes)

1. **Upload TPR data** → Check TPR workflow messages formatting
2. **Complete TPR workflow** → Check transition messages
3. **Run risk analysis** → Check "Here's what I did" formatting
4. **Run ITN planning** → Check allocation summary formatting
5. **Compare before/after screenshots** → Verify visual improvements

---

## Example: Before vs After

### BEFORE (current code):
```python
message = "**Here's what I did:**\n"
message += "1. **Cleaned your data** - Fixed ward name mismatches\n"
message += "2. **Selected 7 risk factors** - Based on region\n\n"
message += "**Next Steps:**\n"
message += "• **Plan ITN/bed net distribution**\n"
message += "• View highest risk wards\n"
```

**Renders as:** Cramped text, no hierarchy, no proper lists

---

### AFTER (with fixes):
```python
message = "## Here's what I did\n\n"
message += "1. Cleaned your data - Fixed ward name mismatches\n"
message += "2. Selected 7 risk factors - Based on region\n\n"
message += "### Next Steps\n\n"
message += "- Plan ITN/bed net distribution\n"
message += "- View highest risk wards\n\n"
```

**Renders as:**
- Proper `<h2>` heading with vertical spacing
- Proper numbered list with spacing
- Proper `<h3>` subheading
- Proper `<ul>` list with spacing
- Clean, scannable, professional

---

## Key Findings

1. **Root Cause Confirmed:** Hardcoded text uses bold/bullets instead of semantic Markdown
2. **Scale of Problem:** ~70+ instances across 4 files
3. **Worst Offender:** `complete_analysis_tools.py` (50+ instances)
4. **User Impact:** Exactly matches complaint in transcript (no spacing, no bullets)
5. **Solution:** Replace bold/bullets with proper Markdown headings/lists
6. **Effort:** Moderate (3-3.5 hours estimated)

---

## Recommendations

1. **Start with complete_analysis_tools.py** (biggest impact)
2. **Test each file after changes** (verify rendering)
3. **Follow SSE_STREAMING_FORMAT_GUIDE.md** (proven patterns)
4. **Add blank lines liberally** (`\n\n` between sections)
5. **Use semantic headings** (`##` for main, `###` for sub)
6. **Use markdown lists** (`-` for bullets, `1.` for numbered)

---

## Next Steps (Awaiting User Approval)

1. ⏸️ **Waiting for approval to proceed with fixes**
2. ⏸️ Once approved, fix files in priority order
3. ⏸️ Test each fix on production
4. ⏸️ Document changes in deployment notes

---

**Investigation Status:** ✅ COMPLETE
**Ready to Code:** ⏸️ AWAITING USER APPROVAL
**Files Identified:** 4 files, ~70+ bad patterns
**Estimated Fix Time:** 3-3.5 hours
