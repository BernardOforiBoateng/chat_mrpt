# TPR Meeting Quick Reference Card
**One-Page Cheat Sheet for Discussion**

---

## 🔴 THE PROBLEM (30 seconds)

**Current TPR values are too high (40-90%) because**:
- We measure **test positivity** (% of tested people who are positive)
- Not **population incidence** (% of all people who have malaria)
- Missing denominator = catchment population per facility

**Why it matters**:
- Can't plan ITN distribution without knowing total population at risk
- 71% TPR doesn't tell you if 100 or 10,000 people need nets

---

## 📊 THE NUMBERS

### National Statistics
- **National TPR**: 41.5% (2 in 5 tests positive)
- **Highest TPR**: Edo (90%), Anambra (87%), Imo (86%)
- **Adamawa** (demo state): 71.9% TPR

### Data Quality Issues
- **51% missing data** overall
- **97.9% missing** microscopy data
- 15+ facilities with **impossible values** (positive > tested)

---

## 💡 THE SOLUTION

### Hybrid Catchment Population Model

| Facility Type | Method | Data Source |
|--------------|--------|-------------|
| **Urban** | OPD attendance ÷ coverage rate | Existing NMEP data |
| **Rural with GPS** | Voronoi spatial catchment | GPS + WorldPop raster |
| **Fallback** | Ward pop ÷ facility count | NPC census |

### Example Impact (Adamawa)
| Metric | Before | After |
|--------|--------|-------|
| **TPR** | 71.9% | 71.9% (unchanged) |
| **Incidence** | N/A | **15.4%** (usable!) |
| **Coverage** | N/A | 21.4% tested |
| **At Risk** | Unknown | **690,999 people** |

---

## 🎯 WHAT WE NEED

### Data Requirements
✅ Ward-level population (NPC census)
✅ Facility GPS coordinates (DHIS2/NMEP)
✅ WorldPop population rasters (validation)
✅ Facility type classification (existing)

### Timeline
- **2-3 days**: Prototype for Adamawa
- **2 weeks**: Scale to all 37 states
- **1 month**: Integrate into microplanning

---

## 🗣️ KEY TALKING POINTS

### 1. Acknowledge
"Yes, TPR values are too high - we're measuring test positivity, not population incidence."

### 2. Explain
"For microplanning, we need to know how many people each facility serves (catchment population)."

### 3. Propose
"I recommend a hybrid model: OPD for urban, spatial for rural, census for fallback."

### 4. Data
"We need ward populations, facility GPS, and WorldPop rasters - are these available?"

### 5. Timeline
"Prototype in 2-3 days for Adamawa, scale to all states in 2 weeks."

---

## ❓ QUESTIONS TO ASK

### Must Answer
1. Which catchment estimation method do you prefer?
2. Do we have NPC census data at ward level?
3. Are facility GPS coordinates available?

### Nice to Know
4. Should we integrate into ChatMRPT or separate preprocessing?
5. What's the priority timeline for microplanning?
6. Who validates the catchment estimates?

---

## 📋 MEETING OUTPUTS

**Decisions Needed**:
- [ ] Approve hybrid catchment model approach
- [ ] Confirm data sources (NPC, GPS, WorldPop)
- [ ] Set timeline (prototype → scale → integrate)
- [ ] Assign validation responsibility

**Action Items**:
- [ ] Bernard: Gather NPC ward population data
- [ ] Bernard: Get facility GPS coordinates from NMEP
- [ ] Bernard: Build prototype for Adamawa
- [ ] Grace/Laurette: Review and validate methodology

---

## 🔧 TECHNICAL FORMULA

### Current (Wrong)
```
TPR = (Positive Cases / Tests Conducted) × 100
Problem: Only counts people who came to facility
```

### New (Correct)
```
TPR = (Positive Cases / Tests Conducted) × 100 [unchanged]
Incidence = (Positive Cases / Catchment Population) × 100 [NEW!]
Coverage = (Tests Conducted / Catchment Population) × 100 [NEW!]
```

### Catchment Estimation
```python
if urban and has_OPD:
    catchment = OPD_attendance / 0.35  # 35% coverage
elif has_GPS:
    catchment = spatial_voronoi_method(GPS)
else:
    catchment = (ward_pop / num_facilities) * type_weight
```

---

## 📊 VISUALIZATION FIX

**Issue**: "Shorten y-axis for monthly tests plot"

**Current**: 0-10,000 scale (hides most facilities)
**Fix**: 0-2,000 scale (show distribution clearly)

**Issue**: "Are 12 months reported per state?"

**Answer**: Yes, all states show 12 periods BUT 51% missing data

---

## 🎓 WHY THIS MATTERS (30-second pitch)

"Right now, a 71% TPR tells us '71% of people we tested have malaria,' but we don't know:
- How many people we DIDN'T test
- How many people the facility serves
- How many nets to distribute

With catchment populations, we get:
- 15% incidence (realistic!)
- 21% coverage (we're missing 79%)
- 691K people at risk (allocate nets accordingly)

This transforms TPR from a **data point** into a **planning tool**."

---

## 🚦 SUCCESS CRITERIA

### Before (Current State)
❌ TPR values too high to use
❌ Can't plan ITN distribution
❌ Don't know population at risk
❌ No testing coverage metrics

### After (With Catchment Pop)
✅ Realistic incidence rates (10-25%)
✅ Calculate nets per catchment
✅ Identify under-tested areas
✅ Prioritize high-burden facilities

---

**Print this page and bring to meeting!**
