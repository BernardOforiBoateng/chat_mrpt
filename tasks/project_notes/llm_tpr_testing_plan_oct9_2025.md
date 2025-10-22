# LLM-Driven TPR Workflow Testing Plan

**Date**: October 9, 2025
**Deployment Status**: ✅ Deployed to both production instances
**CloudFront URL**: https://d225ar6c86586s.cloudfront.net
**Test Environment**: Production (CloudFront CDN)

---

## Deployment Summary

✅ **Successfully deployed** to both production instances:
- Instance 1 (3.21.167.170): Service restarted at 19:22:53 UTC
- Instance 2 (18.220.103.20): Service restarted at 19:22:56 UTC

**Files Deployed**:
1. `app/data_analysis_v3/core/tpr_language_interface.py` (213 lines)
2. `app/data_analysis_v3/tpr/workflow_manager.py` (1,481 lines)

---

## Testing Objectives

### Primary Goals
1. Verify natural language understanding works for TPR selections
2. Test LLM slot resolution accuracy and confidence scoring
3. Validate rationale messages display correctly
4. Confirm fallback behavior when LLM confidence is low
5. Ensure backward compatibility with keyword-based inputs

### Success Criteria
- ✅ State selection works with natural language (e.g., "analyze Kano")
- ✅ Facility selection works with natural language (e.g., "I want secondary facilities")
- ✅ Age group selection works with natural language (e.g., "under five children")
- ✅ System provides clear rationale for interpretations
- ✅ Low-confidence inputs trigger clarification prompts
- ✅ Original keyword inputs still work ("primary", "u5", etc.)

---

## Test Plan

### Phase 1: Data Upload Test

**URL**: https://d225ar6c86586s.cloudfront.net

**Steps**:
1. Open CloudFront URL in browser
2. Navigate to "Data Analysis" tab
3. Upload test CSV file with malaria testing data
   - Should contain: State, LGA, Ward, Facility, Test data columns
   - Recommended: Use Kano State data for consistency with existing tests
4. Verify data loads successfully
5. Check data overview displays correctly (first 5 columns)

**Expected Result**:
- Data uploads without errors
- System displays data summary
- "Run TPR analysis" option is available

---

### Phase 2: TPR Workflow - Natural Language Testing

#### Test 2.1: Natural Language State Selection

**Trigger**: Say "run TPR analysis" or click TPR button

**Natural Language Inputs to Test**:
1. "I want to analyze Kano"
2. "Let's look at Kano State"
3. "analyze kano"
4. "Can we do Kano?"
5. "Kano please"

**Expected Behavior**:
- System resolves input to "Kano State"
- Displays acknowledgment: "Great choice! You've selected **Kano State**..."
- Shows rationale: "_I interpreted your selection as Kano State: [LLM rationale]_"
- Proceeds to facility level selection

**Fallback Test**:
- Input: "I want to analyze xyz" (non-existent state)
- Expected: "I want to be sure I understood you correctly. Could you rephrase which state you'd like to analyze?"

#### Test 2.2: Natural Language Facility Selection

**Natural Language Inputs to Test**:
1. "I want secondary facilities"
2. "Let's use secondary level"
3. "secondary please"
4. "Can we do secondary?"
5. "I prefer secondary facilities"
6. "secondary"
7. "2" (numeric choice)

**Expected Behavior**:
- System resolves to "secondary"
- Displays: "Perfect! You've selected **Secondary** facilities..."
- Shows rationale: "_I mapped your reply to Secondary: [LLM rationale]_"
- Proceeds to age group selection

**Fallback Test**:
- Input: "I want the middle ones" (ambiguous)
- Expected: Clarification prompt with choices listed

#### Test 2.3: Natural Language Age Group Selection

**Natural Language Inputs to Test**:
1. "under five children"
2. "children less than 5 years"
3. "kids under 5"
4. "u5 please"
5. "under fives"
6. "pregnant women"
7. "expecting mothers"
8. "over 5 years old"
9. "adults and older children"

**Expected Behavior**:
- System resolves to correct age group ("u5", "pw", or "o5")
- Displays: Acknowledgment with test count
- Shows rationale: "_I treated your request as [age group] based on: [LLM rationale]_"
- Begins TPR calculation

**Fallback Test**:
- Input: "the young ones" (ambiguous)
- Expected: Clarification with "Under 5, Over 5, Pregnant women, All ages" choices

---

### Phase 3: Keyword Compatibility Testing

**Purpose**: Ensure backward compatibility with existing keyword inputs

#### Test 3.1: Exact Keywords Still Work

**State Selection**:
- Input: "Kano State" (exact match)
- Expected: Immediate resolution, no LLM call needed

**Facility Selection**:
- Input: "primary", "secondary", "tertiary", "all"
- Expected: Instant resolution

