# Catchment Population Implementation Roadmap
**Technical Plan for Adding Catchment Population to TPR Analysis**

---

## 📋 Executive Summary

**Goal**: Add catchment population estimates to TPR analysis to convert test positivity rates into actionable population incidence rates for microplanning.

**Impact**: Transforms TPR from 40-90% (unusable) to 10-25% incidence (realistic and actionable).

**Timeline**: 2-3 weeks from data gathering to full deployment.

**Complexity**: Medium (data engineering + spatial analysis + validation).

---

## 🎯 Project Phases

### Phase 1: Data Collection (Days 1-3)
**Status**: 🟡 Waiting on data sources

#### Required Datasets

| Dataset | Source | Format | Priority | Status |
|---------|--------|--------|----------|--------|
| Ward population | NPC Census 2024 | CSV | HIGH | 🔴 Not acquired |
| Facility GPS | NMEP/DHIS2 | CSV | MEDIUM | 🔴 Not acquired |
| WorldPop raster | worldpop.org | GeoTIFF | MEDIUM | 🟢 Can download |
| Facility types | NMEP | CSV | LOW | 🟢 In dataset |
| OPD attendance | NMEP | CSV | HIGH | 🟢 In dataset |

#### Data Collection Tasks
- [ ] **Contact NPC** for ward-level population projections (2024)
- [ ] **Extract facility GPS** from DHIS2 or NMEP database
- [ ] **Download WorldPop** Nigeria 2024 population raster (100m resolution)
- [ ] **Verify facility types** in current NMEP dataset
- [ ] **Confirm OPD data** completeness in TPR dataset

---

### Phase 2: Prototype Development (Days 4-7)
**Status**: 🔴 Not started (waiting on Phase 1)

#### Adamawa Pilot Implementation

**Objective**: Build and validate catchment estimation for single state (226 wards, 868 facilities).

#### Technical Components

**1. Catchment Estimation Engine**
```python
# File: app/analysis/catchment_estimator.py

class CatchmentEstimator:
    """
    Estimates facility catchment populations using hybrid model
    """

    def __init__(self, ward_populations, facility_data, population_raster):
        self.ward_pops = ward_populations
        self.facilities = facility_data
        self.pop_raster = population_raster

    def estimate(self, facility_id):
        """
        Main estimation function
        Returns: (catchment_pop, method, confidence)
        """
        facility = self.facilities[facility_id]

        # Method 1: Urban + OPD data
        if facility['urban_percentage'] > 50 and facility['OPD_attendance'] > 0:
            return self._estimate_from_opd(facility)

        # Method 2: Rural + GPS coordinates
        elif facility['has_gps'] and facility['urban_percentage'] <= 50:
            return self._estimate_spatial(facility)

        # Method 3: Fallback - Equal ward distribution
        else:
            return self._estimate_from_ward(facility)

    def _estimate_from_opd(self, facility):
        """
        Urban method: Use OPD attendance as proxy
        Assumes 30-50% of catchment population visits facility annually
        """
        opd = facility['OPD_attendance']
        coverage_rate = 0.35  # Conservative estimate

        catchment = opd / coverage_rate
        confidence = 'medium' if opd > 1000 else 'low'

        return catchment, 'opd_based', confidence

    def _estimate_spatial(self, facility):
        """
        Rural method: Voronoi tessellation + population raster
        """
        # Create Voronoi polygon for facility
        voronoi_poly = self._create_voronoi_polygon(facility)

        # Extract population from raster within polygon
        catchment = self._sum_population_in_polygon(
            voronoi_poly,
            self.pop_raster
        )

        confidence = 'high'
        return catchment, 'spatial', confidence

    def _estimate_from_ward(self, facility):
        """
        Fallback: Divide ward population by number of facilities
        Weight by facility type
        """
        ward_pop = self.ward_pops[facility['ward_code']]
        num_facilities = self._count_facilities_in_ward(facility['ward_code'])

        # Facility type weights
        weights = {'Primary': 1.0, 'Secondary': 2.0, 'Tertiary': 3.0}
        weight = weights.get(facility['type'], 1.0)

        # Calculate total weight in ward
        total_weight = sum(
            weights.get(f['type'], 1.0)
            for f in self._get_ward_facilities(facility['ward_code'])
        )

        # Proportional allocation
        catchment = (ward_pop * weight) / total_weight
        confidence = 'low'

        return catchment, 'ward_based', confidence

    def _create_voronoi_polygon(self, facility):
        """Create Voronoi polygon using scipy.spatial"""
        from scipy.spatial import Voronoi
        import geopandas as gpd

        # Get all facility coordinates in state
        points = self.facilities[['longitude', 'latitude']].values

        # Compute Voronoi diagram
        vor = Voronoi(points)

        # Extract polygon for this facility
        # (Implementation details omitted for brevity)
        return voronoi_polygon

    def _sum_population_in_polygon(self, polygon, raster):
        """Extract population from raster within polygon bounds"""
        import rasterio
        from rasterio.mask import mask

        with rasterio.open(raster) as src:
            out_image, out_transform = mask(src, [polygon], crop=True)
            population = out_image.sum()

        return population
```

