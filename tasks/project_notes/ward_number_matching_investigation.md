# Ward Number Matching Investigation Report

## Date: 2025-09-01
## Analyst: Claude
## Issue: Incorrect matching of numbered/lettered wards

## Executive Summary

The automated ward cleaning system is systematically mismatching wards that contain numbers, Roman numerals, or letters. This is causing health facilities to be assigned to the **wrong geographic wards**, which would corrupt any spatial or demographic analysis.

## Critical Findings

### 1. The Core Problem

The fuzzy matching algorithm cannot distinguish between:
- **Arabic numerals** (1, 2, 3, 4)
- **Roman numerals** (I, II, III, IV)
- **Letters** (A, B, C)

This leads to systematic mismatches where:
- "Arochukwu 1" matches to "Arochukwu 2" instead of "Arochukwu I"
- "Item 4" matches to "Item 3" instead of "Item Iv"
- "Alayi A" and "Alayi B" BOTH match to "Alayi 2"

### 2. Data Structure Analysis

#### TPR Data Format:
```
ab Arochukwu 1 Ward          -> Should be: Arochukwu I
ab Arochukwu Ward 4          -> Should be: Arochukwu Iv
ab Ohafor 1 Ward             -> Should be: Ohafor I
ab Item 4 Ward               -> Should be: Item Iv
ab Alayi A Ward              -> Should be: Alayi 1
ab Alayi B Ward              -> Should be: Alayi 2
```

#### Shapefile Format:
```
Arochukwu I, Arochukwu 2, Arochukwu 3, Arochukwu Iv
Ohafor I, Ohafor 2
Item 1, Item 2, Item 3, Item Iv
Alayi 1, Alayi 2
```

### 3. Why Fuzzy Matching Fails

Testing revealed that fuzzy matching scores are **identical** for wrong matches:

| Original | Correct Match | Score | Wrong Match | Score |
|----------|--------------|-------|-------------|-------|
| Arochukwu 1 | Arochukwu I | 82 | Arochukwu 2 | **91** |
| Item 4 | Item Iv | 62 | Item 3 | **83** |
| Ohafor 1 | Ohafor I | 88 | Ohafor 2 | **88** |
| Alayi A | Alayi 1 | 86 | Alayi 2 | **86** |

The algorithm picks the wrong match because:
1. "1" → "2" is seen as more similar than "1" → "I"
2. When scores are tied, it arbitrarily picks one
3. No special handling for Roman numerals or letter-to-number conversion

### 4. Impact Analysis

#### Affected States (from testing):
- **Abia**: 36 wards with confidence < 70%
- Similar issues likely in all 37 states

#### Data Corruption:
- Health facilities assigned to wrong wards
- Population data aggregated incorrectly
- Spatial analysis completely invalid for affected wards

### 5. Grace's Manual Approach

Grace correctly identified:
1. "1" should map to "I" (Roman numeral) in certain contexts
2. "4" should map to "Iv" (Roman IV)
3. "A" should map to "1", "B" to "2", etc.
4. LGA boundaries must be respected

## Root Causes in Code

### Issue 1: No Roman Numeral Handling
The `technique_1_fuzzy_matching` function treats all characters equally:
```python
best_match = process.extractOne(
    cleaned_ward,
    candidate_wards,
    scorer=fuzz.token_sort_ratio
)
```

### Issue 2: Arbitrary Selection on Tie Scores
When multiple wards have the same score, the system picks arbitrarily rather than using additional logic.

### Issue 3: No Letter-to-Number Mapping
The system doesn't recognize that "A" → "1", "B" → "2", etc.

## Proposed Solutions

### Solution 1: Roman Numeral Converter
```python
def convert_roman_arabic(ward_name):
    """Convert between Roman and Arabic numerals for matching"""
    conversions = {
        '1': ['1', 'I', 'i'],
        '2': ['2', 'II', 'ii'],
        '3': ['3', 'III', 'iii'],
        '4': ['4', 'IV', 'iv', 'Iv'],
        '5': ['5', 'V', 'v']
    }
    # Apply conversions for better matching
```

### Solution 2: Letter-to-Number Mapping
```python
def convert_letter_number(ward_name):
    """Convert A→1, B→2, etc."""
    letter_map = {
        'A': '1', 'B': '2', 'C': '3', 'D': '4'
    }
    # Apply mapping
```

### Solution 3: Exact Number Matching Priority
```python
def match_numbered_ward(ward_name, candidates):
    """Prioritize exact number matches"""
    # Extract number from ward name
    # Find candidates with same number
    # Return exact match if found
```

### Solution 4: Tie-Breaking Logic
When fuzzy scores are tied:
1. Prefer exact number matches
2. Check LGA consistency
3. Use position/order as last resort

## Validation Requirements

1. **Test all numbered wards** in each state
2. **Compare with Grace's manual corrections**
3. **Ensure no duplicate assignments** (like Alayi A and B both → 2)
4. **Verify LGA boundaries** are respected

## Immediate Actions Needed

1. **STOP using current cleaned data** - it has systematic errors
2. **Implement Roman numeral handling**
3. **Add letter-to-number conversion**
4. **Create validation tests** for numbered wards
5. **Re-run cleaning on all 37 states**
6. **Manual review** of all numbered ward matches

## Conclusion

The current automated system has a fundamental flaw in handling numbered wards. Grace's manual approach correctly identifies the pattern (1→I, 4→Iv, A→1, B→2), while the automation fails due to treating these as simple string matching problems. This is not a minor formatting issue but a **critical data integrity problem** that affects the geographic accuracy of all analyses.