**Age Group Selection**:
- Input: "u5", "o5", "pw", "all_ages"
- Expected: Instant resolution

---

### Phase 4: Edge Cases and Error Handling

#### Test 4.1: Empty/Invalid Inputs

**Test Cases**:
1. Empty input (just press Enter)
2. Special characters only: "!!!", "@#$%"
3. Very long input (300+ characters)
4. Non-English characters: "分析", "анализ"

**Expected Behavior**:
- Graceful handling with clarification prompt
- No crashes or errors
- Clear guidance to user

#### Test 4.2: Ambiguous Inputs

**Test Cases**:
1. "I'm not sure" (state selection)
2. "Maybe secondary or tertiary" (facility selection)
3. "All children" (age group - ambiguous between u5 and o5)

**Expected Behavior**:
- Low confidence score from LLM
- Clarification prompt with available choices
- Helpful rationale explaining the ambiguity

#### Test 4.3: Conversational Inputs

**Test Cases**:
1. "Well, I think maybe we should analyze Kano" (state)
2. "Hmm, I want to use, let's say, secondary facilities" (facility)
3. "Yeah, let's go with under five kids for now" (age group)

**Expected Behavior**:
- LLM extracts correct choice despite conversational filler
- High confidence score (>0.8)
- Natural rationale message

---

### Phase 5: End-to-End Workflow Test

**Scenario**: Complete TPR workflow using only natural language

**Steps**:
1. Upload data → Say "run TPR analysis"
2. State: "Let's analyze Kano State"
3. Facility: "I want to use secondary level facilities"
4. Age Group: "Under five children please"
5. Wait for TPR calculation
6. Verify TPR map displays
7. Check download files available
8. Confirm transition prompt for risk analysis

**Expected Result**:
- Seamless workflow completion
- All natural language inputs resolved correctly
- Rationale messages provide transparency
- TPR results calculated and displayed
- Map visualization loads
- Download links work

---

## Test Data Requirements

### Recommended Test Dataset

**File**: Sample Kano State malaria testing data (CSV)

**Required Columns**:
- `State` or `StateName`: "Kano State"
- `LGA` or `LGAName`: e.g., "Kano Municipal"
- `Ward` or `WardName`: e.g., "Gandun Albasa"
- `FacilityName`: e.g., "Gandun Albasa PHC"
- `FacilityLevel`: "Primary", "Secondary", or "Tertiary"
- Test data columns:
  - `U5_RDT_Positive`, `U5_RDT_Tested`
  - `O5_RDT_Positive`, `O5_RDT_Tested`
  - `PW_RDT_Positive`, `PW_RDT_Tested`
  - (Similar for Microscopy if available)

**Minimum Requirements**:
- At least 10 wards
- At least 50 facilities
- Variety of facility levels (Primary, Secondary, Tertiary)
- Complete test data (no excessive nulls)

---

## Testing Checklist

### Pre-Test Setup
- [ ] CloudFront URL accessible
- [ ] Test data file prepared
- [ ] Browser console open (F12) to monitor errors
- [ ] Network tab open to check API calls

### Test Execution
- [ ] **Data Upload** - File uploads successfully
- [ ] **TPR Start** - Workflow initiates correctly
- [ ] **State Selection (NL)** - "analyze Kano" works
- [ ] **State Selection (Keyword)** - "Kano State" works
- [ ] **Facility Selection (NL)** - "secondary facilities" works
- [ ] **Facility Selection (Keyword)** - "secondary" works
- [ ] **Age Group (NL)** - "under five children" works
- [ ] **Age Group (Keyword)** - "u5" works
- [ ] **Rationale Display** - Rationale messages show correctly
- [ ] **Clarification Prompts** - Low-confidence inputs ask for clarification
- [ ] **TPR Calculation** - Completes successfully
- [ ] **Map Display** - TPR map renders
- [ ] **Downloads** - CSV and shapefile links work
- [ ] **Edge Cases** - Empty/invalid inputs handled gracefully

### Post-Test Verification
- [ ] Check browser console for errors
- [ ] Verify no 500 errors in Network tab
- [ ] Confirm LLM API calls completed (check timing)
- [ ] Review confidence scores in rationale messages
- [ ] Test on mobile browser (responsive design)

---

## Monitoring and Logging

### CloudWatch Logs to Check

**After testing, SSH to instances and check logs**:

```bash
# SSH to Instance 1
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170

# Check application logs
sudo journalctl -u chatmrpt -f --since "5 minutes ago"

# Grep for LLM-related logs
sudo journalctl -u chatmrpt --since "10 minutes ago" | grep -i "resolve_slot\|classify_intent\|TPRLanguageInterface"

# Check for errors
sudo journalctl -u chatmrpt --since "10 minutes ago" | grep -i "error\|exception\|traceback"
```