**2. Updated TPR Calculator**
```python
# File: app/analysis/tpr_calculator_v2.py

def calculate_adjusted_metrics(facility_data, catchment_population):
    """
    Calculate TPR + new incidence and coverage metrics
    """
    positive = facility_data['total_positive']
    tested = facility_data['total_tested']

    # Original TPR (unchanged)
    tpr = (positive / tested * 100) if tested > 0 else 0

    # NEW: Incidence rate (per catchment population)
    incidence = (positive / catchment_population * 100) if catchment_population > 0 else 0

    # NEW: Testing coverage
    coverage = (tested / catchment_population * 100) if catchment_population > 0 else 0

    return {
        'tpr': tpr,
        'incidence': incidence,
        'coverage': coverage,
        'catchment_population': catchment_population,
        'positive_cases': positive,
        'tests_conducted': tested
    }
```

**3. Validation Module**
```python
# File: app/analysis/catchment_validator.py

class CatchmentValidator:
    """
    Validate catchment estimates against known benchmarks
    """

    def validate_state_total(self, state_code, facility_catchments):
        """
        Check if sum of catchments ≈ state population
        """
        total_catchment = sum(facility_catchments.values())
        state_population = self._get_state_population(state_code)

        ratio = total_catchment / state_population

        if 0.8 <= ratio <= 1.2:
            return 'PASS', ratio
        else:
            return 'FAIL', ratio

    def validate_facility_range(self, facility_type, catchment):
        """
        Check if catchment is within expected range for facility type
        """
        ranges = {
            'Primary': (2000, 30000),
            'Secondary': (30000, 250000),
            'Tertiary': (200000, 2000000)
        }

        min_pop, max_pop = ranges.get(facility_type, (0, float('inf')))

        if min_pop <= catchment <= max_pop:
            return 'PASS'
        elif catchment < min_pop:
            return 'LOW'
        else:
            return 'HIGH'

    def validate_incidence_rate(self, incidence):
        """
        Check if calculated incidence is within WHO expected range
        """
        # WHO Nigeria estimates: 10-30% malaria incidence
        if 5 <= incidence <= 40:
            return 'PASS'
        else:
            return 'REVIEW'
```

#### Prototype Deliverables
- [ ] Working catchment estimator for Adamawa
- [ ] Validation report comparing 3 methods
- [ ] Updated TPR results with incidence rates
- [ ] Documentation of assumptions and limitations

---

### Phase 3: Testing & Validation (Days 8-10)
**Status**: 🔴 Not started

#### Validation Checklist

**1. State-Level Validation**
- [ ] Sum of facility catchments ≈ Adamawa population (4.5M)
- [ ] Average catchment per facility: 5,000-15,000 (reasonable)
- [ ] Urban vs rural catchment differences align with expectations

**2. Incidence Rate Validation**
- [ ] Incidence rates fall in 10-25% range (realistic)
- [ ] High-TPR facilities now show reasonable incidence
- [ ] Spatial patterns match known malaria hotspots

**3. Coverage Rate Validation**
- [ ] Testing coverage: 15-40% (typical for Nigeria)
- [ ] Urban facilities have higher coverage than rural
- [ ] Low-coverage facilities flagged for intervention

**4. Method Comparison**
| Method | Facilities | Avg Catchment | Confidence |
|--------|-----------|---------------|------------|
| OPD-based | ~200 | 12,000 | Medium |
| Spatial | ~400 | 8,000 | High |
| Ward-based | ~268 | 10,000 | Low |

