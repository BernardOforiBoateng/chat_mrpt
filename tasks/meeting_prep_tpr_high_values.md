# TPR Meeting Preparation - High Values Issue
**Date**: 2025-10-07
**Meeting**: Discussion on TPR Analysis High Values & Catchment Population

---

## 🎯 Meeting Purpose
Discuss why TPR values are too high for microplanning and how to estimate catchment populations for health facilities.

---

## 📊 The Core Problem: TPR Values Are Too High

### Current Situation
Based on the Nigeria TPR analysis completed (337,773 records, 37 states):

**National Average TPR**: 41.49%
- This means **2 in 5 malaria tests are positive**
- This is unusually high for microplanning purposes

**Top High-TPR States**:
1. **Edo State**: 90.3% TPR
2. **Anambra**: 86.8% TPR
3. **Imo State**: 85.5% TPR
4. **Ondo State**: 85.0% TPR
5. **Sokoto State**: 82.7% TPR

**Adamawa State** (your demo example):
- **TPR: 71.9%** (226 wards, 868 facilities)
- Total tests: 961,604
- Positive: 690,999

### Why This Is a Problem

**1. Denominator Issue - Missing Catchment Population**
Currently, TPR calculation is:
```
TPR = (Positive Cases / Tests Conducted) × 100
```

**The problem**: We're only counting people who **came to the facility and were tested**, not the **total population the facility serves**.

**What we need**:
```
True Incidence Rate = (Positive Cases / Catchment Population) × 100
```

**2. Selection Bias**
- Only symptomatic people get tested
- Facilities with high disease burden test more people
- Urban facilities have better access → higher test volumes
- Rural facilities may have limited testing capacity

**3. Unusable for Microplanning**
- ITN (bed net) distribution needs to target **total population at risk**, not just tested individuals
- Can't plan interventions if you don't know the denominator
- 90% TPR doesn't tell you if 100 or 10,000 people are at risk

---

## 🔍 Root Causes (What the Data Shows)

### Data Quality Issues Identified

**1. Incomplete Denominators**
- **Test data completeness**: Only 51% overall
- **RDT data**: 47.4% missing
- **Microscopy data**: 97.9% missing (barely used)
- Many facilities report positive cases but incomplete test counts

**2. Facility-Level Problems**
Found 15+ facilities where **positive > tested** (impossible values)
- Example: 50 positive but only 40 tested
- Indicates data entry errors or incomplete test records

**3. No Population Data**
The NMEP dataset **does NOT include**:
- Catchment population per facility
- Ward-level population estimates
- Household counts
- Coverage denominators

**4. Testing Bias Patterns**
- **Urban areas**: Higher TPR (easier access, more testing)
- **Facility type matters**:
  - Primary facilities: 3.9M tests (80% coverage)
  - Tertiary facilities: Only 6,230 tests
- Only symptomatic patients get tested (no screening)

---

## 💡 Solution: Estimate Catchment Population

### What Grace Was Going to Work On
Estimate the **catchment population** for each health facility - the total number of people the facility is expected to serve.

### Why This Matters
With catchment population, we can calculate:
```
Adjusted Incidence = (Positive Cases / Catchment Population) × 100
Coverage Rate = (Tests Conducted / Catchment Population) × 100
```

This gives us:
1. **True disease burden** (not just test positivity)
2. **Testing coverage** (are we reaching enough people?)
3. **Resource allocation** (how many nets per catchment area)

---

## 🛠️ Proposed Approaches to Estimate Catchment Population

### Option 1: Use Ward Population + Facility Distribution
**Method**:
1. Get ward-level population from census (NPC data)
2. Count number of facilities per ward
3. Divide ward population by facility count
4. Weight by facility type (tertiary gets more)

**Formula**:
```
Catchment_Pop = (Ward_Population / Num_Facilities) × Facility_Weight
Where:
- Primary facility weight = 1.0
- Secondary facility weight = 2.0
- Tertiary facility weight = 3.0
```

**Pros**:
- Simple, uses existing census data
- Works for all facilities

**Cons**:
- Assumes equal distribution (not true in urban areas)
- Doesn't account for cross-ward referrals

---

### Option 2: Voronoi Tessellation (Spatial Catchment)
**Method**:
1. Map all health facilities with GPS coordinates
2. Create Voronoi polygons (areas closest to each facility)
3. Intersect with population density raster
4. Sum population within each facility's catchment area

**Formula**:
```
Catchment_Pop = ∫∫ Population_Density(x,y) dA
Where area A = Voronoi polygon for facility
```

**Pros**:
- Geospatially accurate
- Accounts for facility proximity
- Works for rural areas

**Cons**:
- Requires GPS coordinates for all facilities
- Complex implementation
- May overestimate urban facility catchments

---

### Option 3: Use Attendance Data as Proxy
**Method**:
1. Use **OPD (Outpatient Department) attendance** as denominator
2. Calculate malaria incidence rate among people who visited facility
3. Extrapolate to catchment population using coverage estimates

**Formula**:
```
Adjusted_TPR = (Positive Cases / OPD Attendance) × 100
Estimated_Catchment = OPD_Attendance / Assumed_Coverage_Rate
```

