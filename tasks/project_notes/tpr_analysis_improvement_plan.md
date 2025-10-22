# TPR System Analysis: What Works vs What Doesn't

## Date: 2025-01-06

## 🟢 What Works (Keep These Foundations)

### 1. TPR Calculation Formula ✅
```python
# Standard TPR (this is correct)
TPR = (Positive Cases / Tested Cases) * 100
Where:
- Tested = max(RDT_Tested, Microscopy_Tested)
- Positive = max(RDT_Positive, Microscopy_Positive)

# Alternative for Urban Areas (when TPR > 50%)
TPR = (Positive Cases / Outpatient Attendance) * 100
```

### 2. Age Group Considerations ✅
- Under 5 (u5)
- Over 5 (o5) 
- Pregnant Women (pw)
- All ages (sum across groups)
- **KEEP**: The logic for handling different age groups

### 3. Geopolitical Zone Variables ✅
```python
ZONE_VARIABLES = {
    'North_East': ['housing_quality', 'evi', 'ndwi', 'soil_wetness'],
    'North_West': ['housing_quality', 'elevation', 'evi', 'distance_to_waterbodies', 'soil_wetness'],
    # etc...
}
```
- **KEEP**: The mapping of which environmental variables matter for each zone

### 4. Data Quality Checks ✅
- Positive cases shouldn't exceed tested
- Tested shouldn't exceed persons with fever
- OPD shouldn't exceed general attendance
- **KEEP**: These logical consistency rules

## 🔴 What Doesn't Work (Fix These)

### 1. Rigid Column Detection ❌
- Hardcoded column name patterns
- No user input when columns can't be found
- Fails silently or crashes

### 2. Ward Name Matching ❌
- Brittle regex cleaning (removes prefixes like 'ad')
- No user verification of fuzzy matches
- No way to correct mismatches

### 3. No Interactive Workflow ❌
- System makes all decisions automatically
- User can't guide the analysis
- No transparency about what's happening

### 4. Inflexible Facility Type Handling ❌
- Can't handle different naming conventions
- No way to specify which facilities to include/exclude
- Urban detection is primitive

### 5. Silent Failures ❌
- When shapefile doesn't match, continues anyway
- When zone variables missing, no notification
- Data quality issues not reported to user

## 💡 New Interactive Conversation Flow

### Phase 1: Data Understanding (Interactive)
```
LLM: "I've loaded your TPR file. I found these columns:
      - State, LGA, Ward, Facility
      - RDT_Tested, RDT_Positive (looks like RDT test data)
      - Microscopy_Tested, Microscopy_Positive (microscopy data)
      - OPD_Attendance (outpatient data)
      
      Which age groups should I analyze?
      1. Under 5 only
      2. Over 5 only
      3. Pregnant women only
      4. All ages combined
      5. Let me look for age-specific columns"

User: "5"

LLM: "I found these age-specific columns:
      - RDT_Tested_U5, RDT_Positive_U5
      - RDT_Tested_O5, RDT_Positive_O5
      
      Should I calculate TPR for:
      1. Each age group separately
      2. All ages combined
      3. Both"
```

### Phase 2: Data Quality Check (Interactive)
```
LLM: "I've found some data quality issues:
      
      ⚠️ 15 facilities where positive > tested:
      - Facility A: 50 positive but only 40 tested
      - Facility B: 30 positive but only 25 tested
      [Show first 5...]
      
      How should I handle these?
      1. Exclude these facilities
      2. Set positive = tested (cap at 100%)
      3. Use alternative calculation (positive/OPD)
      4. Let me investigate further"

User: "4"

LLM: "Looking deeper, these facilities all have high OPD numbers.
      It's possible the tested column is incomplete.
      I recommend using alternative calculation for these.
      Proceed? (yes/no)"
```

### Phase 3: TPR Calculation Method (Interactive)
```
LLM: "For TPR calculation, I can use:
      
      1. Standard: max(RDT, Microscopy) for both positive and tested
      2. RDT only (ignore microscopy)
      3. Microscopy only (more accurate but less coverage)
      4. Custom combination
      
      Note: I found 80% facilities have RDT data, 45% have microscopy.
      What's your preference?"

User: "1"

LLM: "Good choice. For urban areas with high TPR (>50%), should I:
      1. Keep standard calculation
      2. Switch to positive/OPD ratio
      3. Flag them for manual review"
```

