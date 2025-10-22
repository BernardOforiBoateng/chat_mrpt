# Text Formatting Fix Plan - Comprehensive Step-by-Step

**Date:** 2025-10-06
**Status:** 📋 PLAN - AWAITING APPROVAL
**Estimated Total Time:** 4-5 hours
**Risk Level:** 🟡 MEDIUM (user-facing changes, but reversible)

---

## 🎯 Objective

Fix all hardcoded text formatting issues in TPR workflow, risk analysis, and ITN planning tools to use proper Markdown syntax that renders correctly in the React frontend.

**Success Criteria:**
- ✅ All assistant responses have proper vertical spacing
- ✅ Headings render as `<h2>` and `<h3>` elements
- ✅ Lists render as proper `<ul>` and `<li>` elements
- ✅ Text is scannable and professional-looking
- ✅ All workflows still function correctly

---

## 📊 Scope Summary

| File | Bad Patterns | Priority | Estimated Time |
|------|-------------|----------|----------------|
| complete_analysis_tools.py | ~50+ | 🔴 CRITICAL | 2 hours |
| tpr_workflow_handler.py | ~12 | 🟠 HIGH | 45 mins |
| itn_planning_tools.py | ~10 | 🟡 MEDIUM | 30 mins |
| response_formatter.py | 1 | 🟢 LOW | 5 mins |

**Total:** ~70+ instances across 4 files

---

## 🧩 Transformation Rules (Reference)

### Rule 1: Bold Headings → Markdown Headings
```python
# BEFORE (Bad)
"**Section Title:**"
"**Subtitle:**"

# AFTER (Good)
"## Section Title\n\n"
"### Subtitle\n\n"
```

### Rule 2: Unicode Bullets → Markdown Lists
```python
# BEFORE (Bad)
"• Item 1\n• Item 2\n"

# AFTER (Good)
"- Item 1\n- Item 2\n\n"
```

### Rule 3: Numbered Lists (Remove Bold)
```python
# BEFORE (Bad)
"1. **Item one**\n2. **Item two**"

# AFTER (Good)
"1. Item one\n2. Item two\n\n"
```

### Rule 4: Add Blank Lines Between Sections
```python
# BEFORE (Bad)
"Section 1\nSection 2"

# AFTER (Good)
"Section 1\n\nSection 2"
```

### Rule 5: Inline Bold - KEEP UNCHANGED
```python
# These are for EMPHASIS, not headings - KEEP AS IS
f"You selected **{value}**"
"just say **'yes'** or **'continue'**"
```

**Decision Rule:** Only change bold when it's used AS a heading/label at start of line, NOT for emphasis within sentences.

---

## 📋 Step-by-Step Execution Plan

### PHASE 1: PREPARATION (15-20 mins)

#### Step 1.1: Create AWS Backups
```bash
# SSH to both instances, create timestamped backups
ssh Instance1:
  cp complete_analysis_tools.py complete_analysis_tools.py.backup_formatting_20251006
  cp tpr_workflow_handler.py tpr_workflow_handler.py.backup_formatting_20251006
  cp itn_planning_tools.py itn_planning_tools.py.backup_formatting_20251006
  cp response_formatter.py response_formatter.py.backup_formatting_20251006

ssh Instance2:
  # Same backups
```

**Success Check:** ✅ Backup files exist on both instances

---

#### Step 1.2: Create Local Workspace
```bash
# Create local directory for work
mkdir /tmp/formatting_fixes
cd /tmp/formatting_fixes
```

**Success Check:** ✅ Directory created

---

#### Step 1.3: Download Current Files from AWS
```bash
# Download from Instance 1 to local machine
scp Instance1:/path/complete_analysis_tools.py ./
scp Instance1:/path/tpr_workflow_handler.py ./
scp Instance1:/path/itn_planning_tools.py ./
scp Instance1:/path/response_formatter.py ./
```

**Success Check:** ✅ All 4 files downloaded locally

---

### PHASE 2: FILE FIXES (3-3.5 hours)

**Strategy:** Fix ONE file at a time, test immediately, then move to next.

---

#### Step 2.1: Fix complete_analysis_tools.py (Priority 1)

**Time Estimate:** 2 hours
**Complexity:** High (~50+ instances)

##### 2.1.1: Apply Transformations
- Line 1014: `**Behind the Scenes - Statistical Testing:**` → `### Behind the Scenes - Statistical Testing\n\n`
- Lines 1017-1023: Replace all `• **Label**:` → `- **Label**:`
- Line 1078: `**Here's what I did:**` → `## Here's what I did\n\n`
- Lines 1079-1086: Remove bold from numbered list items
- Lines 1090-1097: Replace `•` with `-`
- Line 1097: `**To start ITN planning**` → `### To start ITN planning\n\n`
- Lines 1104-1164: Replace all `**Label:**` with `### Label\n\n`

