# Bed Net Planning Failure Investigation

## Date: 2025-09-26

## Problem Statement
Users report that bed net planning fails for Sokoto state with error: "Population data not available for Sokoto". User believed population data for all Nigerian states was embedded in the system.

## Investigation Findings

### 1. Root Cause Identified
**Missing Population Data Files** - Only 9 of 36 Nigerian states have population data files.

### 2. Current State Analysis

#### States WITH Population Data (9 states):
- Adamawa - `pbi_distribution_adamawa_clean.xlsx`
- Delta - `pbi_distribution_delta_clean.xlsx`
- Kaduna - `pbi_distribution_kaduna_clean.xlsx`
- Katsina - `pbi_distribution_katsina_clean.xlsx`
- Kwara - `pbi_distribution_kwara_clean.xlsx`
- Niger - `pbi_distribution_niger_clean.xlsx`
- Osun - `pbi_distribution_osun_clean.xlsx`
- Taraba - `pbi_distribution_taraba_clean.xlsx`
- Yobe - `pbi_distribution_yobe_clean.xlsx`

#### States WITHOUT Population Data (27 states):
Including but not limited to:
- **Sokoto** (the reported failure case)
- Abia, Akwa Ibom, Anambra, Bauchi, Bayelsa, Benue, Borno, Cross River
- Ebonyi, Edo, Ekiti, Enugu, Gombe, Imo, Jigawa, Kano, Kebbi
- Kogi, Lagos, Nasarawa, Ogun, Ondo, Oyo, Plateau, Rivers, Zamfara
- FCT (Federal Capital Territory)

### 3. Technical Implementation Details

#### File Location
- Path: `/www/ITN/ITN/pbi_distribution_{state}_clean.xlsx`
- Loader: `/app/data/population_data/itn_population_loader.py`
- Pipeline: `/app/analysis/itn_pipeline.py`

#### Code Flow
1. User uploads data for analysis
2. System detects state from data
3. ITN pipeline attempts to load population data
4. `ITNPopulationLoader.load_population_data()` looks for Excel file
5. If file missing → Returns None → Pipeline fails with error message

#### Current Error Handling
```python
# In itn_population_loader.py
file_path = self.data_path / f"pbi_distribution_{state_name}_clean.xlsx"
if not file_path.exists():
    logger.warning(f"Population data not found for {state_name}")
    return None
```

### 4. Impact Assessment

#### User Experience Impact
- **75% failure rate** - Only 9 of 36 states work
- **Misleading expectations** - System implies all states supported
- **No workaround** - Users cannot proceed without population data
- **Poor error messaging** - Doesn't explain why or offer alternatives

#### Business Impact
- Feature unusable for majority of Nigerian states
- Reduces value of ITN distribution planning tool
- May affect user trust in system capabilities

### 5. Data File Analysis

Examined existing population files structure:
- Format: Excel with multiple sheets
- Content: Ward-level population breakdowns
- Categories: Under-5, pregnant women, general population
- Source: Appears to be PBI (Population-Based Impact) distribution data
- File size: ~200-500KB per state

## Solutions Identified

### Option 1: Complete Population Data (Recommended)
**Approach**: Obtain and add missing population data files for all 27 states
- **Pros**: Full functionality, accurate planning, meets user expectations
- **Cons**: Requires data sourcing, validation, processing time
- **Implementation**: 4-8 hours if data available

### Option 2: Fallback Estimates
**Approach**: Use national/regional averages when state data missing
- **Pros**: Immediate partial solution, all states work
- **Cons**: Less accurate, may mislead planning decisions
- **Implementation**: 2-3 hours

### Option 3: External Data Integration
**Approach**: Connect to population API or database
- **Pros**: Always up-to-date, scalable
- **Cons**: Dependency on external service, potential costs
- **Implementation**: 6-8 hours

### Option 4: User-Provided Population Data
**Approach**: Allow users to upload their own population data
- **Pros**: Flexible, user controls accuracy
- **Cons**: Extra user burden, needs validation
- **Implementation**: 3-4 hours

### Option 5: Clear Feature Scoping (Quick Fix)
**Approach**: Explicitly list supported states, prevent unsupported state selection
- **Pros**: Immediate fix, honest about limitations
- **Cons**: Doesn't solve core problem
- **Implementation**: 1 hour

## Recommendation

**Immediate Action** (1 hour):
- Implement Option 5 to prevent user frustration
- Add clear messaging about supported states

**Short-term** (This week):
- Implement Option 2 as fallback mechanism
- Begin sourcing missing population data

**Long-term** (Next sprint):
- Complete Option 1 with all state data
- Consider Option 3 for sustainability

## Code Changes Required

### 1. Better Error Messages
```python
# In itn_population_loader.py
if not file_path.exists():
    supported_states = self.get_supported_states()
    error_msg = (
        f"Population data not available for {state_name}. "
        f"Currently supported states: {', '.join(supported_states)}. "
        "Please contact support to request data for your state."
    )
    logger.warning(error_msg)
    return {"error": error_msg}
```

### 2. Supported States Check
```python
# Add to itn_pipeline.py
def check_state_support(self, state_name):
    supported = self.population_loader.get_supported_states()
    if state_name.lower() not in [s.lower() for s in supported]:
        return False, supported
    return True, supported
```

### 3. UI Prevention
```javascript
// In upload form validation
const SUPPORTED_STATES = ['Adamawa', 'Delta', 'Kaduna', 'Katsina',
                          'Kwara', 'Niger', 'Osun', 'Taraba', 'Yobe'];

function validateStateSupport(detectedState) {
    if (!SUPPORTED_STATES.includes(detectedState)) {
        showWarning(`ITN planning not available for ${detectedState}`);
    }
}
```

## Testing Requirements

1. Test all 9 supported states still work
2. Test graceful failure for unsupported states
3. Verify error messages are helpful
4. Check documentation is updated
5. Validate any fallback mechanisms

## Documentation Updates Needed

1. Update feature documentation
2. List supported states clearly
3. Add FAQ about population data
4. Create data contribution guide
5. Update CLAUDE.md if needed

## UPDATE: New Discovery

After further investigation prompted by user's question about population data being replaced, I found:

### Current Implementation Has Partial Fallback
The code DOES have a population fallback mechanism in `itn_pipeline.py`:
- Lines 432-447: Uses average population (10,000 default) when ward data is missing
- BUT: This fallback only works WITHIN a state that has a population file
- If the state file doesn't exist at all, it fails before reaching the fallback

### The Problem Flow
1. User uploads data for Sokoto
2. System tries to load `pbi_distribution_Sokoto_clean.xlsx`
3. File doesn't exist → Returns error immediately
4. Never reaches the fallback code that would use estimates

### AWS Status
- Checked AWS production instances (3.21.167.170, 18.220.103.20)
- Still only 9 population files present
- No comprehensive population file was deployed
- User may be thinking of a different update or planned change

## Lessons Learned

1. **Assumption validation** - System claimed "all states" but only had 25% coverage
2. **Data dependency documentation** - Critical data requirements weren't visible
3. **Error message quality** - Generic errors didn't help users understand issue
4. **Feature completeness** - Partial implementations should be clearly marked
5. **Testing coverage** - Need tests for all claimed supported regions
6. **Fallback logic placement** - Fallback should trigger at file level, not just ward level