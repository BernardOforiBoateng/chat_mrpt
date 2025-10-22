# PCA Statistical Tests Planning Notes
**Date**: August 2, 2025
**Task**: Implement KMO and Bartlett's tests for PCA suitability

## Problem Statement
Currently, ChatMRPT runs PCA analysis on all datasets regardless of whether the data is suitable for PCA. This can lead to misleading results when the data doesn't meet PCA assumptions.

## Solution Requirements
Per user request (context.md):
1. Implement Kaiser-Meyer-Olkin (KMO) test - threshold 0.5
2. Implement Bartlett's test of sphericity
3. Only run PCA if tests pass
4. If tests fail, run composite analysis only
5. Inform users why PCA was skipped

## Discovery Process

### 1. Pipeline Architecture Review
Reviewed the analysis pipeline structure and found:
- **Dual-method approach**: System runs both composite and PCA analyses
- **Sequential execution**: Composite runs first, then PCA
- **Independent pipelines**: Each method has its own pipeline class
- **Unified dataset**: Results are combined after both analyses

### 2. Key Files Identified
- `app/analysis/pca_pipeline.py` - Core PCA implementation
- `app/tools/complete_analysis_tools.py` - Orchestrates both analyses
- `app/analysis/engine.py` - Analysis coordination
- `app/analysis/pipeline.py` - Composite analysis

### 3. Critical Code Locations Found

#### PCA Pipeline Flow (pca_pipeline.py):
1. Line 53: `run_complete_pca_analysis()` - Main entry point
2. Line 120: `_standardize_data()` - Data standardization
3. Line 129: `_run_pca_analysis()` - Actual PCA execution
4. Line 350: Standardization implementation
5. Line 386: PCA model fitting

#### Complete Analysis Tool (complete_analysis_tools.py):
1. Line 150: PCA analysis call
2. Line 303: User summary generation
3. Line 394: `_run_pca_analysis()` method

### 4. Integration Points
The best place to add the statistical tests is:
- **After** data standardization (need standardized data for tests)
- **Before** PCA model fitting (to decide whether to proceed)
- Specifically between lines 120-129 in `run_complete_pca_analysis()`

## Design Decisions

### 1. Test Placement
**Decision**: Add tests as a separate method `_check_pca_suitability()` in PCAAnalysisPipeline class

**Rationale**:
- Keeps code modular and testable
- Easy to skip or modify tests
- Clear separation of concerns

### 2. Failure Handling
**Decision**: Return gracefully with explanation rather than throwing error

**Rationale**:
- User experience - analysis should continue with composite
- Clear communication about why PCA was skipped
- Maintains system stability

### 3. Threshold Configuration
**Decision**: Start with hardcoded KMO threshold of 0.5

**Rationale**:
- Standard statistical threshold
- Can make configurable later if needed
- Keeps initial implementation simple

### 4. Dependency Management
**Decision**: Use factor_analyzer library if available, fallback to manual implementation

**Rationale**:
- factor_analyzer provides robust implementations
- Manual fallback ensures system works without additional dependencies
- Maintains flexibility

## Implementation Strategy

### Phase 1: Core Implementation
1. Add statistical test methods to PCA pipeline
2. Integrate tests into pipeline flow
3. Handle test failure cases

### Phase 2: User Experience
1. Update summary generation
2. Add clear test result messaging
3. Ensure smooth workflow when PCA skipped

### Phase 3: Testing & Validation
1. Test with various datasets
2. Verify thresholds work correctly
3. Ensure user messages are clear

## Potential Challenges

1. **Missing Dependencies**: factor_analyzer may not be installed
   - Solution: Implement manual calculation as fallback

2. **Data Requirements**: Tests need sufficient variables and samples
   - Solution: Add minimum data checks before running tests

3. **User Confusion**: Users may not understand why PCA was skipped
   - Solution: Provide clear, educational messaging about test results

4. **Backward Compatibility**: Existing analyses expect both methods
   - Solution: Ensure composite-only results structure matches expected format

## Next Steps

1. Check if factor_analyzer is in requirements.txt
2. Implement `_check_pca_suitability()` method
3. Integrate into pipeline with conditional logic
4. Update user messaging
5. Test with various datasets
6. Document changes

## Questions to Consider

1. Should thresholds be configurable?
2. Should we save test results for audit trail?
3. How detailed should user explanations be?
4. Should we allow override of test results?

## References
- [Kaiser-Meyer-Olkin Test](https://www.statisticshowto.com/kaiser-meyer-olkin/)
- [Bartlett's Test in SPSS](https://datapott.com/kaiser-meyer-olkin-kmo-and-bartletts-test-of-sphericity-in-spss/)
- Factor Analysis best practices

## Status
Planning complete. Ready to begin implementation.