**Detailed Pattern Replacements:**
```python
# Pattern 1: Main section headings
"**Here's what I did:**" → "## Here's what I did\n\n"
"**Behind the Scenes - Statistical Testing:**" → "### Behind the Scenes - Statistical Testing\n\n"

# Pattern 2: Subsection headings
"**Next Steps:**" → "### Next Steps\n\n"
"**Allocation Summary:**" → "### Allocation Summary\n\n"
"**Coverage Statistics:**" → "### Coverage Statistics\n\n"

# Pattern 3: Bullet points
"• **KMO Test Result**:" → "- **KMO Test Result**:"
"• **Bartlett's Test**:" → "- **Bartlett's Test**:"
"• **Plan ITN/bed net distribution**" → "- Plan ITN/bed net distribution"

# Pattern 4: Numbered lists
"1. **Cleaned your data**" → "1. Cleaned your data"
"2. **Selected 7 risk factors**" → "2. Selected 7 risk factors"

# Pattern 5: Add spacing after sections
After each heading: Add \n\n if not present
After lists: Add \n\n if not present
```

##### 2.1.2: Test Locally (Visual Review)
- Open file in editor
- Verify all transformations look correct
- Check no broken strings
- Check no syntax errors

**Success Check:** ✅ File compiles, no syntax errors

##### 2.1.3: Deploy to Instance 1 ONLY (Test Instance)
```bash
scp complete_analysis_tools.py Instance1:/path/
ssh Instance1 'sudo systemctl restart chatmrpt'
```

**Success Check:** ✅ Service restarts successfully

##### 2.1.4: Test Risk Analysis Workflow
1. Upload test data to production
2. Run TPR workflow (if not already done)
3. Run risk analysis: "run malaria risk analysis"
4. Check output formatting:
   - ✅ "Here's what I did" renders as heading with spacing
   - ✅ Numbered list has proper spacing
   - ✅ "Next Steps" renders as heading
   - ✅ Bullet points render as proper list
   - ✅ "Behind the Scenes" has proper spacing

**Success Check:** ✅ All formatting looks good, no regressions

##### 2.1.5: Deploy to Instance 2 (Production Instance)
```bash
scp complete_analysis_tools.py Instance2:/path/
ssh Instance2 'sudo systemctl restart chatmrpt'
```

**Success Check:** ✅ Both instances have updated code

##### 2.1.6: Take Screenshot (Before/After)
- Capture before screenshot (from context.md or fresh test)
- Capture after screenshot
- Document in `/tasks/formatting_screenshots/`

**Success Check:** ✅ Screenshots show clear improvement

---

#### Step 2.2: Fix tpr_workflow_handler.py (Priority 2)

**Time Estimate:** 45 mins
**Complexity:** Medium (~12 instances)

##### 2.2.1: Apply Transformations
- Line 464: `"**Your TPR workflow status:**\n\n"` → `"## Your TPR workflow status\n\n"`
- Line 467: `f"• **{key}**: {value}\n"` → `f"- **{key}**: {value}\n"`
- Line 535: `"**The process has 3 simple steps:**\n\n"` → `"## The process has 3 simple steps\n\n"`
- Line 582: Same as 535
- Line 657: `"\n\n**Tip**: Secondary..."` → `"\n\n### Tip\n\nSecondary..."`
- Line 803: `"⚠️ **You've already selected...**\n\n"` → `"## ⚠️ You've already selected...\n\n"`
- Line 987: `f"✅ **Calculating TPR for {state}**"` → `f"## ✅ Calculating TPR for {state}\n\n"`

**Note:** Keep emphasis bold (lines 627, 717, 875, 935) - these are inline, not headings

**Detailed Pattern Replacements:**
```python
# Headings at start of messages
"**Your TPR workflow status:**" → "## Your TPR workflow status\n\n"
"**The process has 3 simple steps:**" → "## The process has 3 simple steps\n\n"
"**Tip**:" → "### Tip\n\n"

# Bullet points
"• **{key}**:" → "- **{key}**:"

# Keep these (inline emphasis):
f"You've selected **{state}**" → KEEP AS IS
f"just say **'yes'**" → KEEP AS IS
```

##### 2.2.2: Test Locally

**Success Check:** ✅ File compiles, no syntax errors

##### 2.2.3: Deploy to Instance 1 ONLY
```bash
scp tpr_workflow_handler.py Instance1:/path/
ssh Instance1 'sudo systemctl restart chatmrpt'
```