**5. Edge Cases**
- [ ] Facilities with missing OPD data
- [ ] Facilities without GPS coordinates
- [ ] Wards with only 1 facility
- [ ] Cross-ward referral patterns

#### Validation Outputs
- [ ] Validation report (pass/fail for each method)
- [ ] Comparison with WHO/NMEP benchmarks
- [ ] List of outliers requiring manual review
- [ ] Confidence scores per facility

---

### Phase 4: Scale to All States (Days 11-17)
**Status**: 🔴 Not started

#### Scaling Strategy

**1. Parallel Processing**
```python
# Process all 37 states in parallel
from multiprocessing import Pool

def process_state(state_code):
    estimator = CatchmentEstimator(state_code)
    results = estimator.estimate_all_facilities()
    return results

with Pool(processes=8) as pool:
    all_results = pool.map(process_state, state_codes)
```

**2. Quality Control**
- Run validation checks for each state
- Flag states with >20% outliers
- Manual review for failing states

**3. Data Storage**
```python
# Output schema: facility_catchment_populations.csv
columns = [
    'facility_id',
    'state', 'lga', 'ward',
    'catchment_population',
    'estimation_method',
    'confidence_score',
    'validation_status'
]
```

#### Deliverables
- [ ] Catchment populations for all 27,929 facilities
- [ ] State-level validation reports (37 states)
- [ ] Outlier list for manual review
- [ ] Data quality dashboard

---

### Phase 5: Integration into ChatMRPT (Days 18-21)
**Status**: 🔴 Not started

#### Integration Points

**1. TPR Workflow Enhancement**
```python
# File: app/data_analysis_v3/core/tpr_workflow_handler.py

def _execute_tpr_calculation(self):
    """
    Enhanced TPR calculation with catchment population
    """
    # Existing TPR calculation
    tpr_results = self._calculate_tpr(...)

    # NEW: Add catchment population
    catchment_estimator = CatchmentEstimator(
        ward_populations=self.ward_pops,
        facility_data=self.facilities,
        population_raster=self.pop_raster
    )

    # Estimate for each facility
    tpr_results['catchment_population'] = tpr_results['facility_id'].apply(
        catchment_estimator.estimate
    )

    # Calculate adjusted metrics
    tpr_results['incidence'] = (
        tpr_results['total_positive'] /
        tpr_results['catchment_population'] * 100
    )

    tpr_results['coverage'] = (
        tpr_results['total_tested'] /
        tpr_results['catchment_population'] * 100
    )

    return tpr_results
```

**2. Updated Visualizations**
```python
# File: app/tools/tpr_visualization_tool.py

def create_incidence_map(tpr_results):
    """
    Create choropleth map of incidence rates (not just TPR)
    """
    # Color scale: 0-40% incidence (realistic range)
    # Tooltip: Show TPR, incidence, coverage, catchment pop

def create_coverage_map(tpr_results):
    """
    NEW: Map showing testing coverage per ward
    Helps identify under-tested areas
    """
```

**3. User Communication**
```python
# Updated LLM prompts
TPR_COMPLETION_MESSAGE = """
✅ TPR Analysis Complete!

📊 Test Positivity Rate: {avg_tpr}% (% of tests positive)
📍 Malaria Incidence: {avg_incidence}% (% of population affected)
🏥 Testing Coverage: {avg_coverage}% (% of population tested)
👥 Population at Risk: {total_positive:,} people

Highest Incidence Wards:
1. {ward1}: {incidence1}% ({pop1:,} people affected)
2. {ward2}: {incidence2}% ({pop2:,} people affected)
3. {ward3}: {incidence3}% ({pop3:,} people affected)

Would you like to proceed with ITN distribution planning?
"""
```

**4. Updated Output Files**
```csv
# tpr_results_with_catchment.csv
WardCode,WardName,TPR,Incidence,Coverage,Catchment_Pop,Positive,Tested,Method,Confidence
ADS001,Yola North,58.3,16.2,27.8,25000,4050,6950,opd_based,medium
ADS002,Girei,42.1,12.5,29.7,18000,2250,7570,spatial,high
...
```

#### Integration Deliverables
- [ ] Updated TPR workflow with catchment estimation
- [ ] New incidence and coverage visualizations
- [ ] Enhanced user messaging
- [ ] Updated documentation

---

### Phase 6: Documentation & Training (Days 22-24)
**Status**: 🔴 Not started

#### Documentation Tasks

