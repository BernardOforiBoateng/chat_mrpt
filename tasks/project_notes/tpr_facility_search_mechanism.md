# How TPR Currently Searches for Health Facilities

## Current Facility Search Mechanism

### 1. **Facility Level Column** 
The data has a column called `level` (or `facility_level`) that categorizes each facility:
- **Primary** (PHC, Primary Health Centers)
- **Secondary** (General Hospitals)
- **Tertiary** (Teaching Hospitals, Federal Medical Centers)

### 2. **How It's Stored in Data**
```
| State | LGA | Ward | Health Facility | level | ... |
|-------|-----|------|----------------|--------|-----|
| Adamawa | Demsa | Bille | Bille PHC | Primary | ... |
| Adamawa | Demsa | Bille | Demsa General Hospital | Secondary | ... |
| Adamawa | Yola North | Jimeta | FMC Yola | Tertiary | ... |
```

### 3. **Current Search Process** (`facility_filter.py`)

```python
# Step 1: System looks for the level column
level_col = 'facility_level' if 'facility_level' in data.columns else 'level'

# Step 2: Maps different variations
FACILITY_LEVEL_MAPPINGS = {
    'Primary': ['Primary', 'Primary Health Facility', 'PHC'],
    'Secondary': ['Secondary', 'Secondary Health Facility', 'General Hospital'],
    'Tertiary': ['Tertiary', 'Tertiary Health Facility', 'Teaching Hospital']
}

# Step 3: Filter by level
if user_selects == "Primary":
    filtered_data = data[data[level_col].isin(['Primary', 'PHC', 'Primary Health Facility'])]
```

### 4. **The Analysis Process**

When user selects "Primary facilities only":
```python
1. Filter data to only Primary facilities
2. Calculate TPR for just those facilities
3. Aggregate to ward level (only including Primary facilities)
4. Generate maps showing Primary facility performance
```

### 5. **Facility Statistics Generated**
```python
# For each facility level, system calculates:
{
    'Primary': {
        'facility_count': 987,           # Number of facilities
        'facility_percentage': 79.2,     # % of all facilities
        'record_count': 2961,           # Data records
        'lga_coverage': {               # Geographic coverage
            'count': 21,                # LGAs with Primary facilities
            'percentage': 100.0         # % of LGAs covered
        },
        'ward_coverage': {
            'count': 215,               # Wards with Primary facilities
            'percentage': 95.1          # % of wards covered
        }
    }
}
```

## Current Column Dependencies

The facility search relies on:
1. **`level` column** - Must exist in the data
2. **Known values** - "Primary", "Secondary", "Tertiary"
3. **Facility column** - To count unique facilities
4. **Location columns** - State, LGA, Ward for geographic filtering

## What Happens in New Format?

If the new TPR format:
- **Has `level` column**: Will work fine
- **Missing `level` column**: System will fail to filter by facility type
- **Different values**: If it says "PHC" instead of "Primary", the mapping handles it

## Dynamic Detection Needed

For the new format, we need to:
1. **Check if level column exists** at all
2. **Detect what values it contains** (might be different naming)
3. **Map to standard categories** or skip facility filtering if not available

## User Experience Impact

**If facility level column is missing:**
```
ChatMRPT: "What type of health facilities would you like to include?"
- All facilities (only option available)
- [Primary/Secondary/Tertiary options hidden]

"Note: Facility level information not available in this dataset"
```

**If facility level has different values:**
```
# Backend detects: "PHC", "Hospital", "Clinic"
# Maps to: Primary, Secondary, Primary

ChatMRPT: "What type of health facilities would you like to include?"
- All facilities
- PHC/Clinics (Primary care)
- Hospitals (Secondary care)
```

## Summary

The current system:
1. **Expects** a `level` column with specific values
2. **Filters** data based on facility type selection
3. **Aggregates** TPR only for selected facility types
4. **Falls back** to "all facilities" if column missing

For dynamic detection, we need to:
- Detect if facility level column exists
- Map any values found to standard categories
- Gracefully handle missing facility level data