##### 2.2.4: Test TPR Workflow
1. Clear session, start fresh
2. Upload TPR data
3. Start TPR workflow: "start tpr workflow"
4. Check output formatting:
   - ✅ "The process has 3 simple steps" renders as heading
   - ✅ Status messages have proper spacing
   - ✅ Tips render as subsections
   - ✅ Step acknowledgments have spacing

**Success Check:** ✅ All formatting looks good

##### 2.2.5: Deploy to Instance 2

##### 2.2.6: Screenshot

---

#### Step 2.3: Fix itn_planning_tools.py (Priority 3)

**Time Estimate:** 30 mins
**Complexity:** Low (~10 instances)

##### 2.3.1: Apply Transformations
- Line 138: `"⚠️ **Ward Matching Notice**:"` → `"### ⚠️ Ward Matching Notice\n\n"`
- Lines 377-379: Remove bold from numbered list
- Line 394: `"✅ **ITN Distribution Plan Complete!**"` → `"## ✅ ITN Distribution Plan Complete!\n\n"`
- Line 396: `"**Allocation Summary:**"` → `"### Allocation Summary\n\n"`
- Line 401: `"**Coverage Statistics:**"` → `"### Coverage Statistics\n\n"`
- Line 410: `"**Top 5 Highest Risk Wards...**"` → `"### Top 5 Highest Risk Wards\n\n"`
- Line 413: Remove bold from ward names in numbered list

**Detailed Pattern Replacements:**
```python
# Main heading
"✅ **ITN Distribution Plan Complete!**" → "## ✅ ITN Distribution Plan Complete!\n\n"

# Subsection headings
"**Allocation Summary:**" → "### Allocation Summary\n\n"
"**Coverage Statistics:**" → "### Coverage Statistics\n\n"
"**Top 5 Highest Risk Wards...**" → "### Top 5 Highest Risk Wards\n\n"

# Numbered lists
"1. **Total number of nets**:" → "1. Total number of nets:"
"{i}. **{ward}**" → "{i}. {ward}"
```

##### 2.3.2: Test Locally

##### 2.3.3: Deploy to Instance 1

##### 2.3.4: Test ITN Planning Workflow
1. Ensure analysis complete
2. Run ITN planning: "help me distribute ITNs"
3. Check output formatting:
   - ✅ "ITN Distribution Plan Complete" renders as heading
   - ✅ Subsections have proper hierarchy
   - ✅ Top wards list has spacing
   - ✅ Questions are clear

**Success Check:** ✅ All formatting looks good

##### 2.3.5: Deploy to Instance 2

##### 2.3.6: Screenshot

---

#### Step 2.4: Fix response_formatter.py (Priority 4)

**Time Estimate:** 5 mins
**Complexity:** Trivial (1 instance)

##### 2.4.1: Apply Transformation
- Line 191: `f"• {insight}"` → `f"- {insight}"`

##### 2.4.2: Test Locally

##### 2.4.3: Deploy to Both Instances

##### 2.4.4: Test (Minimal - just verify no errors)

---

### PHASE 3: COMPREHENSIVE TESTING (30-45 mins)

#### Step 3.1: End-to-End Workflow Test
1. Fresh session
2. Upload TPR data
3. Complete entire workflow:
   - TPR analysis
   - Risk analysis
   - ITN planning
4. Check all outputs have proper formatting

**Success Check:** ✅ All workflows work, all formatting is clean

---

#### Step 3.2: Visual Comparison
- Compare screenshots before/after for each workflow
- Document improvements in `/tasks/formatting_improvements.md`

**Success Check:** ✅ Clear visual improvement documented

---

#### Step 3.3: Edge Case Testing
- Test with different states (multiple states vs single state)
- Test with different facility levels
- Test with missing data scenarios
- Verify error messages also have proper formatting

**Success Check:** ✅ No formatting regressions in edge cases

---

### PHASE 4: CLEANUP & DOCUMENTATION (15-20 mins)

#### Step 4.1: Update Documentation
- Create `/tasks/DEPLOYMENT_FORMATTING_FIXES.md` with:
  - Date of deployment
  - Files changed
  - Before/after examples
  - Rollback procedure
  - Success metrics

**Success Check:** ✅ Documentation complete

---

#### Step 4.2: Create Rollback Script (Just in Case)
```bash
# Create rollback script for emergency use
cat > /tmp/rollback_formatting.sh <<'EOF'
#!/bin/bash
# Rollback formatting fixes
ssh Instance1 'cp *.backup_formatting_20251006 [original_names] && systemctl restart chatmrpt'
ssh Instance2 'cp *.backup_formatting_20251006 [original_names] && systemctl restart chatmrpt'
EOF

chmod +x /tmp/rollback_formatting.sh
```

**Success Check:** ✅ Rollback script ready (hopefully never needed)

---