**1. Technical Documentation**
- [ ] `docs/catchment_population_methodology.md` - Full methodology
- [ ] `docs/catchment_estimation_api.md` - API reference
- [ ] `docs/validation_procedures.md` - QA procedures

**2. User Documentation**
- [ ] Update ChatMRPT user guide
- [ ] Add FAQ section on incidence vs TPR
- [ ] Create interpretation guide for results

**3. NMEP/WHO Documentation**
- [ ] Methodology whitepaper
- [ ] Validation results report
- [ ] Comparison with WHO estimates

**4. Code Documentation**
- [ ] Docstrings for all new functions
- [ ] Type hints and parameter descriptions
- [ ] Example usage notebooks

#### Training Materials
- [ ] Video walkthrough (10 min)
- [ ] Slide deck explaining incidence vs TPR
- [ ] Case study: Adamawa before/after

---

## 🔧 Technical Requirements

### Python Packages
```python
# Add to requirements.txt
geopandas>=0.14.0
rasterio>=1.3.0
scipy>=1.11.0  # For Voronoi
shapely>=2.0.0
```

### Data Storage
```
instance/catchment_data/
├── ward_populations.csv (NPC census)
├── facility_gps.csv (NMEP GPS coordinates)
├── worldpop_nigeria_2024.tif (Population raster)
├── catchment_estimates.csv (Computed catchments)
└── validation_reports/ (QA outputs)
```

### Performance Considerations
- **Memory**: WorldPop raster ~500MB (manageable)
- **Compute**: 27,929 facilities × 3 methods = ~30 seconds
- **Storage**: 27,929 rows × 10 columns = 1-2 MB CSV

---

## 📊 Expected Results

### Before (Current State)
| State | TPR | Interpretation |
|-------|-----|----------------|
| Adamawa | 71.9% | Too high, unusable |
| Edo | 90.3% | Unrealistic |
| National | 41.5% | Not actionable |

### After (With Catchment)
| State | TPR | Incidence | Coverage | Population at Risk |
|-------|-----|-----------|----------|-------------------|
| Adamawa | 71.9% | **15.4%** | 21.4% | 690,999 |
| Edo | 90.3% | **22.1%** | 24.5% | 107,957 |
| National | 41.5% | **18.2%** | 43.9% | 22.7M |

---

## ⚠️ Risks & Mitigation

### Risk 1: Data Availability
**Risk**: NPC census data or facility GPS not available
**Mitigation**: Use WorldPop only + ward-based fallback method
**Impact**: Medium confidence but still usable

### Risk 2: Validation Failures
**Risk**: Catchment estimates don't match state populations
**Mitigation**: Manual adjustment factors per state
**Impact**: Requires epidemiologist review

### Risk 3: Computational Complexity
**Risk**: Voronoi + raster processing too slow
**Mitigation**: Pre-compute catchments, cache results
**Impact**: Minimal (one-time cost)

### Risk 4: User Confusion
**Risk**: Users don't understand incidence vs TPR
**Mitigation**: Clear messaging, training materials
**Impact**: None (educational only)

---

## 📋 Success Metrics

### Technical Metrics
- [ ] ✅ Catchment estimation completes for all 37 states
- [ ] ✅ 90% of facilities pass validation checks
- [ ] ✅ Incidence rates fall in 10-30% range
- [ ] ✅ State-level totals within ±20% of census

### User Metrics
- [ ] ✅ Users can interpret incidence rates
- [ ] ✅ ITN distribution planning becomes feasible
- [ ] ✅ NMEP accepts methodology

### Impact Metrics
- [ ] ✅ Microplanning uses incidence (not TPR)
- [ ] ✅ Under-tested areas identified
- [ ] ✅ Resource allocation improves

---

## 🚀 Next Steps (Immediate)

### This Week
1. **Monday**: Meet with team, get approval for approach
2. **Tuesday**: Contact NPC for ward population data
3. **Wednesday**: Extract facility GPS from DHIS2
4. **Thursday**: Download WorldPop raster
5. **Friday**: Start Phase 2 prototype

### Week 2
- Build and test Adamawa prototype
- Run validation checks
- Present results to team

### Week 3
- Scale to all 37 states
- Integrate into ChatMRPT
- Write documentation

---

**Document Owner**: Bernard Boateng
**Last Updated**: 2025-10-07
**Status**: Draft (awaiting team approval)