### Phase 4: Ward Matching (Interactive)
```
LLM: "I need to match ward names with the shapefile.
      
      ✅ Exact matches: 180/226 wards
      ⚠️ Fuzzy matches found for 35 wards:
      
      TPR Data → Shapefile:
      'Bajoga Ward' → 'Bajoga' (95% confident)
      'Billiri Ward' → 'Billiri' (95% confident)
      'Kaltungo East' → 'Kaltungo' (75% confident)
      
      Should I:
      1. Accept all matches above 90% confidence
      2. Accept all matches above 75% confidence
      3. Review each match with me
      4. Only use exact matches"

User: "3"

LLM: "Let's review uncertain matches:
      
      'Kaltungo East' in your data might match:
      a) 'Kaltungo' in shapefile
      b) 'East Kaltungo' in shapefile
      c) Skip this ward
      
      Which is correct?"
```

### Phase 5: Environmental Variables (Interactive)
```
LLM: "Based on Adamawa being in North-East zone, I should extract:
      - housing_quality
      - evi (vegetation index)
      - ndwi (water index)
      - soil_wetness
      
      I found raster files for:
      ✅ evi: 2023-2024 monthly data
      ✅ ndwi: 2023-2024 monthly data
      ❌ housing_quality: No file found
      ⚠️ soil_wetness: Only 2022 data
      
      Should I:
      1. Use available data only
      2. Skip environmental variables
      3. Use alternative variables"
```

### Phase 6: Results Review (Interactive)
```
LLM: "TPR Analysis Complete! Here's what I found:
      
      📊 Summary Statistics:
      - Average TPR: 31.5%
      - Highest: Yola North (58.3%)
      - Lowest: Demsa (12.1%)
      
      🚨 High Risk Wards (TPR > 40%):
      1. Yola North - 58.3% (urban, using OPD calculation)
      2. Yola South - 45.2%
      3. Girei - 42.1%
      
      ⚠️ Data Quality Notes:
      - 15 wards had incomplete data
      - 10 wards couldn't be matched to shapefile
      
      Would you like to:
      1. Export results as is
      2. Recalculate with different parameters
      3. Investigate specific wards
      4. Add manual corrections"
```

## 🎯 Implementation Strategy

### Core Improvements:

1. **Dynamic Column Detection with User Confirmation**
```python
def detect_columns_interactive(df, llm):
    # LLM analyzes columns
    detected = llm.analyze_columns(df)
    
    # Show user what was found
    response = llm.ask_user(
        f"I detected: {detected}. Is this correct?"
    )
    
    if response == 'no':
        # Let user specify columns
        return llm.get_user_column_mapping()
```

2. **Interactive TPR Calculation**
```python
def calculate_tpr_interactive(data, llm):
    # Check data quality first
    issues = find_data_issues(data)
    
    if issues:
        # Ask user how to handle
        decision = llm.ask_user_about_issues(issues)
        data = apply_user_decision(data, decision)
    
    # Ask about calculation method
    method = llm.ask_calculation_method()
    
    # Calculate with transparency
    results = calculate_with_method(data, method)
    
    # Show intermediate results
    llm.show_results_preview(results)
    
    # Get user confirmation
    if llm.get_confirmation():
        return results
    else:
        # Recalculate with new parameters
        return recalculate_interactive(data, llm)
```

3. **Smart Ward Matching with Verification**
```python
def match_wards_interactive(tpr_data, shapefile, llm):
    # Try exact matching first
    exact_matches = find_exact_matches(tpr_data, shapefile)
    
    # For unmatched, use fuzzy matching
    fuzzy_matches = find_fuzzy_matches(unmatched, shapefile)
    
    # Group by confidence
    high_confidence = [m for m in fuzzy_matches if m.score > 0.9]
    uncertain = [m for m in fuzzy_matches if 0.7 < m.score <= 0.9]
    
    # Auto-accept high confidence
    accepted = exact_matches + high_confidence
    
    # Ask user about uncertain matches
    for match in uncertain:
        decision = llm.ask_user_about_match(match)
        if decision == 'accept':
            accepted.append(match)
    
    return accepted
```

## 📋 Key Principles for New System

1. **Transparency First**
   - Show what the system is doing
   - Explain why decisions are made
   - Let user see intermediate results

2. **User Control**
   - User can override any decision
   - User can choose calculation methods
   - User verifies uncertain matches

3. **Graceful Degradation**
   - Missing data doesn't break the system
   - Provides alternatives when something fails
   - Always produces some result

4. **Educational**
   - Explains TPR concepts as it goes
   - Shows why certain methods are recommended
   - Teaches user about data quality

5. **Flexible**
   - Handles any column naming convention
   - Works with partial data
   - Adapts to user preferences

## 🚀 Next Steps

1. Create conversation flow manager
2. Implement interactive prompts
3. Add user decision tracking
4. Build flexible TPR calculator
5. Create smart ward matcher
6. Test with real user scenarios