**Key Log Patterns to Look For**:
- ✅ `Resolved facility level: secondary (confidence=0.95)`
- ✅ `Resolved age group: u5 (confidence=0.92)`
- ✅ `Intent classification: start (confidence=0.85)`
- ⚠️ `Slot resolution fallback` (indicates LLM unavailable)
- ❌ `Error` or `Exception` (indicates bugs)

### Performance Metrics

**Expected Timings**:
- Keyword match: ~20ms
- LLM slot resolution: 2-5 seconds
- Total TPR calculation: 10-30 seconds (depending on data size)

**Monitor**:
- LLM API call latency
- Overall workflow completion time
- Any timeout errors

---

## Troubleshooting Guide

### Issue: LLM Not Resolving Natural Language

**Symptoms**:
- Only exact keywords work
- Natural language inputs always ask for clarification

**Possible Causes**:
1. `OPENAI_API_KEY` not set in production environment
2. LLM initialization failed
3. Network issues blocking OpenAI API

**Resolution**:
```bash
# SSH to instance
ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170

# Check environment variable
sudo cat /etc/systemd/system/chatmrpt.service | grep OPENAI_API_KEY

# Check logs for LLM initialization
sudo journalctl -u chatmrpt --since "10 minutes ago" | grep "OPENAI_API_KEY\|TPRLanguageInterface"
```

### Issue: All Inputs Have Low Confidence

**Symptoms**:
- Every input triggers clarification
- Confidence scores always < 0.6

**Possible Causes**:
- LLM model temperature too high
- Prompt template issues
- Choice mismatch (LLM suggesting choices not in the list)

**Resolution**:
- Check LLM temperature setting (should be 0 in tpr_language_interface.py:62)
- Verify choices passed to `resolve_slot()` are correct
- Review LLM rationale messages for clues

### Issue: Service Crashes After Deployment

**Symptoms**:
- 502 Bad Gateway errors
- Service status shows "failed"

**Resolution**:
```bash
# Check service status
sudo systemctl status chatmrpt

# View error logs
sudo journalctl -u chatmrpt -n 100 --no-pager

# Restart service
sudo systemctl restart chatmrpt

# If syntax errors, rollback
cd /home/ec2-user
tar -xzf ChatMRPT_BEFORE_LLM_REFACTOR_*.tar.gz
sudo systemctl restart chatmrpt
```

---

## Test Results Template

### Test Session Details
- **Date**: [Fill in]
- **Tester**: [Fill in]
- **Browser**: [Chrome/Firefox/Safari version]
- **Start Time**: [Fill in]
- **End Time**: [Fill in]

### Results Summary

| Test Case | Input | Expected | Actual | Status | Notes |
|-----------|-------|----------|--------|--------|-------|
| State NL | "analyze Kano" | Resolves to "Kano State" | | ✅/❌ | |
| State Keyword | "Kano State" | Instant resolution | | ✅/❌ | |
| Facility NL | "secondary facilities" | Resolves to "secondary" | | ✅/❌ | |
| Facility Keyword | "secondary" | Instant resolution | | ✅/❌ | |
| Age NL | "under five children" | Resolves to "u5" | | ✅/❌ | |
| Age Keyword | "u5" | Instant resolution | | ✅/❌ | |
| Ambiguous Input | "the young ones" | Clarification prompt | | ✅/❌ | |
| End-to-End | Full natural language | Complete workflow | | ✅/❌ | |

### Issues Found
[List any bugs, unexpected behavior, or UX issues]

### Recommendations
[Suggest improvements based on testing]

---

## Next Steps After Testing

### If Tests Pass
1. ✅ Update CLAUDE.md with LLM architecture
2. ✅ Document confidence threshold tuning (if needed)
3. ✅ Create user-facing documentation for natural language features
4. ✅ Plan next iteration improvements (semantic memory, multi-turn reasoning)

### If Tests Fail
1. ❌ Document failure scenarios
2. ❌ Collect logs and error messages
3. ❌ Identify root cause (syntax, logic, API, etc.)
4. ❌ Fix issues and redeploy
5. ❌ Re-test until all tests pass

---

## Contact for Support

**If issues found during testing**:
1. Document the exact steps to reproduce
2. Capture browser console logs
3. Save CloudWatch logs from affected instances
4. Create issue report in `tasks/project_notes/`
5. Consider rollback if critical production impact

---

## Conclusion

This testing plan ensures comprehensive validation of the LLM-driven TPR refactoring across:
- ✅ Natural language understanding
- ✅ Slot resolution accuracy
- ✅ Backward compatibility
- ✅ Edge case handling
- ✅ End-to-end workflow

**Deployment Status**: ✅ READY FOR TESTING

**CloudFront URL**: https://d225ar6c86586s.cloudfront.net

**Test Now!** 🚀