**Pros**:
- Uses existing data (OPD attendance is in dataset)
- Already validated in urban areas with high TPR
- No external data needed

**Cons**:
- Assumes coverage rate (20-40% typical)
- Doesn't work if OPD data is missing
- Biased by facility accessibility

---

### Option 4: Hybrid Model (Recommended)
**Method**: Combine multiple approaches based on data availability

**For Urban Facilities**:
- Use OPD attendance as primary denominator
- Apply typical urban coverage rates (30-50%)

**For Rural Facilities**:
- Use ward population / facility count
- Weight by facility type and accessibility

**For All Facilities**:
- Validate using WorldPop population density rasters
- Cross-check with testing coverage rates

**Implementation**:
```python
def estimate_catchment_population(facility):
    if facility.has_OPD_data and facility.urban_percentage > 50:
        # Urban: Use OPD with coverage factor
        return facility.OPD_attendance / URBAN_COVERAGE_RATE

    elif facility.has_GPS_coords:
        # Rural with GPS: Use spatial catchment
        return calculate_voronoi_catchment(facility)

    else:
        # Fallback: Equal distribution within ward
        ward_pop = get_ward_population(facility.ward)
        num_facilities = count_facilities_in_ward(facility.ward)
        weight = FACILITY_TYPE_WEIGHTS[facility.type]
        return (ward_pop / num_facilities) * weight
```

---

## 📊 Expected Impact on TPR Values

### Current (Without Catchment Population)
**Adamawa Example**:
- TPR: 71.9%
- Interpretation: "72% of tested people have malaria"
- Problem: Only 961,604 tests for entire state

### After Correction (With Catchment Population)
**Adamawa Example** (assuming 4.5M population):
- Malaria Incidence: 15.4% (690,999 / 4,500,000)
- Testing Coverage: 21.4% (961,604 / 4,500,000)
- Interpretation: "15% of population has malaria, we're testing 21%"

**This is more realistic and actionable!**

---

## 🎤 Talking Points for Meeting

### 1. Acknowledge the Problem
"The TPR values we're seeing (40-90%) are too high because we're using **test positivity** instead of **incidence rate**. We need catchment populations to fix this."

### 2. Explain Why It Matters
"For ITN distribution, we need to know how many people live in high-risk areas, not just how many tested positive. Right now, we can't do that."

### 3. Propose the Hybrid Solution
"I recommend a **hybrid approach**: Use OPD for urban facilities, spatial methods for rural facilities, and census data as fallback. This gives us the best coverage with available data."

### 4. Define Data Requirements
"To implement this, we need:
- Ward-level population from NPC census
- GPS coordinates for facilities (or LGA centroids)
- WorldPop raster data for validation
- Facility type classification"

### 5. Discuss Implementation Timeline
"This is a **data engineering task**, not an analysis change. The TPR calculation stays the same, but we add a catchment population column. We can prototype this for Adamawa in 2-3 days."

### 6. Address the Y-Axis Visualization Issue
"For the monthly test plot, I'll shorten the y-axis to focus on the 0-2000 range where most facilities cluster. The current scale (0-10000) hides the distribution details."

### 7. Confirm Reporting Completeness
"Regarding the 12 months of data - yes, all states show 12 monthly reporting periods in 2024. However, **51% of the data is missing**, so 'complete' doesn't mean 'full coverage'."

---

## 📋 Recommended Next Steps

### Immediate (This Week)
1. ✅ **Clarify requirements** with Laurette and Grace
   - Which approach do you prefer?
   - What data sources are available?
   - What's the priority timeline?

2. ✅ **Gather data**
   - NPC census data per ward
   - WorldPop population rasters
   - Facility GPS coordinates (if available)

3. ✅ **Prototype for Adamawa**
   - Test hybrid model on single state
   - Validate results against known population
   - Show before/after TPR comparison

### Short-term (Next 2 Weeks)
4. **Scale to all states**
   - Apply catchment estimation nationwide
   - Add to ChatMRPT tool as new feature
   - Update TPR calculation to include incidence rate

5. **Validate results**
   - Compare with WHO estimates
   - Cross-check with NMEP historical data
   - Review with epidemiology experts

### Long-term (Next Month)
6. **Integrate into microplanning**
   - Update ITN allocation algorithm
   - Use incidence rate instead of TPR
   - Add catchment population to risk scoring

---

## 🔧 Technical Implementation Plan

### Phase 1: Data Collection
```python
# Required datasets
- nigeria_ward_population.csv (from NPC)
- nigeria_facilities_gps.csv (from NMEP)
- worldpop_nigeria_2024.tif (from WorldPop)
- facility_types.csv (Primary/Secondary/Tertiary)
```

### Phase 2: Catchment Estimation Function
```python
def estimate_facility_catchment(
    facility_id,
    ward_population,
    facility_coords,
    OPD_attendance,
    facility_type,
    urban_percentage
):
    """
    Estimate catchment population using hybrid model
    Returns: (catchment_pop, method_used, confidence_score)
    """
    # Implementation per Option 4
    pass
```