#### Step 4.3: Clean Up Old Backups (Optional)
- Decide which old backups to keep
- Remove very old backups if disk space is tight
- Keep all `backup_formatting_20251006` files

**Success Check:** ✅ Disk space managed

---

## 🚨 Risk Mitigation

### What Could Go Wrong?

1. **Syntax Errors in Python Files**
   - **Prevention:** Test locally first
   - **Detection:** Service restart fails
   - **Fix:** Use backup, investigate, re-apply carefully

2. **Broken String Formatting**
   - **Prevention:** Visual review before deploy
   - **Detection:** Empty messages or errors in output
   - **Fix:** Rollback, fix strings, redeploy

3. **Logic Errors (Unlikely)**
   - **Prevention:** Only changing strings, not logic
   - **Detection:** Workflows behave differently
   - **Fix:** Rollback immediately, investigate

4. **Frontend Rendering Issues**
   - **Prevention:** Follow SSE_STREAMING_FORMAT_GUIDE.md exactly
   - **Detection:** Messages still look bad
   - **Fix:** Adjust Markdown syntax, test again

### Rollback Procedure

If ANYTHING breaks:
```bash
# Immediate rollback (< 2 mins)
ssh Instance1:
  cp complete_analysis_tools.py.backup_formatting_20251006 complete_analysis_tools.py
  cp tpr_workflow_handler.py.backup_formatting_20251006 tpr_workflow_handler.py
  cp itn_planning_tools.py.backup_formatting_20251006 itn_planning_tools.py
  cp response_formatter.py.backup_formatting_20251006 response_formatter.py
  sudo systemctl restart chatmrpt

ssh Instance2:
  # Same

# Verify service is healthy
curl http://[ALB]/health
```

---

## ✅ Success Criteria Checklist

### Code Quality:
- [ ] All Python files compile without errors
- [ ] No broken string formatting
- [ ] No logic changes (only formatting changes)

### Formatting Quality:
- [ ] Headings use `##` or `###`
- [ ] Lists use `-` for bullets
- [ ] Blank lines (`\n\n`) between sections
- [ ] No unicode bullets (`•`)
- [ ] No bold as headings (`**Title:**`)

### User Experience:
- [ ] All messages have vertical spacing
- [ ] Text is scannable and hierarchical
- [ ] Lists render properly
- [ ] Professional appearance
- [ ] Matches ChatGPT-style formatting

### Functionality:
- [ ] TPR workflow works end-to-end
- [ ] Risk analysis works correctly
- [ ] ITN planning works correctly
- [ ] No regressions in any workflow
- [ ] Error messages still display properly

### Deployment:
- [ ] Changes deployed to both instances
- [ ] Services restarted successfully
- [ ] Backups created and accessible
- [ ] Rollback script ready
- [ ] Documentation updated

---

## 📅 Timeline

| Phase | Task | Time | Cumulative |
|-------|------|------|-----------|
| 1 | Preparation | 15-20 mins | 20 mins |
| 2.1 | Fix complete_analysis_tools.py | 2 hours | 2h 20m |
| 2.2 | Fix tpr_workflow_handler.py | 45 mins | 3h 5m |
| 2.3 | Fix itn_planning_tools.py | 30 mins | 3h 35m |
| 2.4 | Fix response_formatter.py | 5 mins | 3h 40m |
| 3 | Comprehensive testing | 30-45 mins | 4h 20m |
| 4 | Cleanup & documentation | 15-20 mins | 4h 40m |

**Total Estimated Time:** 4.5-5 hours

**Recommended Schedule:**
- Session 1 (2.5 hours): Phases 1-2.1 (Prep + Risk Analysis)
- Session 2 (2 hours): Phases 2.2-2.4 (TPR + ITN + Formatter)
- Session 3 (1 hour): Phases 3-4 (Testing + Cleanup)

Or complete in one 5-hour session if preferred.

---

## 📝 Notes

- **Follow the reference:** SSE_STREAMING_FORMAT_GUIDE.md is the gold standard
- **Test after each file:** Don't batch changes
- **Keep backups:** We have rollback capability
- **Document everything:** Screenshot before/after
- **Be methodical:** Don't rush, don't skip steps
- **Stay focused:** Fix formatting only, don't change logic

---

## 🎯 Expected Outcome

**Before:** Cramped text, no hierarchy, poor readability
**After:** Clean headings, proper lists, scannable structure

**User Satisfaction:** From "I'm going to fall asleep" to "This looks professional"

---

**Plan Status:** ✅ COMPLETE - AWAITING APPROVAL
**Ready to Execute:** YES (upon approval)
**Risk Level:** 🟡 MEDIUM (reversible)
**Estimated Time:** 4.5-5 hours
**Next Step:** User approval → Execute Phase 1
