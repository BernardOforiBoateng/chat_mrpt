# TPR Workflow Test Instructions

## Changes Deployed (2025-10-01)

### Fixed Issues:
1. **Facility Statistics Display** - Now shows test counts (RDT + Microscopy) for each facility level
2. **Formatter Usage** - Bridge code now uses proper `MessageFormatter` instead of manual message building
3. **Data Structure** - Fixed incorrect key access (`levels` not `facility_levels`)
4. **Test Count Calculation** - Properly sums RDT and Microscopy tests from data_analyzer

### Files Updated:
- `app/web/routes/data_analysis_v3_routes.py` (lines 464-484)
- `app/data_analysis_v3/core/formatters.py` (lines 55-130)

## Manual Testing Instructions

### Option 1: Using Python Test Script

```bash
# Activate virtual environment
source chatmrpt_venv_new/bin/activate

# Run test
python tests/simple_tpr_test.py
```

**Steps:**
1. Script will prompt to upload data first
2. Go to https://d225ar6c86586s.cloudfront.net
3. Upload a TPR CSV file (with State, FacilityLevel, RDT_Tested_*, etc.)
4. Return to terminal and press Enter
5. Script will run through all workflow steps

### Option 2: Manual Web Testing

1. **Upload TPR Data**
   - Go to https://d225ar6c86586s.cloudfront.net
   - Upload TPR CSV file

2. **Start TPR Workflow**
   - Type: `tpr` or `start tpr workflow`
   - **Verify**: Introduction shows workflow explanation, 3 steps, post-calculation info
   - **Verify**: Confirmation prompt appears ("Ready to begin?")

3. **Confirm**
   - Type: `yes` or `continue`
   - **Verify**: State auto-selected (e.g., "Adamawa (auto-selected)")
   - **Verify**: Facility selection appears

4. **Check Facility Statistics**
   - Type: `what are my options?` or just read current message
   - **Verify**: Each facility level shows:
     - Facility name (Primary, Secondary, Tertiary)
     - Facility count
     - **Test count (NOT ZERO!)**
     - "(Recommended)" marker on Primary
   - **Verify**: "all" option at the end

5. **Select Facility**
   - Type: `primary`
   - **Verify**: Moves to age group selection

6. **Check Age Group Statistics**
   - Type: `show age groups` or read current message
   - **Verify**: Shows u5, o5, pw options
   - **Verify**: Test counts and TPR% displayed
   - **Verify**: "(Recommended)" on u5

7. **Test Visualizations (Key Phrase)**
   - Type: `show charts` or `show data`
   - **Verify**: Visualizations are returned (NOT auto-shown earlier)

8. **Select Age Group**
   - Type: `u5`
   - **Verify**: TPR calculation completes
   - **Verify**: Shows ward-level results
   - **Verify**: Transition prompt appears

9. **Transition to Risk**
   - Type: `continue` or `yes`
   - **Verify**: Risk analysis starts
   - **Verify**: Environmental variables mentioned

## What to Look For

### ✅ SUCCESS Criteria:
- [ ] Facility statistics show **non-zero test counts**
- [ ] Format: `- **primary** (Recommended) - Primary\n  - XX facilities, YYY,YYY tests`
- [ ] Recommended markers appear (Primary for facilities, u5 for age)
- [ ] Visualizations appear **only when requested** with key phrases
- [ ] All stages complete without errors
- [ ] Smooth transition from TPR → Risk Analysis

### ❌ FAILURE Indicators:
- [ ] "0 tests" or "0 total tests" in facility selection
- [ ] Missing facility statistics
- [ ] No recommended markers
- [ ] 500/502 errors
- [ ] Visualizations auto-show without request
- [ ] Workflow gets stuck

## Expected Output Examples

### Facility Selection (CORRECT):
```
**State:** Adamawa (auto-selected)

Now, which health facility level would you like to analyze?

- **primary** (Recommended) - Primary
  - 60 facilities, 8,500 tests
- **secondary** - Secondary
  - 30 facilities, 3,200 tests
- **tertiary** - Tertiary
  - 10 facilities, 1,100 tests

- **all** - All Facilities Combined
  - 100 facilities

**Need help deciding?** Ask me to show you visualizations or explain the differences.

Type: **primary**, **secondary**, **tertiary**, or **all**
```

### Age Group Selection (CORRECT):
```
Perfect! **Primary facilities** selected.

## Step 2: Choose Age Group

Select which age group to analyze. Here's what your data contains:

- **u5** (Recommended) - Under 5 years
  - 5,000 tests, TPR: 15.2%
- **o5** - Over 5 years
  - 3,500 tests, TPR: 8.7%
- **pw** - Pregnant Women
  - 800 tests, TPR: 12.3%

- **all** - All age groups combined
  - 9,300 total tests

**Need help deciding?** Ask me to show you visualizations or explain the differences.

Type: **u5**, **o5**, **pw**, or **all**
```

## Troubleshooting

### If statistics are still missing:
1. Check server logs:
   ```bash
   ssh -i /tmp/chatmrpt-key2.pem ec2-user@3.21.167.170 'sudo journalctl -u chatmrpt -f'
   ```

2. Verify data structure:
   ```python
   # The analyze_facility_levels() should return:
   {
       'levels': {
           'primary': {'count': XX, 'rdt_tests': YY, 'microscopy_tests': ZZ, ...},
           ...
       }
   }
   ```

3. Check formatter is extracting correctly:
   ```python
   rdt_tests = level_data.get('rdt_tests', 0)
   microscopy_tests = level_data.get('microscopy_tests', 0)
   total_tests = rdt_tests + microscopy_tests
   ```

### If 502 errors occur:
- Worker timeout (increase in gunicorn_config.py)
- Check if TPR analyzer is taking too long
- Verify data file size is reasonable

## Next Steps After Testing

If all tests pass:
1. Mark this fix as verified and complete
2. Document in project notes
3. Close related issues

If tests fail:
1. Capture exact error messages
2. Check server logs for tracebacks
3. Verify data format matches expected structure
4. Debug specific failing step
