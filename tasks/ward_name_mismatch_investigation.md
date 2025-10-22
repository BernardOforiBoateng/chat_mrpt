# Investigation: 38 Wards Losing WardCodes in TPR Pipeline

## Summary
38 wards (actually 46 total) lose their WardCodes during the TPR to Risk Analysis transition because of **ward name mismatches** between the TPR data source and the Nigerian shapefile.

## Root Cause
The TPR data and the complete Nigerian shapefile use **different naming conventions** for the same wards. When the TPR pipeline merges these datasets, wards with mismatched names fail to join properly and lose their WardCodes.

## Evidence Found

### Data Sources Analyzed
1. **TPR Data**: `instance/uploads/*/Adamawa_plus.csv`
   - Has 226 wards total
   - Only 180 have WardCodes (46 missing)
   
2. **Nigerian Shapefile**: `www/complete_names_wards/wards.shp`
   - Has 226 Adamawa wards
   - ALL have proper WardCodes

### Specific Name Mismatches Discovered

| TPR Name | Shapefile Name | WardCode | LGA | Issue Type |
|----------|---------------|----------|-----|------------|
| Hosheri-Zum | Hoserezum | ADSHNG07 | Hong | Hyphen vs merged |
| Futudou/Futuless | Futuless | ADSMCH02 | Michika | Slash combination |
| Garta/Ghumchi | Garta | ADSMCH03 | Michika | Slash combination |
| Wagga (Madagali) | Waga-Chakawa | ADSMDG09 | Madagali | Parenthetical + spelling |
| Mayo-Ine | Mayo Inne | ADSFUR06 | Fufore | Hyphen vs space |
| Uki-Tuki | Uki Tuki | ADSFUR09 | Fufore | Hyphen vs space |
| Wuro-Bokki | Wuro Bokki | ADSFUR10 | Fufore | Hyphen vs space |
| Girei I | Girei 1 | ADSGRE04 | Girei | Roman vs Arabic numerals |
| Girei II | Girei 2 | ADSGRE05 | Girei | Roman vs Arabic numerals |
| Ga'anda | Gaanda | ADSGMB03 | Gombi | Apostrophe |
| Gabun | Gabon | ADSGMB04 | Gombi | Spelling variation |

## Patterns Identified

### 1. Slash Combinations
- TPR uses "/" to combine ward names: `Futudou/Futuless`
- Shapefile has them as single names: `Futuless`

### 2. Hyphenation Differences
- TPR uses hyphens: `Mayo-Ine`, `Uki-Tuki`
- Shapefile uses spaces: `Mayo Inne`, `Uki Tuki`

### 3. Number Format Variations
- TPR uses Roman numerals: `Girei I`, `Girei II`
- Shapefile uses Arabic numbers: `Girei 1`, `Girei 2`

### 4. Special Characters
- TPR has apostrophes: `Ga'anda`
- Shapefile doesn't: `Gaanda`

### 5. Duplicate Names Across LGAs
These wards appear in multiple LGAs, causing ambiguity:
- Lamurde (appears in 2 LGAs)
- Ribadu (appears in 2 LGAs)
- Yelwa (appears in 2 LGAs)
- Nassarawo (appears in 2 LGAs)

## Impact on Analysis

When these 46 wards lose their WardCodes:
1. They can't properly merge with demographic/environmental data
2. They end up with NaN values in composite and PCA scores
3. The analysis summary falls back to a simpler version
4. Users don't see the full PCA test results they requested

## Solution Required

The TPR shapefile extraction process (`app/tpr_module/services/shapefile_extractor.py`) needs enhanced name matching:

1. **Normalize ward names** before merging:
   - Remove hyphens, slashes, apostrophes
   - Standardize Roman/Arabic numerals
   - Strip parenthetical information

2. **Use LGA context** for disambiguation:
   - Match wards within their specific LGA
   - Resolve duplicate names using LGA information

3. **Implement fuzzy matching** as fallback:
   - Use string similarity for close matches
   - Set appropriate threshold (e.g., 80% similarity)

4. **Preserve original WardCodes** from shapefile:
   - Don't rely on TPR data for WardCodes
   - Always use the authoritative shapefile WardCodes

## Files Involved
- `/app/tpr_module/services/shapefile_extractor.py` - Needs fixing
- `/app/tpr_module/integration/risk_transition.py` - Propagates the issue
- `/app/analysis/pipeline_stages/data_preparation.py` - Where NaN values appear