### Phase 3: Update TPR Calculation
```python
def calculate_adjusted_tpr(
    positive_cases,
    tests_conducted,
    catchment_population
):
    """
    Returns:
    - TPR (test positivity rate)
    - Incidence (disease rate in population)
    - Coverage (testing coverage)
    """
    tpr = (positive_cases / tests_conducted) * 100
    incidence = (positive_cases / catchment_population) * 100
    coverage = (tests_conducted / catchment_population) * 100

    return {
        'tpr': tpr,
        'incidence': incidence,
        'coverage': coverage
    }
```

### Phase 4: Validation & Testing
- Compare with WHO Nigeria estimates (15-25% incidence expected)
- Validate against DHS survey data
- Review ward-level results for outliers

---

## ❓ Questions to Ask in Meeting

### Data Availability
1. Do we have access to **NPC census data** at ward level?
2. Are **facility GPS coordinates** available in DHIS2/NMEP database?
3. Can we use **WorldPop** or **GRID3** population rasters?

### Methodological Preferences
4. Which catchment estimation approach does the team prefer?
5. Should we prioritize **speed** (simple ward division) or **accuracy** (spatial modeling)?
6. What's the acceptable **margin of error** for catchment estimates?

### Implementation Timeline
7. When do you need usable TPR values for microplanning?
8. Should we prototype on Adamawa first or go straight to all states?
9. Who will validate the catchment population estimates?

### Integration
10. Will this be added to **ChatMRPT tool** or separate analysis?
11. Should the tool allow users to **upload their own catchment data**?
12. Do we need to document this methodology for NMEP/WHO?

---

## 📚 Supporting References

### Nigeria Population Data Sources
- **National Population Commission (NPC)**: Census projections
- **WorldPop**: High-resolution population density (100m grid)
- **GRID3**: Settlement-level population estimates
- **DHS (Demographic Health Survey)**: Household-level data

### Catchment Population Methods (Literature)
- WHO Guideline: "Estimating health facility catchment areas" (2021)
- Malaria Atlas Project: Spatial accessibility modeling
- MEASURE Evaluation: "Service area analysis for health facilities"

### Typical Catchment Population Ranges
- **Primary Health Center**: 5,000-20,000 people
- **Secondary Hospital**: 50,000-200,000 people
- **Tertiary Hospital**: 500,000+ people

---

## 🎯 Success Metrics

After implementing catchment population estimates:

✅ **TPR values will be supplemented with**:
- Malaria incidence rate (more realistic 10-25% range)
- Testing coverage rate (helps identify gaps)
- Population at risk (for ITN allocation)

✅ **Microplanning becomes possible**:
- Calculate nets needed per catchment area
- Identify under-tested populations
- Prioritize high-incidence facilities

✅ **Data quality improves**:
- Flag facilities with impossible ratios
- Validate reporting completeness
- Standardize across states

---

## 💬 Meeting Talking Points Summary

**Opening**: "Thank you for the feedback. The high TPR values (71% for Adamawa, 41% nationally) are indeed too high for microplanning because they reflect **test positivity**, not **population incidence**. We need catchment populations to convert this into usable metrics."

**Problem**: "Right now, a 71% TPR means '71% of people tested have malaria,' but we don't know how many people the facility serves. So we can't calculate how many nets to distribute or where the highest disease burden really is."

**Solution**: "I propose a **hybrid catchment estimation model**: Use OPD attendance for urban facilities, spatial methods for rural facilities with GPS, and census-based allocation as fallback. This gives us the best coverage."

**Data Needs**: "To implement this, we need: (1) Ward population from NPC census, (2) Facility GPS coordinates if available, and (3) WorldPop rasters for validation. Do we have access to these?"

**Timeline**: "We can prototype this for Adamawa in 2-3 days to validate the approach, then scale to all 37 states within 2 weeks."

**On Visualizations**: "For the monthly tests plot - yes, I'll shorten the y-axis to show the 0-2000 range where most facilities cluster. And yes, all 12 months are reported per state, though overall data completeness is 51%."

**Next Steps**: "After this meeting, I'll need clarity on: (1) Which approach you prefer, (2) What data sources are available, and (3) Whether we integrate this into ChatMRPT or keep it as a separate preprocessing step."

**Closing**: "This is a solvable problem - it's a data engineering task, not a fundamental flaw in the analysis. The TPR calculations are correct; we just need to add the right denominator to make them actionable for microplanning."

---

## 📎 Appendix: Key Data Files

### Analyzed Data
- `state_tpr_summary.csv`: State-level TPR values (37 states)
- `tpr_analysis_key_findings.md`: National TPR analysis results
- `summary_statistics.csv`: Data completeness by column
- Context demo: Adamawa state TPR workflow example

### Supporting Documents
- `tpr_analysis_improvement_plan.md`: Interactive workflow redesign
- `tpr_analysis_investigation_results.md`: Ward matching issues
- `tpr_analysis_column_meanings.md`: Data dictionary

---

**Prepared by**: Bernard Boateng
**Last Updated**: 2025-10-07
**Meeting Attendees**: Bernard, Laurette Mhlanga, Grace Legris (TBD)
