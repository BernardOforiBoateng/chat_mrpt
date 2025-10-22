# TPR Analysis Investigation Results

## Date: 2025-08-04

## Key Findings

### 1. Shapefile Has Duplicates (234 features instead of 226)
The shapefile (`Adamawa_state.zip`) contains **234 features** but only **226 unique WardCodes**.

**8 WardCodes appear twice (16 duplicate rows total):**
- `ADSFUR08` - Ribadu (Fufore) - appears 2x with identical data
- `ADSLMR04` - Lamurde (Lamurde LGA) - appears 2x with identical data
- `ADSGYL06` - Lamurde (Mubi South) - appears 2x with identical data
- `ADSGYL09` - Nassarawo (Mubi South) - appears 2x with identical data
- `ADSYLN09` - Nassarawo (Yola North) - appears 2x with identical data
- `ADSMUB11` - Yelwa (Mubi North) - appears 2x with identical data
- `ADSMWA10` - Ribadu (Mayo-Belwa) - appears 2x with identical data
- `ADSYLN11` - Yelwa (Yola North) - appears 2x with identical data

### 2. TPR Output Has WardCode-LGA Mismatches (223 rows)
The `Adamawa_plus.csv` has **223 unique rows** but contains critical errors:

**WardCode Prefix Mismatches:**
1. **Ribadu (ADSMWA10)** - Claims to be in Fufore but:
   - WardCode prefix `MWA` = Mayo-Belwa
   - LGACode 2012 = Mayo-Belwa
   - But listed under Fufore LGA

2. **Lamurde/Lamurde (ADSGYL06)** - Claims to be in Lamurde but:
   - WardCode prefix `GYL` = Mubi South (formerly Guyuk)
   - LGACode 2015 = Mubi South
   - But listed under Lamurde LGA

3. **Nasarawo (ADSGYL09)** - Correct LGA but wrong code:
   - In Mubi South (correct)
   - But also appears as ADSYLN09 (Yola North code)

4. **Nasarawo (ADSYLN09)** - Claims to be in Mubi South but:
   - WardCode prefix `YLN` = Yola North
   - LGACode 2020 = Yola North
   - But listed under Mubi South

5. **Yelwa (ADSMUB11)** - Claims to be in Yola North but:
   - WardCode prefix `MUB` = Mubi North
   - LGACode 2014 = Mubi North
   - But listed under Yola North

### 3. The Real Problem: Cross-LGA Ward Contamination

The TPR pipeline is incorrectly assigning WardCodes from one LGA to wards in a different LGA. This happens because:

1. **Multiple wards share the same name** across different LGAs (e.g., "Ribadu" exists in both Fufore and Mayo-Belwa)
2. **The NMEP source data has incorrect ward-to-LGA mappings**
3. **The pipeline aggregates by LGA+Ward name** but takes the first WardCode it finds
4. **When facilities report conflicting WardCodes** for the same ward, the pipeline doesn't validate them

### 4. Missing Wards (226 - 223 = 3 missing)

Three wards are completely missing from the TPR output:
- These are likely wards that exist in the master shapefile but had no facilities reporting data
- Or wards that were lost during the incorrect WardCode assignment process

### 5. Impact on Analysis

- **Ward count**: Shows 223 instead of 226
- **Duplicate entries**: 8 wards appear twice with wrong WardCodes
- **Wrong geographic attribution**: Wards are assigned to wrong LGAs
- **TPR values**: Potentially incorrect as facilities may be grouped incorrectly

## Root Cause

The issue originates from the **NMEP TPR source data**, which has:
1. Facilities with incorrect WardCode assignments
2. Ward names that don't match their WardCodes
3. LGA assignments that don't match the WardCode prefixes

## Solution Required

The TPR pipeline needs to:
1. **Validate WardCode-LGA consistency** using the prefix mapping
2. **Correct mismatched WardCodes** based on the actual LGA
3. **Remove duplicate entries** from the shapefile before merging
4. **Use the master Nigerian shapefile** as the source of truth for ward-LGA relationships